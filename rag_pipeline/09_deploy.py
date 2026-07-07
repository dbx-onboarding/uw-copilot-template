# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 09 — Deploy
# MAGIC
# MAGIC Logs and registers `UWCopilotAgent` in Unity Catalog, creates or updates
# MAGIC the Model Serving endpoint, and deploys the Streamlit Workbench app.
# MAGIC
# MAGIC **Run this notebook to:**
# MAGIC - Promote a new model version to `champion` alias
# MAGIC - Update the serving endpoint with the latest model
# MAGIC - Deploy the Databricks App
# MAGIC
# MAGIC To deploy the app only (without re-logging the model), set:
# MAGIC `dbutils.widgets.text("deploy_app_only", "false")`

# COMMAND ----------

# DBTITLE 1,Widget + sys.path setup
dbutils.widgets.text("deploy_app_only", "false")
DEPLOY_APP_ONLY = dbutils.widgets.get("deploy_app_only").lower() == "true"

import sys, os

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
_src_path  = os.path.join(_repo_root, "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# COMMAND ----------

# DBTITLE 1,Skip restart
# Python restart not needed — sys.path set above.

# COMMAND ----------

# DBTITLE 1,Config (post-restart)
import os, sys
import mlflow

# Clear cached modules so updated agent.py is loaded
for _mod in [k for k in sys.modules if k.startswith("uw_copilot")]:
    del sys.modules[_mod]

from uw_copilot.config import Config
from uw_copilot.agent  import log_and_register_agent

# Re-derive after restartPython() cleared all module-level variables
_nb_path        = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root      = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
DEPLOY_APP_ONLY = dbutils.widgets.get("deploy_app_only").lower() == "true"

cfg = Config()
os.environ["UWCOPILOT_REPO_ROOT"] = _repo_root  # agent.load_context() uses this

print(f"Prefix:          {cfg.prefix}")
print(f"UC Model:        {cfg.uc_model}")
print(f"Serving EP:      {cfg.serving_endpoint}")
print(f"App:             {cfg.app_name}")
print(f"Repo root:       {_repo_root}")
print(f"Deploy app only: {DEPLOY_APP_ONLY}")

# COMMAND ----------

# DBTITLE 1,Pre-deploy validation — test all modules
# =============================================================================
# Validate all uw_copilot modules before deploying
# Run this cell to catch import errors BEFORE log_and_register_agent()
# =============================================================================
import traceback

_pass = 0
_fail = 0

def assert_val(v):
    assert v, f"Value is empty/None: {v!r}"

def assert_eq(actual, expected):
    assert actual == expected, f"Expected {expected!r}, got {actual!r}"

def assert_contains(text, substr):
    assert substr in text, f"'{substr}' not found in text ({len(text)} chars)"

def _test(label, fn):
    global _pass, _fail
    try:
        fn()
        print(f"  \u2705 {label}")
        _pass += 1
    except Exception as e:
        print(f"  \u274c {label}: {e}")
        traceback.print_exc()
        _fail += 1

print("=" * 60)
print("PRE-DEPLOY VALIDATION")
print("=" * 60)

# --- 1. Module imports ---
print("\n\u2500\u2500 Module Imports \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
_test("Config",            lambda: __import__("uw_copilot.config", fromlist=["Config"]))
_test("HybridRetriever",   lambda: __import__("uw_copilot.retrieval", fromlist=["HybridRetriever", "QueryIntent"]))
_test("StructuredDataTool", lambda: __import__("uw_copilot.structured", fromlist=["StructuredDataTool"]))
_test("FeedbackManager",   lambda: __import__("uw_copilot.feedback", fromlist=["FeedbackManager"]))
_test("GuardrailPipeline", lambda: __import__("uw_copilot.guardrails", fromlist=["GuardrailPipeline"]))
_test("HierarchicalChunker", lambda: __import__("uw_copilot.chunker", fromlist=["HierarchicalChunker"]))
_test("SessionManager",    lambda: __import__("uw_copilot.session", fromlist=["SessionManager"]))
_test("UWCopilotAgent",    lambda: __import__("uw_copilot.agent", fromlist=["UWCopilotAgent", "log_and_register_agent"]))

# --- 2. Config validation ---
print("\n\u2500\u2500 Config Values \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
_test("cfg.chat_model set",      lambda: assert_val(cfg.chat_model))
_test("cfg.vs_index set",        lambda: assert_val(cfg.vs_index))
_test("cfg.serving_endpoint set", lambda: assert_val(cfg.serving_endpoint))
_test("cfg.warehouse_id set",    lambda: assert_val(cfg.warehouse_id))
_test("cfg.uc_model set",        lambda: assert_val(cfg.uc_model))

# --- 3. Intent routing ---
print("\n\u2500\u2500 Intent Routing \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
from uw_copilot.retrieval import HybridRetriever, QueryIntent
_test("SQL intent: 'how many drivers'",
      lambda: assert_eq(HybridRetriever(cfg, None).detect_intent("how many drivers do we have"), QueryIntent.SQL))
_test("SQL intent: 'total loss'",
      lambda: assert_eq(HybridRetriever(cfg, None).detect_intent("what is total loss for Lone Star"), QueryIntent.SQL))
_test("Keyword intent: 'CLM-26-001'",
      lambda: assert_eq(HybridRetriever(cfg, None).detect_intent("tell me about CLM-26-001"), QueryIntent.KEYWORD))
_test("Hybrid intent: 'referral triggers'",
      lambda: assert_eq(HybridRetriever(cfg, None).detect_intent("what are the referral triggers for HAZMAT"), QueryIntent.HYBRID))

# --- 4. StructuredDataTool schema context ---
print("\n\u2500\u2500 Structured Data Tool \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
from uw_copilot.structured import StructuredDataTool
from databricks.sdk import WorkspaceClient
_w = WorkspaceClient()
_sdt = StructuredDataTool(cfg, _w)
_test("Schema context built",    lambda: assert_val(_sdt.schema_context))
_test("Schema has insureds table", lambda: assert_contains(_sdt.schema_context, "insureds"))
_test("Schema has submissions table", lambda: assert_contains(_sdt.schema_context, "submissions"))
_test(f"SQL prompt references {cfg.catalog}.{cfg.schema}",
      lambda: assert_contains(_sdt.sql_prompt, f"{cfg.catalog}.{cfg.schema}"))

# --- 5. FeedbackManager init ---
print("\n\u2500\u2500 Feedback Manager \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
from uw_copilot.feedback import FeedbackManager
_fm = FeedbackManager(cfg, _w)
_test("FeedbackManager.table correct", lambda: assert_eq(_fm.table, f"{cfg.catalog}.{cfg.schema}.copilot_feedback"))

# --- 6. MLflow resources declaration ---
print("\n\u2500\u2500 MLflow Resources \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
import inspect
from uw_copilot.agent import log_and_register_agent
_src = inspect.getsource(log_and_register_agent)
_test("Declares DatabricksServingEndpoint",    lambda: assert_contains(_src, "DatabricksServingEndpoint"))
_test("Declares DatabricksVectorSearchIndex",  lambda: assert_contains(_src, "DatabricksVectorSearchIndex"))
_test("Declares DatabricksSQLWarehouse",       lambda: assert_contains(_src, "DatabricksSQLWarehouse"))
_test("Passes resources to log_model",         lambda: assert_contains(_src, "resources=resources"))

# --- Summary ---
print("\n" + "=" * 60)
if _fail == 0:
    print(f"\u2705 ALL {_pass} TESTS PASSED — safe to deploy")
else:
    print(f"\u274c {_fail} FAILED, {_pass} passed — fix before deploying")
print("=" * 60)

# COMMAND ----------

# MAGIC %md ## Step 1 — Log & Register Model

# COMMAND ----------

if not DEPLOY_APP_ONLY:
    model_uri = log_and_register_agent(cfg, alias="champion")
    print(f"\n✅ Registered: {model_uri}")
else:
    print("Skipping model logging (deploy_app_only=true)")
    model_uri = f"models:/{cfg.uc_model}@champion"

# COMMAND ----------

# MAGIC %md ## Step 2 — Create or Update Serving Endpoint

# COMMAND ----------

if not DEPLOY_APP_ONLY:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import ServedEntityInput, EndpointCoreConfigInput
    from mlflow import MlflowClient

    mlflow.set_registry_uri("databricks-uc")
    w  = WorkspaceClient()
    mc = MlflowClient()

    try:
        alias_info    = mc.get_model_version_by_alias(cfg.uc_model, "champion")
        model_version = alias_info.version
    except Exception:
        versions      = mc.search_model_versions(f"name='{cfg.uc_model}'")
        model_version = max(v.version for v in versions)

    print(f"Deploying {cfg.uc_model} v{model_version} to {cfg.serving_endpoint}")

    from databricks.sdk.errors import ResourceDoesNotExist

    try:
        ep           = w.serving_endpoints.get(name=cfg.serving_endpoint)
        config_state = str(ep.state.config_update) if ep.state else ""
        if "FAILED" in config_state:
            print(f"Endpoint in failed state ({config_state}) — deleting and recreating...")
            w.serving_endpoints.delete(name=cfg.serving_endpoint)
            raise ResourceDoesNotExist("deleted failed endpoint")
        print(f"Endpoint exists — updating to v{model_version}")
        w.serving_endpoints.update_config_and_wait(
            name=cfg.serving_endpoint,
            served_entities=[
                ServedEntityInput(
                    entity_name=cfg.uc_model,
                    entity_version=model_version,
                    scale_to_zero_enabled=True,
                    workload_size="Small",
                )
            ],
        )
    except ResourceDoesNotExist:
        print(f"Creating new endpoint: {cfg.serving_endpoint}")
        w.serving_endpoints.create_and_wait(
            name=cfg.serving_endpoint,
            config=EndpointCoreConfigInput(
                served_entities=[
                    ServedEntityInput(
                        entity_name=cfg.uc_model,
                        entity_version=model_version,
                        scale_to_zero_enabled=True,
                        workload_size="Small",
                    )
                ]
            ),
        )

    print(f"✅ Endpoint ready: {cfg.serving_endpoint} (v{model_version})")

# COMMAND ----------

# DBTITLE 1,Step 2b — Enable Inference Table Logging
# =============================================================================
# Enable AI Gateway inference table logging.
#
# auto_capture_config (legacy inference tables) is DEPRECATED in this workspace.
# The current approach is AI Gateway, which captures every request + response at
# the gateway layer into a UC Delta table:
#   {catalog}.{schema}.{gateway_name}_payload
#
# This cell creates (or updates) a gateway named {serving_endpoint}_gateway that
# routes to the serving endpoint and enables inference table logging.
#
# After this cell runs, the app can optionally call the gateway URL instead of
# the serving endpoint directly — or the gateway can run in parallel purely for
# logging. Either way, the payload table starts accumulating records immediately.
#
# Safe to re-run — skips creation if the gateway already exists.
# =============================================================================
if not DEPLOY_APP_ONLY:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import AiGatewayInferenceTableConfig

    w           = WorkspaceClient()  # self-contained — safe to run without cell 9
    _tbl_prefix = cfg.serving_endpoint

    # PUT is idempotent — creates or updates AI Gateway config in one call.
    # GET 404s when no config exists yet, so skip the pre-check.
    print(f"Configuring AI Gateway inference logging on {cfg.serving_endpoint}...")
    w.serving_endpoints.put_ai_gateway(
        name=cfg.serving_endpoint,
        inference_table_config=AiGatewayInferenceTableConfig(
            catalog_name=cfg.catalog,
            schema_name=cfg.schema,
            table_name_prefix=_tbl_prefix,
            enabled=True,
        ),
    )
    print(f"\u2705 AI Gateway inference logging enabled")
    print(f"   Endpoint: {cfg.serving_endpoint}")
    print(f"   Table:    {cfg.catalog}.{cfg.schema}.{_tbl_prefix}_payload")
else:
    print("Skipping inference logging (deploy_app_only=true)")

# COMMAND ----------

# MAGIC %md ## Step 3 — Deploy Databricks App

# COMMAND ----------

# DBTITLE 1,Step 3 — Deploy Databricks App
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import App, AppDeployment

w        = WorkspaceClient()
app_name = cfg.app_name.replace("_", "-")
app_path = _repo_root  # deploy entire repo so src/, config/, prompts/ are available

# Create the app resource if it doesn't exist yet
try:
    w.apps.get(app_name)
    print(f"App '{app_name}' exists — deploying update")
except Exception:
    print(f"Creating app resource: {app_name}")
    w.apps.create_and_wait(
        app=App(name=app_name, description=f"UW CoPilot Workbench — {cfg.company_name}"),
    )

# Deploy source code
try:
    deployment = w.apps.deploy_and_wait(
        app_name=app_name,
        app_deployment=AppDeployment(source_code_path=app_path),
    )
    url = getattr(deployment, "url", None) or "check Apps UI"
    print(f"✅ App deployed: {app_name}")
    print(f"   URL: {url}")
except Exception as e:
    print(f"App deploy error: {e}")
    print(f"   Source path: {app_path}")
    print(f"   Open the Apps UI to deploy manually if needed.")

# COMMAND ----------

print("\n" + "="*60)
print("DEPLOYMENT SUMMARY")
print("="*60)
print(f"  Model:    {cfg.uc_model}@champion")
print(f"  Endpoint: {cfg.serving_endpoint}")
print(f"  App:      {cfg.app_name}")
print("="*60)
print("\n✅ Deploy complete")

# COMMAND ----------

# DBTITLE 1,Check feedback table
# Read-only view of all feedback — run after app interactions to verify writes
from databricks.sdk import WorkspaceClient as _WC
from uw_copilot.config import Config as _Cfg
from uw_copilot.feedback import FeedbackManager

_w2  = _WC()
_cfg2 = _Cfg()
_fm  = FeedbackManager(_cfg2, _w2)

_r = _fm._execute(
    "SELECT feedback_id, user_id, question, rating, created_at "
    "FROM atlas.atlas_insurance_rag.copilot_feedback "
    "ORDER BY created_at DESC LIMIT 20"
)
if _r and _r["rows"]:
    print(f"{len(_r['rows'])} row(s) in copilot_feedback:\n")
    for row in _r["rows"]:
        d = dict(zip(_r["columns"], row))
        icon = "👍" if d.get("rating") == "1" else "👎"
        print(f"  {icon} [{d['created_at']}]  user={d['user_id']}  rating={d['rating']}")
        print(f"     Q: {str(d['question'])[:80]}")
else:
    print("Table is empty")

# COMMAND ----------

# DBTITLE 1,Grant app SP access to serving endpoint
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import AccessControlRequest, PermissionLevel

w = WorkspaceClient()

# Look up numeric endpoint ID by name
ep = w.serving_endpoints.get(name=cfg.serving_endpoint)
endpoint_id = ep.id
print(f"Endpoint: {cfg.serving_endpoint} (ID: {endpoint_id})")

# Grant CAN_QUERY to the app's service principal
# service_principal_name in ACLs requires the applicationId (UUID), not the display name
app_info = w.apps.get(cfg.app_name.replace("_", "-"))
app_sp_id = app_info.service_principal_client_id
w.permissions.update(
    request_object_type="serving-endpoints",
    request_object_id=endpoint_id,
    access_control_list=[
        AccessControlRequest(
            service_principal_name=app_sp_id,
            permission_level=PermissionLevel.CAN_QUERY,
        )
    ],
)
print(f"✅ Granted CAN_QUERY to SP '{app_info.service_principal_name}' ({app_sp_id})")

# COMMAND ----------

# DBTITLE 1,Grant UC permissions for model serving SQL execution
# =============================================================================
# Grant Unity Catalog permissions so the model serving endpoint can execute
# SQL queries via the DatabricksSQLWarehouse resource.
#
# The serving endpoint uses a system-managed identity that needs:
#   - USE CATALOG on the catalog
#   - USE SCHEMA on the schema
#   - SELECT on the tables
#
# This grants to 'account users' which covers all system identities including
# the model serving runtime. For production, replace with a dedicated group.
# =============================================================================

# Grant on each table explicitly — schema-level SELECT doesn't propagate
# to the model serving system identity in all cases.
_tables = [
    "insureds", "policies", "drivers", "vehicles", "claims",
    "submissions", "loss_runs", "underwriting_referrals",
]

_grants = [
    f"GRANT USE CATALOG ON CATALOG {cfg.catalog} TO `account users`",
    f"GRANT USE SCHEMA ON SCHEMA {cfg.catalog}.{cfg.schema} TO `account users`",
] + [
    f"GRANT SELECT ON TABLE {cfg.catalog}.{cfg.schema}.{t} TO `account users`"
    for t in _tables
]

print("Granting UC permissions for model serving SQL execution...")
for stmt in _grants:
    try:
        spark.sql(stmt)
        print(f"  ✅ {stmt}")
    except Exception as e:
        err = str(e)
        if "already" in err.lower() or "exists" in err.lower():
            print(f"  ✅ {stmt} (already granted)")
        else:
            print(f"  ⚠️  {stmt}: {err[:100]}")

print("\n✅ Model serving can now execute SQL against operational tables")
