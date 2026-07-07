"""
tests/test_guardrails.py — GuardrailPipeline correctness tests.

Run with: pytest tests/test_guardrails.py -v
"""

import pytest

from uw_copilot.guardrails import GuardrailPipeline, GuardrailResult

# ── Minimal inline rule set (no file I/O needed) ──────────────────────────────

RULES = [
    {
        "name": "binding_opinion_blocker",
        "priority": 1,
        "action": "BLOCK",
        "trigger_phrases": ["I approve this", "coverage is bound", "I decline this"],
        "blocked_message": "I cannot make that decision.",
    },
    {
        "name": "prohibited_topic_filter",
        "priority": 2,
        "action": "BLOCK",
        "prohibited_topics": ["competitor pricing"],
        "blocked_message": "That topic is not permitted.",
    },
    {
        "name": "pii_redactor",
        "priority": 3,
        "action": "REDACT",
        "patterns": [
            {"name": "SSN",  "regex": r"\b\d{3}-\d{2}-\d{4}\b",      "replacement": "[SSN REDACTED]"},
            {"name": "PHONE","regex": r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b","replacement": "[PHONE REDACTED]"},
        ],
    },
    {
        "name": "coverage_disclaimer",
        "priority": 4,
        "action": "APPEND",
        "trigger_topics": ["coverage interpretation"],
        "disclaimer": "*This is informational only.*",
    },
    {
        "name": "citation_enforcer",
        "priority": 5,
        "action": "APPEND_IF_NO_CITATION",
        "reminder": "*Please verify against source documents.*",
    },
]


@pytest.fixture
def pipeline():
    return GuardrailPipeline(RULES)


# ── BLOCK rules ───────────────────────────────────────────────────────────────

class TestBlock:
    def test_binding_opinion_is_blocked(self, pipeline):
        result = pipeline.apply("I approve this submission for immediate binding.")
        assert result.blocked is True
        assert result.answer == "I cannot make that decision."

    def test_binding_opinion_case_insensitive(self, pipeline):
        result = pipeline.apply("After review, i approve this risk.")
        assert result.blocked is True

    def test_clean_answer_not_blocked(self, pipeline):
        result = pipeline.apply("The loss ratio is 72%, below the 75% appetite limit.")
        assert result.blocked is False

    def test_prohibited_topic_blocked(self, pipeline):
        result = pipeline.apply("Based on competitor pricing data, you should charge $5,000.")
        assert result.blocked is True
        assert result.answer == "That topic is not permitted."

    def test_block_terminates_pipeline(self, pipeline):
        """A blocked answer should NOT have PII redaction or disclaimers appended."""
        answer = "I approve this — SSN 123-45-6789"
        result = pipeline.apply(answer)
        assert result.blocked is True
        # SSN should NOT be redacted — pipeline terminated at BLOCK
        assert "SSN REDACTED" not in result.answer

    def test_block_records_rule_name(self, pipeline):
        result = pipeline.apply("I approve this submission.")
        assert any("binding_opinion_blocker" in r for r in result.applied_rules)


# ── REDACT rules ──────────────────────────────────────────────────────────────

class TestRedact:
    def test_ssn_is_redacted(self, pipeline):
        result = pipeline.apply("Driver DOB linked to SSN 123-45-6789 on file.")
        assert "123-45-6789" not in result.answer
        assert "[SSN REDACTED]" in result.answer
        assert result.blocked is False

    def test_phone_number_redacted(self, pipeline):
        result = pipeline.apply("Contact broker at 555-867-5309 for clarification.")
        assert "555-867-5309" not in result.answer
        assert "[PHONE REDACTED]" in result.answer

    def test_multiple_pii_types_redacted(self, pipeline):
        result = pipeline.apply("SSN 123-45-6789, call 555-867-5309.")
        assert "[SSN REDACTED]" in result.answer
        assert "[PHONE REDACTED]" in result.answer
        assert len(result.redacted_items) == 2

    def test_no_pii_no_redaction(self, pipeline):
        answer = "The fleet operates in Texas with a 72% loss ratio."
        result = pipeline.apply(answer)
        assert result.answer == answer or "*Please verify" in result.answer
        assert result.redacted_items == []


# ── APPEND rules ──────────────────────────────────────────────────────────────

class TestAppend:
    def test_disclaimer_appended_when_topic_matches(self, pipeline):
        result = pipeline.apply("Based on the coverage interpretation, this clause excludes...")
        assert "*This is informational only.*" in result.answer

    def test_disclaimer_not_appended_when_topic_absent(self, pipeline):
        result = pipeline.apply("The fleet has 38 units operating long-haul.")
        assert "*This is informational only.*" not in result.answer

    def test_disclaimer_not_duplicated(self, pipeline):
        answer = "coverage interpretation *This is informational only.*"
        result = pipeline.apply(answer)
        assert result.answer.count("*This is informational only.*") == 1


# ── APPEND_IF_NO_CITATION ─────────────────────────────────────────────────────

class TestCitationEnforcer:
    def test_reminder_added_when_no_citation(self, pipeline):
        result = pipeline.apply("The fleet looks acceptable.")
        assert "*Please verify against source documents.*" in result.answer

    def test_reminder_not_added_when_citation_present(self, pipeline):
        result = pipeline.apply("Per the UW Manual §3.4, loss ratio limit is 75%.")
        assert "*Please verify against source documents.*" not in result.answer

    def test_section_symbol_counts_as_citation(self, pipeline):
        result = pipeline.apply("See §3.4 for referral triggers.")
        assert "*Please verify" not in result.answer

    def test_source_reference_counts_as_citation(self, pipeline):
        result = pipeline.apply("Source 1: UW Manual (Claims Procedures)")
        assert "*Please verify" not in result.answer


# ── Priority ordering ─────────────────────────────────────────────────────────

class TestPriority:
    def test_rules_applied_in_priority_order(self):
        """Verify lower-priority APPEND doesn't run when higher-priority BLOCK fires."""
        pipeline = GuardrailPipeline([
            {"name": "blocker", "priority": 1, "action": "BLOCK",
             "trigger_phrases": ["coverage is bound"], "blocked_message": "Blocked."},
            {"name": "appender", "priority": 2, "action": "APPEND",
             "disclaimer": "APPENDED"},
        ])
        result = pipeline.apply("coverage is bound now.")
        assert result.blocked is True
        assert "APPENDED" not in result.answer
