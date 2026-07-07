"""
uw_copilot.structured — NL-to-SQL structured data tool.

Translates natural language questions into SQL against operational Delta tables,
executes via Statement Execution API, and formats results for the LLM.

Usage:
    from uw_copilot.structured import StructuredDataTool
    tool = StructuredDataTool(cfg, workspace_client)
    answer = tool.query("How many trucking companies do we insure?")
"""

from __future__ import annotations

import re
from typing import Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

from .config import Config


def _build_schema_context(cfg: Config) -> str:
    """Build schema context string from config catalog/schema."""
    fq = f"{cfg.catalog}.{cfg.schema}"
    return f"""You have access to the following Delta tables in the {fq} schema.
Use ONLY these tables and columns. Do NOT fabricate table or column names.

### TABLE: {fq}.insureds
Primary accounts with fleet/safety data.
Columns:
- insured_id STRING (PK, format: INS-NNNN)
- company_name STRING
- dba_name STRING
- dot_number STRING
- mc_number STRING
- state_domicile STRING (2-letter state code)
- city STRING
- years_in_business INT
- fleet_size INT
- driver_count INT
- primary_operation STRING (Long Haul, Regional, Local, Intermodal)
- primary_commodity STRING (General Freight, Refrigerated, HAZMAT, etc.)
- safety_rating STRING (Satisfactory, Conditional, Unsatisfactory)
- annual_revenue DECIMAL(15,2)
- annual_mileage BIGINT
- risk_tier STRING (Preferred, Acceptable, Borderline, Decline)
- account_manager STRING
- effective_date DATE

### TABLE: {fq}.policies
Active and expired policy records.
Columns:
- policy_id STRING (PK, format: ACI-LOB-YY-NNNNNN)
- insured_id STRING (FK to insureds)
- line_of_business STRING
- policy_status STRING (Active, Expired, Cancelled)
- effective_date DATE
- expiration_date DATE
- written_premium DECIMAL(12,2)
- liability_limit STRING
- deductible DECIMAL(10,2)
- vehicles_covered INT
- territory STRING
- broker_name STRING
- underwriter STRING
- renewal_status STRING (Renew, Review Required, Non-Renew)
- loss_ratio_current DECIMAL(5,2)

### TABLE: {fq}.drivers
CDL driver roster with MVR and telematics.
Columns:
- driver_id STRING (PK, format: DRV-NNNN)
- insured_id STRING (FK to insureds)
- first_name STRING
- last_name STRING
- cdl_class STRING (A, B, C)
- years_cdl_experience INT
- mvr_points INT (0-7 scale, 5+ is high risk)
- driver_status STRING (Active, Excluded, Terminated, Leave)
- hazmat_endorsement BOOLEAN
- accidents_3yr INT
- violations_3yr INT
- telematics_score DECIMAL(5,1) (0-100, higher is better)

### TABLE: {fq}.vehicles
Fleet vehicle inventory (power units and trailers).
Columns:
- vehicle_id STRING (PK, format: VEH-NNNN)
- insured_id STRING (FK to insureds)
- policy_id STRING (FK to policies)
- year INT
- make STRING
- model STRING
- vehicle_type STRING
- gvw INT (gross vehicle weight)
- stated_value DECIMAL(10,2)
- radius_class STRING
- garage_state STRING (2-letter state code)
- has_dashcam BOOLEAN
- has_eld BOOLEAN
- inspection_result STRING (Pass, Conditional, Fail)
- annual_mileage INT

### TABLE: {fq}.claims
Open and closed claims with reserves and litigation.
Columns:
- claim_id STRING (PK, format: CLM-YY-NNNNNNN)
- policy_id STRING (FK)
- insured_id STRING (FK)
- loss_date DATE
- claim_status STRING (Open, Closed, Reopened)
- loss_type STRING (Bodily Injury, Property Damage, Collision, Cargo, etc.)
- loss_description STRING
- fault_percentage DECIMAL(5,2)
- attorney_involved BOOLEAN
- litigation_status STRING (None, Suit Filed, In Trial, Settled)
- total_incurred DECIMAL(12,2)
- total_paid DECIMAL(12,2)
- case_reserves DECIMAL(12,2)
- large_loss_flag BOOLEAN

### TABLE: {fq}.submissions
New business and renewal submissions pipeline.
Columns:
- submission_id STRING (PK, format: SUB-YY-NNNNN)
- insured_id STRING (FK)
- company_name STRING
- broker_name STRING
- submission_date DATE
- target_effective DATE
- submission_status STRING (Received, In Review, Quoted, Bound, Declined)
- fleet_size INT
- driver_count INT
- primary_operation STRING
- primary_commodity STRING
- expiring_premium DECIMAL(12,2)
- quoted_premium DECIMAL(12,2)
- loss_ratio_3yr DECIMAL(5,2)
- underwriter STRING
- referral_required BOOLEAN
- decline_reason STRING

### TABLE: {fq}.loss_runs
Historical loss experience by policy period.
Columns:
- loss_run_id STRING (PK)
- insured_id STRING (FK)
- policy_id STRING (FK)
- policy_period STRING (format: YYYY-YYYY)
- num_claims INT
- total_incurred DECIMAL(12,2)
- total_paid DECIMAL(12,2)
- total_reserves DECIMAL(12,2)
- earned_premium DECIMAL(12,2)
- loss_ratio DECIMAL(7,2)
- large_losses INT
- frequency DECIMAL(5,2)
- severity DECIMAL(12,2)

### TABLE: {fq}.underwriting_referrals
Authority escalation decisions.
Columns:
- referral_id STRING (PK, format: REF-YY-NNN)
- submission_id STRING (FK)
- insured_id STRING (FK)
- referral_date DATE
- referral_reason STRING
- referral_tier STRING (VP Underwriting, CCO, Reserve Committee)
- decision STRING (Approved, Approved with Conditions, Declined, Pending)
- conditions STRING

### COMMON JOINS:
- insureds.insured_id = policies.insured_id
- insureds.insured_id = drivers.insured_id
- insureds.insured_id = vehicles.insured_id
- policies.policy_id = vehicles.policy_id
- insureds.insured_id = claims.insured_id
- policies.policy_id = claims.policy_id
- insureds.insured_id = loss_runs.insured_id
- insureds.insured_id = submissions.insured_id
- insureds.insured_id = underwriting_referrals.insured_id
"""


