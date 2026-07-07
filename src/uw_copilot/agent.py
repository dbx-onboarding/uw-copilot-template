"""
uw_copilot.agent — MLflow ChatAgent for model serving.

Architecture per request:
  1. Detect intent   — HybridRetriever.detect_intent()
  2. Retrieve docs   — HybridRetriever.search()
  3. Build context   — HybridRetriever.build_context()
  4. Generate        — LLM with system prompt + context + history
  5. Apply guardrails — GuardrailPipeline.apply()

Usage:
    from uw_copilot.agent import UWCopilotAgent, log_and_register_agent
    log_and_register_agent(cfg)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import mlflow
from mlflow.pyfunc import ChatModel
from mlflow.types.llm import ChatChoice, ChatCompletionResponse, ChatMessage
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    ChatMessage as SDKChatMessage,
    ChatMessageRole,
)

from uw_copilot.config import Config
from uw_copilot.guardrails import GuardrailPipeline
from uw_copilot.retrieval import HybridRetriever, QueryIntent
from uw_copilot.structured import StructuredDataTool


class UWCopilotAgent(ChatModel):
    """
    Production MLflow ChatAgent registered at {catalog}.{schema}.uw_copilot_rag_model
    and served at {prefix}_rag_endpoint.
    """

    def __init__(self):
        self.cfg:         Optional[Config]            = None
        self.w:           Optional[WorkspaceClient]   = None
        self.retriever:   Optional[HybridRetriever]   = None
        self.structured:  Optional[StructuredDataTool] = None
        self.guardrails:  Optional[GuardrailPipeline] = None
        self.system_prompt: str = ""
        self._last_docs:  list = []  # populated per-request; used to build source citations

    def load_context(self, context):
        # Only load static artifacts here — WorkspaceClient is NOT initialised
        # during load_context because Databricks runtime credentials are not yet
        # injected at mlflow_parse time. They become available on the first request.
        self.cfg        = Config(context.artifacts.get("config"))
        self.guardrails = GuardrailPipeline.from_config_file(context.artifacts.get("guardrails"))

        sp = context.artifacts.get("system_prompt")
        self.system_prompt = (
            Path(sp).read_text() if sp and Path(sp).exists()
            else "You are a helpful underwriting assistant."
        )

    def _ensure_clients_loaded(self):
        """Lazy-init WorkspaceClient, HybridRetriever, and StructuredDataTool on first predict() call."""
        if self.w is None:
            self.w          = WorkspaceClient()
            self.retriever  = HybridRetriever(self.cfg, self.w)
            self.structured = StructuredDataTool(self.cfg, self.w)

    def predict(self, context, messages: list, params=None):
        self._ensure_clients_loaded()
        extra     = params if isinstance(params, dict) else {}
        user_role = extra.get("user_role", "underwriter")
        question  = _extract_last_user_message(messages)

        if not question:
            return _format_response("No question found in the request.", [])

        intent = self.retriever.detect_intent(question)

        # Route SQL-intent queries to the structured data tool — but enforce RBAC.
        # Roles without operational-data access fall back to document retrieval
        # rather than querying the operational tables directly.
        if intent == QueryIntent.SQL and _can_query_structured(user_role):
            self._last_docs = []
            sql_context = self.structured.query(question)
            answer, _ = self._generate(question, sql_context, messages)
            result = self.guardrails.apply(answer)
            return _format_response(result.answer, [])

        # Default: document retrieval path.
        # SQL-intent from a role that can't use structured data is answered from docs.
        doc_intent = intent if intent != QueryIntent.SQL else QueryIntent.HYBRID
        docs   = self.retriever.search(question, user_role=user_role, intent=doc_intent)
        self._last_docs = docs
        ctx    = self.retriever.build_context(docs)
        answer, sources = self._generate(question, ctx, messages)
        answer = _append_citations(answer, docs)  # surface sources inline in the answer
        result = self.guardrails.apply(answer)
        return _format_response(result.answer, sources)

    def _generate(self, question: str, context_block: str, history: list):
        system = self.system_prompt
        if context_block:
            system += f"\n\n{context_block}"

        sdk_messages = [SDKChatMessage(role=ChatMessageRole.SYSTEM, content=system)]
        for m in (history or [])[-8:]:
            role_str = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else "user")
            content  = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else "")
            role_enum = ChatMessageRole.USER if role_str == "user" else ChatMessageRole.ASSISTANT
            sdk_messages.append(SDKChatMessage(role=role_enum, content=content))
        sdk_messages.append(SDKChatMessage(role=ChatMessageRole.USER, content=question))

        try:
            response = self.w.serving_endpoints.query(
                name=self.cfg.chat_model,
                messages=sdk_messages,
                max_tokens=2048,
                temperature=0.1,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"Error generating response: {e}"

        sources = [{"path": d.source_path, "category": d.category} for d in (getattr(self, "_last_docs", []))]
        return answer, sources


# ── Registration ──────────────────────────────────────────────────────────────

def log_and_register_agent(cfg: Config, alias: str = "champion") -> str:
    """Register UWCopilotAgent in Unity Catalog. Call from notebook 09_deploy."""
    from mlflow.models.resources import (
        DatabricksServingEndpoint,
        DatabricksVectorSearchIndex,
        DatabricksSQLWarehouse,
        DatabricksTable,
    )

    mlflow.set_registry_uri("databricks-uc")
    repo_root = _find_repo_root()

    # Declare resources so Model Serving injects credentials at inference time
    resources = [
        DatabricksServingEndpoint(endpoint_name=cfg.chat_model),
        DatabricksVectorSearchIndex(index_name=cfg.vs_index),
    ]
    if cfg.warehouse_id:
        resources.append(DatabricksSQLWarehouse(warehouse_id=cfg.warehouse_id))

    # Declare table resources so the serving endpoint gets SELECT on operational tables
    _operational_tables = [
        "insureds", "policies", "drivers", "vehicles", "claims",
        "submissions", "loss_runs", "underwriting_referrals",
    ]
    for tbl in _operational_tables:
        resources.append(DatabricksTable(table_name=f"{cfg.catalog}.{cfg.schema}.{tbl}"))

    with mlflow.start_run(run_name=f"uw_copilot_{cfg.prefix}"):
        model_info = mlflow.pyfunc.log_model(
            artifact_path="uw_copilot_agent",
            python_model=os.path.join(repo_root, "src", "uw_copilot", "agent.py"),
            code_paths=[os.path.join(repo_root, "src", "uw_copilot")],
            artifacts={
                "config":        os.path.join(repo_root, "config", "company_config.yaml"),
                "system_prompt": os.path.join(repo_root, "prompts", "system_prompt.md"),
                "guardrails":    os.path.join(repo_root, "prompts", "guardrails_config.yaml"),
            },
            pip_requirements=[
                "databricks-sdk>=0.20.0",
                "databricks-ai-search>=0.3.0",
                "mlflow>=2.13.0",
                "pyyaml>=6.0",
            ],
            resources=resources,
            registered_model_name=cfg.uc_model,
            input_example={
                "messages": [{"role": "user", "content": "What are the referral triggers for HAZMAT fleets?"}]
            },
        )

    client = mlflow.MlflowClient()
    version = model_info.registered_model_version
    client.set_registered_model_alias(cfg.uc_model, alias, version)
    uri = f"models:/{cfg.uc_model}@{alias}"
    print(f"Registered: {uri}")
    return uri


# ── RBAC for the structured-data (NL-to-SQL) path ───────────────────────────────
# Roles that must NOT run free-form queries against operational tables. External
# parties (brokers) get document-grounded answers instead. Override by editing
# this set or adapting to your rbac policy.
SQL_DENIED_ROLES = {"broker"}


def _can_query_structured(user_role: str) -> bool:
    return (user_role or "").lower() not in SQL_DENIED_ROLES


def _append_citations(answer: str, docs: list) -> str:
    """Append a deduplicated Sources list so citations reach the caller/UI."""
    if not answer or answer.startswith("Error generating response"):
        return answer
    seen, sources = set(), []
    for d in docs or []:
        path = getattr(d, "source_path", "") or ""
        if not path or getattr(d, "chunk_id", "") == "error":
            continue
        name = path.rstrip("/").split("/")[-1]
        cat = getattr(d, "category", "") or ""
        label = f"{name} ({cat})" if cat else name
        if label not in seen:
            seen.add(label)
            sources.append(label)
    if not sources:
        return answer
    lines = "\n".join(f"- {s}" for s in sources[:5])
    return f"{answer}\n\n**Sources:**\n{lines}"


# ── Utilities ─────────────────────────────────────────────────────────────────

def _extract_last_user_message(messages: list) -> str:
    for m in reversed(messages):
        role    = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
        content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else "")
        if role == "user" and content:
            return content
    return ""


def _format_response(answer: str, sources: list) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        choices=[ChatChoice(message=ChatMessage(role="assistant", content=answer))],
        usage=None,
    )


def _find_repo_root() -> str:
    """
    Find the repo root containing config/company_config.yaml.

    Priority:
      1. UWCOPILOT_REPO_ROOT env var  (set by 09_deploy or CI)
      2. Walk up from src/uw_copilot/ (works for editable installs)
      3. Current working directory    (fallback for Databricks notebooks)
    """
    # 1. Explicit env var — highest priority, works in any context
    env_root = os.environ.get("UWCOPILOT_REPO_ROOT")
    if env_root and Path(env_root, "config", "company_config.yaml").exists():
        return env_root

    # 2. Walk up from __file__ — works for editable installs (pip install -e .)
    here = Path(__file__).resolve().parent
    for ancestor in [here, here.parent, here.parent.parent, here.parent.parent.parent]:
        if (ancestor / "config" / "company_config.yaml").exists():
            return str(ancestor)

    # 3. Current working directory — works in Databricks notebook context
    cwd = Path.cwd()
    for ancestor in [cwd, cwd.parent, cwd.parent.parent]:
        if (ancestor / "config" / "company_config.yaml").exists():
            return str(ancestor)

    raise FileNotFoundError(
        "Could not locate repo root (config/company_config.yaml not found). "
        "Set the UWCOPILOT_REPO_ROOT environment variable to the repo path."
    )


# Required for MLflow code-based logging — tells MLflow which class to instantiate
mlflow.models.set_model(UWCopilotAgent())
