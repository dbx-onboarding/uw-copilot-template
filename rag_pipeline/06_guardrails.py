# Databricks notebook source
# MAGIC %md
# MAGIC # 06 — Guardrails Integration Test
# MAGIC
# MAGIC Validates the 5-stage guardrail pipeline against realistic LLM responses.
# MAGIC
# MAGIC **Guardrail pipeline (priority order):**
# MAGIC 1. `binding_opinion_blocker` — BLOCK
# MAGIC 2. `prohibited_topic_filter` — BLOCK
# MAGIC 3. `pii_redactor` — REDACT + continue
# MAGIC 4. `coverage_disclaimer` — APPEND
# MAGIC 5. `citation_enforcer` — APPEND_IF_NO_CITATION

# COMMAND ----------
import subprocess, sys

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", _repo_root], check=True)

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
from uw_copilot.config     import Config
from uw_copilot.guardrails import GuardrailPipeline, GuardrailAction

cfg      = Config()
pipeline = GuardrailPipeline.from_repo_root(_repo_root)
print(f"Loaded {len(pipeline.validators)} guardrail validators")

# COMMAND ----------
# MAGIC %md ## Test Cases

# COMMAND ----------
test_cases = [
    # (description, response_text, expected_action)
    (
        "Binding opinion — should BLOCK",
        "Based on my analysis, you should bind this account at the current rate.",
        GuardrailAction.BLOCK,
    ),
    (
        "Prohibited topic (legal advice) — should BLOCK",
        "As your legal counsel, I recommend you file suit against the claimant.",
        GuardrailAction.BLOCK,
    ),
    (
        "PII in response — should REDACT",
        "The driver's SSN is 123-45-6789 and DOB is 01/15/1985.",
        GuardrailAction.REDACT,
    ),
    (
        "Coverage interpretation — should APPEND disclaimer",
        "Based on the policy terms, this loss may be covered under the physical damage section.",
        GuardrailAction.APPEND,
    ),
    (
        "Clean response with citation — should PASS",
        "Per the UW Guidelines (UW-0001, Section 4.2), HAZMAT fleets require VP UW referral. [Source: 01_uw_guidelines/UW-0001.pdf]",
        GuardrailAction.PASS,
    ),
]

print(f"{'Test':<45} {'Expected':<15} {'Actual':<15} {'Pass':<5}")
print("-" * 80)

all_pass = True
for desc, text, expected in test_cases:
    result = pipeline.apply(text)
    actual = result.action
    ok     = actual == expected
    if not ok:
        all_pass = False
    print(f"{desc[:44]:<45} {expected.value:<15} {actual.value:<15} {'✅' if ok else '❌':<5}")

print(f"\n{'✅ All guardrail tests passed' if all_pass else '❌ Some tests failed'}")

# COMMAND ----------
# MAGIC %md ## PII Redaction Detail

# COMMAND ----------
pii_test = (
    "Driver Robert Thompson (SSN: 456-78-9012, CDL: IL-CDL-88432156) "
    "was born 1978-05-12 and can be reached at (312) 555-0198."
)
result = pipeline.apply(pii_test)
print("Original:  ", pii_test)
print("Redacted:  ", result.answer)
print("Action:    ", result.action.value)

# COMMAND ----------
print("\n✅ Guardrails integration tests complete")

