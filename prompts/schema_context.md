# Operational Data Schema — NL-to-SQL Context
#
# This file is loaded by 05_structured_data as the schema documentation
# for natural language to SQL generation.
# Update this file if you add, rename, or change operational tables.

You have access to the following Delta tables in the `{catalog}.{schema_prefix}_rag` schema.
Use these tables to answer questions about specific accounts, fleets, claims, and policies.
Always filter by insured identifiers when provided. Use the company context to infer NAICS codes if not stated.

---

## Table: insureds

One row per insured entity.

| Column | Type | Description |
|---|---|---|
| insured_id | STRING | Primary key. Format: INS-NNNN |
| company_name | STRING | Legal company name |
| naics_code | STRING | 6-digit NAICS code |
| naics_description | STRING | Human-readable NAICS sector |
| state | STRING | Primary operating state (2-letter) |
| fleet_size | INT | Number of vehicles on risk |
| fleet_size_band | STRING | SMALL (<10), MEDIUM (10-50), LARGE (50-200), ENTERPRISE (200+) |
| years_in_business | INT | Years since company founded |
| years_band | STRING | NEW (<3), ESTABLISHED (3-10), VETERAN (10+) |
| commodity_type | STRING | Primary commodity hauled |
| operating_radius | STRING | LOCAL, INTERMEDIATE, LONG_HAUL |
| created_at | TIMESTAMP | |

**Example queries:**
- "Find all insureds in Texas with large fleets" → `WHERE state = 'TX' AND fleet_size_band = 'LARGE'`
- "How many insureds are HAZMAT operators?" → filter `commodity_type LIKE '%HAZMAT%'`

---

## Table: drivers

One row per driver on a policy schedule.

| Column | Type | Description |
|---|---|---|
| driver_id | STRING | Primary key. Format: DRV-NNNN |
| insured_id | STRING | Foreign key → insureds |
| full_name | STRING | Driver name |
| cdl_class | STRING | A, B, or C |
| years_experience | INT | Years of CDL experience |
| mvr_points | INT | Current MVR violation points |
| csa_basic_score | FLOAT | FMCSA BASIC composite score (0–100) |
| date_of_birth | DATE | PII — masked for roles without pii_access |
| status | STRING | ACTIVE, TERMINATED, SUSPENDED |

**Example queries:**
- "How many drivers for INS-1001 have more than 5 MVR points?" → `WHERE insured_id = 'INS-1001' AND mvr_points > 5`
- "Show drivers with CSA scores above 65" → `WHERE csa_basic_score > 65`

---

## Table: policies

One row per policy period.

| Column | Type | Description |
|---|---|---|
| policy_id | STRING | Primary key. Format: POL-NNNN |
| insured_id | STRING | Foreign key → insureds |
| policy_number | STRING | External policy number |
| effective_date | DATE | Coverage start |
| expiration_date | DATE | Coverage end |
| written_premium | DECIMAL(12,2) | Premium charged |
| policy_status | STRING | ACTIVE, EXPIRED, CANCELLED, NON_RENEWED |
| liability_limit | DECIMAL(12,2) | Primary liability limit |
| underwriter_id | STRING | Assigned underwriter |
| notes | STRING | Underwriter notes |

---

## Table: claims

One row per claim.

| Column | Type | Description |
|---|---|---|
| claim_id | STRING | Primary key. Format: CLM-NNNN |
| policy_id | STRING | Foreign key → policies |
| insured_id | STRING | Foreign key → insureds |
| driver_id | STRING | Driver involved (nullable) |
| occurrence_date | DATE | Date of loss |
| report_date | DATE | Date claim was reported |
| claim_type | STRING | AUTO_LIABILITY, CARGO, PHYSICAL_DAMAGE, GENERAL_LIABILITY |
| incurred_loss | DECIMAL(12,2) | Total incurred loss amount |
| paid_loss | DECIMAL(12,2) | Amount paid to date |
| reserved_loss | DECIMAL(12,2) | Remaining reserve |
| claim_status | STRING | OPEN, CLOSED, REOPENED |
| large_loss_flag | BOOLEAN | True if incurred_loss > $100,000 |

