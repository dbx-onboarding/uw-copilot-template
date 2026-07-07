# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Create Tables
# MAGIC
# MAGIC Creates all Delta tables for the UW CoPilot platform.
# MAGIC Safe to re-run — all statements use `CREATE TABLE IF NOT EXISTS`.
# MAGIC
# MAGIC **Operational tables (8):** insureds, policies, drivers, vehicles,
# MAGIC claims, submissions, loss_runs, underwriting_referrals
# MAGIC
# MAGIC **Pipeline tables (5):** parsed_documents, document_chunks,
# MAGIC conversation_sessions, copilot_feedback, feedback_overrides

# COMMAND ----------

# DBTITLE 1,Setup sys.path
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

# DBTITLE 1,Setup catalog/schema
from uw_copilot.config import Config

cfg = Config()
C   = cfg.catalog
S   = cfg.schema

spark.sql(f"CREATE CATALOG IF NOT EXISTS {C}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {C}.{S}")
# NOTE: spark.conf.set('spark.databricks.delta.schema.autoMerge.enabled', 'true')
# is NOT supported on serverless. Use .option('mergeSchema', 'true') on writes instead.
print(f"Using {C}.{S}")

# COMMAND ----------

# MAGIC %md ## Operational Tables

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.insureds (
    insured_id          STRING  NOT NULL COMMENT 'Unique insured identifier (INS-XXXX)',
    company_name        STRING  NOT NULL COMMENT 'Legal entity name',
    dba_name            STRING  COMMENT 'Doing business as',
    dot_number          STRING  COMMENT 'USDOT number',
    mc_number           STRING  COMMENT 'Motor Carrier number',
    state_domicile      STRING  COMMENT 'State of domicile (2-letter)',
    city                STRING,
    years_in_business   INT     COMMENT 'Years under current authority',
    fleet_size          INT     COMMENT 'Total power units',
    driver_count        INT     COMMENT 'Active scheduled drivers',
    primary_operation   STRING  COMMENT 'Long Haul, Regional, Local, Intermodal, Dedicated',
    primary_commodity   STRING  COMMENT 'Primary cargo type',
    safety_rating       STRING  COMMENT 'Satisfactory, Conditional, Unsatisfactory, None',
    csa_unsafe_driving  DECIMAL(5,1),
    csa_hos             DECIMAL(5,1),
    csa_vehicle_maint   DECIMAL(5,1),
    csa_driver_fitness  DECIMAL(5,1),
    annual_revenue      DECIMAL(15,2),
    annual_mileage      BIGINT,
    telematics_provider STRING,
    dashcam_coverage_pct DECIMAL(5,2),
    risk_tier           STRING  COMMENT 'Preferred, Acceptable, Borderline, Decline',
    account_manager     STRING,
    effective_date      DATE,
    CONSTRAINT pk_insureds PRIMARY KEY (insured_id)
)
COMMENT 'Fleet customers and policyholders'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  insureds OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.policies (
    policy_id           STRING  NOT NULL,
    insured_id          STRING  NOT NULL COMMENT 'FK to insureds',
    line_of_business    STRING,
    policy_status       STRING  COMMENT 'Active, Expired, Cancelled, Non-Renewed',
    effective_date      DATE,
    expiration_date     DATE,
    written_premium     DECIMAL(12,2),
    liability_limit     STRING,
    aggregate_limit     STRING,
    deductible          DECIMAL(10,2),
    vehicles_covered    INT,
    territory           STRING,
    broker_name         STRING,
    underwriter         STRING,
    renewal_status      STRING  COMMENT 'Auto-Renew, Review Required, Non-Renew',
    loss_ratio_current  DECIMAL(5,2),
    CONSTRAINT pk_policies PRIMARY KEY (policy_id)
)
COMMENT 'Insurance policies'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  policies OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.drivers (
    driver_id               STRING  NOT NULL COMMENT 'DRV-NNNN',
    insured_id              STRING  NOT NULL,
    first_name              STRING,
    last_name               STRING,
    cdl_number              STRING,
    cdl_state               STRING,
    cdl_class               STRING  COMMENT 'A, B, or C',
    date_of_birth           DATE,
    hire_date               DATE,
    years_cdl_experience    INT,
    mvr_points              INT,
    mvr_date                DATE,
    driver_status           STRING  COMMENT 'Active, Excluded, Terminated, Leave',
    disqualifying_offense   BOOLEAN,
    hazmat_endorsement      BOOLEAN,
    tanker_endorsement      BOOLEAN,
    accidents_3yr           INT,
    violations_3yr          INT,
    telematics_score        DECIMAL(5,1),
    CONSTRAINT pk_drivers PRIMARY KEY (driver_id)
)
COMMENT 'Driver roster with qualification and MVR data'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  drivers OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.vehicles (
    vehicle_id          STRING  NOT NULL COMMENT 'VEH-NNNN',
    insured_id          STRING  NOT NULL,
    policy_id           STRING,
    vin                 STRING,
    year                INT,
    make                STRING,
    model               STRING,
    vehicle_type        STRING,
    gvw                 INT,
    stated_value        DECIMAL(10,2),
    radius_class        STRING,
    garage_state        STRING,
    garage_zip          STRING,
    has_dashcam         BOOLEAN,
    has_eld             BOOLEAN,
    last_inspection_date DATE,
    inspection_result   STRING  COMMENT 'Pass, Conditional, Fail',
    annual_mileage      INT,
    CONSTRAINT pk_vehicles PRIMARY KEY (vehicle_id)
)
COMMENT 'Fleet vehicle inventory'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  vehicles OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.claims (
    claim_id            STRING  NOT NULL COMMENT 'CLM-YY-NNNNNNN',
    policy_id           STRING  NOT NULL,
    insured_id          STRING  NOT NULL,
    loss_date           DATE,
    report_date         DATE,
    claim_status        STRING  COMMENT 'Open, Closed, Reopened, Subrogation',
    loss_type           STRING,
    loss_description    STRING,
    fault_percentage    DECIMAL(5,2),
    claimant_name       STRING,
    adjuster            STRING,
    attorney_involved   BOOLEAN,
    litigation_status   STRING  COMMENT 'None, Pre-Suit, Suit Filed, Trial Set, Settled',
    total_incurred      DECIMAL(12,2),
    total_paid          DECIMAL(12,2),
    case_reserves       DECIMAL(12,2),
    expense_paid        DECIMAL(12,2),
    subrogation_amount  DECIMAL(12,2),
    siu_referral        BOOLEAN,
    large_loss_flag     BOOLEAN COMMENT '>=250K incurred',
    catastrophic_flag   BOOLEAN COMMENT 'Fatality or permanent injury',
    closure_date        DATE,
    CONSTRAINT pk_claims PRIMARY KEY (claim_id)
)
COMMENT 'Claims master with reserves, payments, litigation status'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  claims OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.submissions (
    submission_id       STRING  NOT NULL COMMENT 'SUB-YY-NNNNN',
    insured_id          STRING,
    company_name        STRING,
    broker_name         STRING,
    broker_contact      STRING,
    submission_date     DATE,
    target_effective    DATE,
    submission_status   STRING  COMMENT 'Received, In Review, Quoted, Bound, Declined, Lost',
    fleet_size          INT,
    driver_count        INT,
    primary_operation   STRING,
    primary_commodity   STRING,
    requested_limits    STRING,
    expiring_premium    DECIMAL(12,2),
    quoted_premium      DECIMAL(12,2),
    loss_ratio_3yr      DECIMAL(5,2),
    underwriter         STRING,
    referral_required   BOOLEAN,
    decline_reason      STRING,
    days_to_quote       INT,
    CONSTRAINT pk_submissions PRIMARY KEY (submission_id)
)
COMMENT 'Broker submission pipeline'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  submissions OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.loss_runs (
    loss_run_id     STRING  NOT NULL,
    insured_id      STRING  NOT NULL,
    policy_id       STRING,
    policy_period   STRING  COMMENT 'e.g. 2024-2025',
    valuation_date  DATE,
    num_claims      INT,
    total_incurred  DECIMAL(12,2),
    total_paid      DECIMAL(12,2),
    total_reserves  DECIMAL(12,2),
    earned_premium  DECIMAL(12,2),
    loss_ratio      DECIMAL(7,2)  COMMENT 'Can exceed 100%',
    large_losses    INT,
    frequency       DECIMAL(5,2)  COMMENT 'Claims per power unit',
    severity        DECIMAL(12,2) COMMENT 'Avg claim cost',
    CONSTRAINT pk_loss_runs PRIMARY KEY (loss_run_id)
)
COMMENT 'Historical loss experience by policy period'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  loss_runs OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.underwriting_referrals (
    referral_id             STRING  NOT NULL,
    submission_id           STRING,
    policy_id               STRING,
    insured_id              STRING  NOT NULL,
    referral_date           DATE,
    referral_reason         STRING,
    referral_tier           STRING  COMMENT 'Claims Director, VP UW, CCO, Reserve Committee',
    requesting_underwriter  STRING,
    approving_authority     STRING,
    decision                STRING  COMMENT 'Approved, Approved with Conditions, Declined',
    conditions              STRING,
    decision_date           DATE,
    notes                   STRING,
    CONSTRAINT pk_referrals PRIMARY KEY (referral_id)
)
COMMENT 'Underwriting referrals requiring elevated authority'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  underwriting_referrals OK")