class StructuredDataTool:
    """NL-to-SQL tool for operational Delta table queries."""

    def __init__(self, cfg: Config, w: WorkspaceClient):
        self.cfg = cfg
        self.w = w
        self.schema_context = _build_schema_context(cfg)
        self.sql_prompt = self._build_sql_prompt()

    def _build_sql_prompt(self) -> str:
        return f"""You are a SQL generation assistant for {self.cfg.company_name}.
Your job is to translate natural language questions into valid Databricks SQL queries.

{self.schema_context}

RULES:
1. Generate ONLY a single SELECT statement. No DDL, DML, or multiple statements.
2. Always qualify tables with the full path: {self.cfg.catalog}.{self.cfg.schema}.<table_name>
3. Use column names EXACTLY as documented above.
4. For text matching, use ILIKE for case-insensitive partial matches.
5. Return at most 20 rows unless the user asks for all.
6. Include ORDER BY for ranked/sorted queries.
7. Use appropriate JOINs when data spans multiple tables.
8. For monetary values, use CONCAT(', FORMAT_NUMBER(col, 0)) for readability.
9. Return ONLY the SQL query - no explanation, no markdown code fences.
10. If the question cannot be answered from these tables, return: -- CANNOT_ANSWER
"""

    def query(self, question: str) -> str:
        """
        Full NL-to-SQL pipeline: generate SQL, execute, format results.
        Returns a natural language answer with data.
        """
        sql = self._generate_sql(question)

        if not sql or sql.strip().startswith("--"):
            return "I cannot answer that question from the operational data tables."

        success, result = self._execute_sql(sql)
        if not success:
            return f"I tried to query the data but encountered an issue: {result}"

        return self._format_answer(question, sql, result)

    def _generate_sql(self, question: str) -> str:
        """Use the LLM to translate NL question to SQL."""
        messages = [
            ChatMessage(role=ChatMessageRole.SYSTEM, content=self.sql_prompt),
            ChatMessage(role=ChatMessageRole.USER, content=question),
        ]

        response = self.w.serving_endpoints.query(
            name=self.cfg.chat_model,
            messages=messages,
            max_tokens=500,
            temperature=0.0,
        )

        sql = response.choices[0].message.content.strip()

        # Clean up markdown fences
        if sql.startswith("```"):
            sql = sql.split("\n", 1)[1] if "\n" in sql else sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        return sql.strip()

    def _execute_sql(self, sql: str) -> tuple:
        """
        Execute SQL via Statement Execution API with safety checks.
        Returns (success, result_rows_or_error_message).
        """
        sql_upper = sql.upper().strip()

        # Safety: block non-SELECT
        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "MERGE"]
        for kw in dangerous:
            if re.search(rf"\b{kw}\b", sql_upper):
                return False, f"Blocked: {kw} statements are not allowed."

        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT queries are permitted."

        if not self.cfg.warehouse_id:
            return False, "No SQL warehouse configured. Set warehouse_id in company_config.yaml."

        try:
            result = self.w.statement_execution.execute_statement(
                warehouse_id=self.cfg.warehouse_id,
                statement=sql,
                wait_timeout="30s",
            )
            # Check for execution errors in the result status
            if result.status and result.status.state and result.status.state.value in ("FAILED", "CANCELED", "CLOSED"):
                err_msg = getattr(result.status, 'error', None)
                return False, f"SQL execution failed: {err_msg}"
            columns = [col.name for col in (result.manifest.schema.columns or [])]
            rows = result.result.data_array or []
            return True, {"columns": columns, "rows": rows, "sql": sql}
        except Exception as e:
            return False, f"SQL execution error: {str(e)[:200]}"

    def _format_answer(self, question: str, sql: str, data: dict) -> str:
        """Format SQL results into a readable context block for the LLM."""
        columns = data["columns"]
        rows = data["rows"]

        if not rows:
            return f"Query returned no results.\n\nSQL used: {sql}"

        # Build a text table
        header = " | ".join(columns)
        separator = "-" * len(header)
        lines = [f"## Structured Data Query Results\n", f"**Query:** {question}\n"]
        lines.append(f"| {header} |")
        lines.append(f"| {' | '.join(['---'] * len(columns))} |")

        for row in rows[:20]:
            formatted = " | ".join(str(v) if v is not None else "NULL" for v in row)
            lines.append(f"| {formatted} |")

        lines.append(f"\n*{len(rows)} row(s) returned*")
        return "\n".join(lines)