---

## Table: loss_runs

One row per insured per policy year (actuarial summary).

| Column | Type | Description |
|---|---|---|
| loss_run_id | STRING | Primary key |
| insured_id | STRING | Foreign key → insureds |
| policy_year | INT | Calendar year |
| earned_premium | DECIMAL(12,2) | Earned premium for the year |
| incurred_loss | DECIMAL(12,2) | Total incurred loss for the year |
| loss_ratio | FLOAT | incurred_loss / earned_premium (e.g. 0.85 = 85%) |
| claim_count | INT | Number of claims in the year |
| large_loss_count | INT | Number of claims > $100K |

**Example queries:**
- "What is the 3-year loss ratio for INS-1002?" → aggregate loss_runs WHERE insured_id = 'INS-1002' AND policy_year >= YEAR(CURRENT_DATE) - 3
- "List all insureds with loss ratios above 80% last year" → filter loss_ratio > 0.80

---

## Table: submissions

One row per new business submission.

| Column | Type | Description |
|---|---|---|
| submission_id | STRING | Primary key. Format: SUB-NNNN |
| insured_id | STRING | Foreign key → insureds (nullable until bound) |
| insured_name | STRING | Submission applicant name |
| received_at | TIMESTAMP | When submission landed in S3 |
| broker_id | STRING | Submitting broker |
| status | STRING | NEW, REVIEW, IN_PROGRESS, ESCALATED, APPROVED, DECLINED |
| ai_score | INT | AI-generated risk score (0–100, higher = higher risk) |
| risk_level | STRING | LOW, MEDIUM, HIGH |
| referral_flag | BOOLEAN | True if AI recommends referral to senior UW |
| completeness_pct | FLOAT | % of required documents received |
| missing_docs | ARRAY<STRING> | List of missing document types |
| notes | STRING | Underwriter notes |

---

## Table: loss_ratios

Pre-computed summary by insured, used for quick lookups.

| Column | Type | Description |
|---|---|---|
| insured_id | STRING | Foreign key → insureds |
| three_year_loss_ratio | FLOAT | Average loss ratio over last 3 policy years |
| five_year_loss_ratio | FLOAT | Average loss ratio over last 5 policy years |
| ytd_loss_ratio | FLOAT | Current year to date |
| trend | STRING | IMPROVING, STABLE, DETERIORATING |
| as_of_date | DATE | Last refresh date |

---

## Table: referrals

One row per referral event.

| Column | Type | Description |
|---|---|---|
| referral_id | STRING | Primary key |
| submission_id | STRING | Foreign key → submissions |
| insured_id | STRING | Foreign key → insureds |
| referred_by | STRING | Underwriter who escalated |
| referred_to | STRING | Senior underwriter or specialist |
| referral_reason | STRING | Free text reason for referral |
| referral_date | TIMESTAMP | When referral was created |
| resolution | STRING | APPROVED, DECLINED, PENDING |
| resolution_date | TIMESTAMP | When referral was resolved (nullable) |

---

## Common Join Patterns

```sql
-- Loss ratio for a specific insured
SELECT lr.three_year_loss_ratio
FROM loss_ratios lr
WHERE lr.insured_id = 'INS-1002'

-- All open submissions with missing documents
SELECT s.submission_id, s.insured_name, s.missing_docs
FROM submissions s
WHERE s.status IN ('NEW', 'REVIEW')
  AND s.completeness_pct < 1.0

-- Drivers above CSA threshold for a given insured
SELECT d.full_name, d.csa_basic_score, d.mvr_points
FROM drivers d
JOIN insureds i ON d.insured_id = i.insured_id
WHERE i.insured_id = '{insured_id}'
  AND d.csa_basic_score > 65
  AND d.status = 'ACTIVE'
```