# COMMAND ----------

# MAGIC %md ## Pipeline Tables

# COMMAND ----------

# DBTITLE 1,Pipeline tables (serverless-compatible, no DEFAULT clauses)
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.parsed_documents (
    doc_id          STRING      NOT NULL,
    source_path     STRING      NOT NULL,
    file_name       STRING,
    category        STRING      COMMENT 'Matches doc_categories[].label in company_config.yaml',
    category_id     STRING      COMMENT 'Matches doc_categories[].id (S3 subfolder name)',
    parsed_text     STRING      COMMENT 'Full extracted text',
    page_count      INT,
    file_size_bytes BIGINT,
    parsed_at       TIMESTAMP,
    content_hash    STRING      COMMENT 'SHA-256 for dedup',
    CONSTRAINT pk_parsed_documents PRIMARY KEY (doc_id)
)
COMMENT 'All parsed PDF documents. Source table for Vector Search chunking.'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  parsed_documents OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.document_chunks (
    chunk_id    STRING      NOT NULL COMMENT 'P-... for parent, C-... for child',
    parent_id   STRING      COMMENT 'NULL for parent chunks',
    chunk_type  STRING      NOT NULL COMMENT 'parent or child',
    chunk_text  STRING,
    doc_id      STRING      NOT NULL,
    category    STRING,
    source_path STRING,
    char_start  INT,
    char_end    INT,
    created_at  TIMESTAMP,
    CONSTRAINT pk_document_chunks PRIMARY KEY (chunk_id)
)
COMMENT 'Hierarchical chunks. child chunks are VS retrieval targets.'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  document_chunks OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.conversation_sessions (
    session_id  STRING      NOT NULL,
    role        STRING      NOT NULL COMMENT 'user, assistant, or system',
    content     STRING      NOT NULL,
    user_id     STRING,
    created_at  TIMESTAMP
)
COMMENT 'Conversation memory. Retained 90 days per data retention policy.'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
""")
print(f"  conversation_sessions OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.copilot_feedback (
    feedback_id STRING      NOT NULL,
    session_id  STRING      NOT NULL,
    user_id     STRING,
    question    STRING      NOT NULL,
    answer      STRING      NOT NULL,
    rating      INT         COMMENT '1 = thumbs up, -1 = thumbs down',
    comment     STRING,
    created_at  TIMESTAMP,
    CONSTRAINT pk_copilot_feedback PRIMARY KEY (feedback_id)
)
COMMENT 'User feedback on CoPilot responses.'
""")
print(f"  copilot_feedback OK")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {C}.{S}.feedback_overrides (
    override_id         STRING      NOT NULL,
    session_id          STRING,
    user_id             STRING      NOT NULL,
    submission_id       STRING,
    ai_recommendation   STRING,
    uw_decision         STRING      NOT NULL,
    override_reason     STRING      COMMENT 'Established Relationship, Risk Characteristic, etc.',
    override_detail     STRING,
    created_at          TIMESTAMP,
    CONSTRAINT pk_feedback_overrides PRIMARY KEY (override_id)
)
COMMENT 'Underwriter decisions that diverge from AI recommendations.'
""")
print(f"  feedback_overrides OK")

# COMMAND ----------

print(f"\n✅ All tables created in {C}.{S}")
display(spark.sql(f"SHOW TABLES IN {C}.{S}"))
