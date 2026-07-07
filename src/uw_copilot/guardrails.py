"""
uw_copilot.guardrails — Five-layer guardrail pipeline.

Applied to every LLM response before it reaches the user.
Rules are loaded from prompts/guardrails_config.yaml — edit that file
to tune triggers, add prohibited topics, or change messages.

Priority order (lower number = higher priority):
  1. binding_opinion_blocker  → BLOCK  (terminates pipeline immediately)
  2. prohibited_topic_filter  → BLOCK
  3. pii_redactor             → REDACT (modifies answer, continues)
  4. coverage_disclaimer      → APPEND
  5. citation_enforcer        → APPEND_IF_NO_CITATION

Usage:
    from uw_copilot.guardrails import GuardrailPipeline
    pipeline = GuardrailPipeline.from_config_file("/path/to/guardrails_config.yaml")
    result = pipeline.apply(llm_answer)
    if result.blocked:
        return result.answer  # safe blocked message
    return result.answer      # possibly redacted + amended
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

import yaml


class GuardrailAction(str, Enum):
    """Most-significant action taken by the guardrail pipeline on a response."""
    PASS   = "pass"    # no rules fired
    APPEND = "append"  # disclaimer or citation reminder appended
    REDACT = "redact"  # PII removed (pipeline continued)
    BLOCK  = "block"   # response blocked entirely


@dataclass
class GuardrailResult:
    answer:         str
    blocked:        bool = False
    applied_rules:  List[str] = field(default_factory=list)
    redacted_items: List[str] = field(default_factory=list)

    @property
    def action(self) -> GuardrailAction:
        """Most significant action: BLOCK > REDACT > APPEND > PASS."""
        if self.blocked:
            return GuardrailAction.BLOCK
        if self.redacted_items:
            return GuardrailAction.REDACT
        if any("APPENDED" in r or "CITATION" in r for r in self.applied_rules):
            return GuardrailAction.APPEND
        return GuardrailAction.PASS


class GuardrailPipeline:
    """
    Runs guardrail rules in priority order.
    A BLOCK immediately returns a safe message without running remaining rules.
    """

    def __init__(self, rules: List[dict]):
        self.rules = sorted(rules, key=lambda r: r.get("priority", 99))

    @property
    def validators(self) -> List[dict]:
        """Alias for rules — used by notebooks to count loaded guardrails."""
        return self.rules

    @classmethod
    def from_config_file(cls, path: str) -> "GuardrailPipeline":
        with open(path) as f:
            cfg = yaml.safe_load(f)
        return cls(cfg.get("guardrails", []))

    @classmethod
    def from_repo_root(cls, repo_root: Optional[str] = None) -> "GuardrailPipeline":
        """Discover guardrails_config.yaml relative to src/uw_copilot/ or an explicit root."""
        if repo_root:
            path = Path(repo_root) / "prompts" / "guardrails_config.yaml"
        else:
            here = Path(__file__).resolve().parent
            path = here.parent.parent / "prompts" / "guardrails_config.yaml"
            if not path.exists():
                # Walk up one more level (handles both installed and editable installs)
                path = here.parent.parent.parent / "prompts" / "guardrails_config.yaml"
        if not path.exists():
            raise FileNotFoundError(f"guardrails_config.yaml not found at {path}")
        return cls.from_config_file(str(path))

    # ── Pipeline ──────────────────────────────────────────────────────────────

    def apply(self, answer: str) -> GuardrailResult:
        """
        Run all rules against answer in priority order.
        Returns a GuardrailResult — inspect .blocked before using .answer.
        """
        result = GuardrailResult(answer=answer)

        for rule in self.rules:
            action = rule.get("action", "").upper()
            name   = rule.get("name", "unknown")

            if action == "BLOCK":
                if self._should_block(answer, rule):
                    result.answer  = rule.get("blocked_message", "I cannot assist with that.")
                    result.blocked = True
                    result.applied_rules.append(f"BLOCKED by {name}")
                    return result  # terminate immediately

            elif action == "REDACT":
                answer, items = self._redact(answer, rule)
                if items:
                    result.applied_rules.append(f"REDACTED by {name}: {items}")
                    result.redacted_items.extend(items)
                result.answer = answer

            elif action == "APPEND":
                if self._should_append(answer, rule):
                    disclaimer = rule.get("disclaimer", "")
                    if disclaimer and disclaimer.strip() not in answer:
                        answer = answer + "\n\n" + disclaimer.strip()
                        result.answer = answer
                        result.applied_rules.append(f"APPENDED by {name}")

            elif action == "APPEND_IF_NO_CITATION":
                if not self._has_citation(answer):
                    reminder = rule.get("reminder", "")
                    if reminder:
                        answer = answer + "\n\n" + reminder.strip()
                        result.answer = answer
                        result.applied_rules.append(f"CITATION REMINDER by {name}")

        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _should_block(answer: str, rule: dict) -> bool:
        answer_lower = answer.lower()
        for phrase in rule.get("trigger_phrases", []):
            if phrase.lower() in answer_lower:
                return True
        for topic in rule.get("prohibited_topics", []):
            if topic.lower().replace("_", " ") in answer_lower:
                return True
        return False

    @staticmethod
    def _redact(answer: str, rule: dict):
        redacted_types: List[str] = []
        for pattern_cfg in rule.get("patterns", []):
            regex       = pattern_cfg.get("regex", "")
            replacement = pattern_cfg.get("replacement", "[REDACTED]")
            name        = pattern_cfg.get("name", "PII")
            if re.search(regex, answer):
                answer = re.sub(regex, replacement, answer)
                redacted_types.append(name)
        return answer, redacted_types

    @staticmethod
    def _should_append(answer: str, rule: dict) -> bool:
        """Only append when the answer touches a trigger topic."""
        topics = rule.get("trigger_topics", [])
        if not topics:
            return True  # no topic filter = always append
        answer_lower = answer.lower()
        return any(t.lower().replace("_", " ") in answer_lower for t in topics)

    @staticmethod
    def _has_citation(answer: str) -> bool:
        """Heuristic: answer contains a document source reference."""
        citation_patterns = [
            r"\[.{3,80}\]",            # [Document Name, §3.4]
            r"§\s*\d",                 # §3.4
            r"\bsource\s*\d",          # Source 1:
            r"\bper\s+the\b",          # per the UW Manual
            r"\baccording\s+to\b",     # according to ...
        ]
        return any(re.search(p, answer, re.IGNORECASE) for p in citation_patterns)
