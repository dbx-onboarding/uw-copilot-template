# UW CoPilot — Technical Architecture & Engineering Design

| | |
|:---|:---|
| **Version** | 3.1 |
| **Status** | Draft — for engineering and data teams |
| **Author** | Solution Architecture |
| **Reference Implementation** | Atlas Commercial Insurance |
| **Platform** | Databricks on AWS |
| **Companion document** | UW_COPILOT_TEMPLATE_SPEC.md (Executive Architecture) |

---

This document contains the implementation detail behind the UW CoPilot. Audience: engineers, data engineers, and ML engineers building or maintaining the system. For business and product context, see the companion Executive Architecture document.

---

## 1. Non-Functional Requirements

| Requirement | Target | Notes |
|:---|:---|:---|
| Availability | 99.9% (business hours) | Measured 8 AM – 8 PM weekdays; planned maintenance window is infra stop/start |
| End-to-end response time | < 5 seconds (p95) | Query submission to response delivery, including retrieval and guardrails |
| Time to first token | < 2 seconds | Streaming response begins before full answer is assembled |
| Concurrent users | 250 simultaneous sessions | Model Serving endpoint scaled to handle peak load |
| Document intake throughput | 500 files per 15-min cycle | Per intake job run; larger volumes extend the cycle, not skip files |
| Vector index freshness | < 20 min from S3 file arrival | Includes Auto Loader pickup (0–15 min) + VS Delta Sync (~2 min) |
| Max document size | 250 MB per file | ai_parse_document() limit; larger files should be split before intake |
| Session memory retention | 90 days (configurable) | conversation_sessions table; older sessions purged on schedule |
| Audit log retention | 7 years | UC system tables (system.access.audit); regulatory requirement for insurance |
| Disaster recovery (RTO) | < 1 hour | Full infra recreatable from Delta tables + DAB bundle; no data loss |
| Recovery Point Objective (RPO) | < 15 minutes | Last completed intake job run; Delta log provides exact recovery point |
| Model version rollback | < 5 minutes | MLflow alias reassignment; serving endpoint points to prior registered version |

---

## 2. Security Architecture

### Network Boundary

All data processing stays within the AWS VPC and Databricks workspace. No submission data, document content, or query/response traffic leaves the customer's perimeter.

| Layer | Control |
|:---|:---|
| S3 → Databricks | S3 bucket registered as Unity Catalog External Location; access via IAM role assumption — no static credentials |
| Model Serving | Runs in isolated Databricks-managed container; no public internet egress in production |
| Databricks App | Served from Databricks-managed infrastructure; SSO (SAML/OIDC) required for access |
| LLM API calls | Claude Sonnet 4 via Databricks Model Serving; calls routed through Databricks, not directly to Anthropic |

### Authentication and Identity

| Component | Mechanism |
|:---|:---|
| User access | Databricks SSO — SAML or OIDC via corporate IdP |
| Service principals | Personal Access Tokens stored in Databricks Secrets (never in code or YAML) |
| S3 access | IAM role (instance profile) attached to job clusters — no access keys |
| Serving endpoint | Databricks token auth; app uses service principal, not user credentials |

### Secrets Management

All credentials, tokens, and connection strings are stored in Databricks Secret Scopes — never in notebooks, config files, or environment variables. Reference pattern:

```python
# Correct — credential never appears in code
api_key = dbutils.secrets.get(scope="uw-copilot", key="anthropic-api-key")

# Wrong — never do this
api_key = "sk-ant-..."
```

### Unity Catalog Governance

| Control | Implementation |
|:---|:---|
| Table access | GRANT/REVOKE at catalog, schema, and table level via UC |
| Row filters | Applied on operational tables — brokers see only their own submissions |
| Column masks | PII fields (SSN, CDL numbers, DOBs) masked for roles without PII access |
| Lineage | Full column-level lineage tracked automatically for all Delta tables |
| Audit logs | All data access, model serving calls, and VS queries written to `system.access.audit` |
| External Location | S3 bucket registered under UC — access controlled by UC policy, not bucket policy alone |

### RBAC at the Retrieval Layer

Document access is enforced at the Vector Search query — not the application layer. A role's category whitelist is passed as a metadata filter before the LLM ever receives retrieved content. See Section 10 for the full policy definition.

### Column Masking — PII Fields

```sql
-- Applied to parsed_documents and document_chunks
-- Roles without PII_ACCESS privilege see redacted values

CREATE OR REPLACE FUNCTION mask_pii(value STRING)
RETURNS STRING
RETURN CASE
  WHEN is_member('pii_access') THEN value
  ELSE regexp_replace(value, '\\b\\d{3}-\\d{2}-\\d{4}\\b', '[SSN REDACTED]')
END;

ALTER TABLE atlas_insurance_rag.parsed_documents
ALTER COLUMN parsed_text
SET MASK mask_pii;
```

### Insurance Regulatory Considerations

* All AI recommendations are advisory — no automated binding, approval, or decline of any risk
* Full audit trail: every query, response, and underwriter decision is logged with user identity and timestamp
* Override decisions are captured with stated reason — defensible record for regulatory review
* Model versioning in MLflow UC registry provides complete history of which model version produced which recommendations

---

## 3. AI Services

| Service | Responsibility | v1 | v2+ |
|:---|:---|:---|:---|
| **Ingestion Service** | S3 → Document AI parsing → hierarchical chunks → Delta append | Yes | + Email parsing, ACORD field extraction |
| **Retrieval Service** | Hybrid semantic + keyword search, RBAC category filtering, top-k | Yes | + Cross-encoder reranking |
| **Conversation Service** | Session memory in Delta, history compression, multi-turn context | Yes | + Session summarisation and handoff |
| **Analytics Service** | Intent routing, NL-to-SQL against operational tables | Yes | + External data connectors |
| **Governance Service** | 5 post-LLM output validators | Yes | Per-role guardrail profiles |
| **Evaluation Service** | LLM-judge scoring, feedback capture, override export | Yes | A/B model comparison, regression on deploy |
| **Similarity Service** | Historical risk matching against structured risk profiles | No | v2 — see Section 8 |
| **Pricing Intelligence** | Suggests pricing bands from historical premium, loss ratios, similar risks | No | v3 — see Section 9 |

---

## 4. End-to-End Architecture

### Submission Intake Flow

```
Broker / External System
        ↓
S3  s3://{company}-submissions/{category}/file.pdf
        ↓
Auto Loader  (every 15 min — new files only, checkpoint-based)
        ↓
Ingestion Service
  ai_parse_document()   → text + tables + structure
  HierarchicalChunker   → parent chunks (2,500 chars) + child chunks (600 chars)
  category_label        ← tagged from S3 subfolder → used for RBAC filtering
        ↓
Delta Tables:  parsed_documents (append)  →  document_chunks (append)
        ↓
Vector Search Delta Sync  (automatic — no manual trigger)
        ↓
Document searchable in CoPilot  ←  5–20 min end-to-end
```

**Future: Event-Driven Intake**  
v1 uses scheduled polling (every 15 min). Future versions may replace this with S3 event notifications (S3 → EventBridge → SNS → Jobs API) to support near real-time submission processing with < 5 min end-to-end latency. The pipeline code remains unchanged — only the trigger mechanism changes.

### Query Flow

```
Underwriter opens Workbench (Databricks App)
        ↓
Selects submission from queue  →  AI Summary panel loads
Asks a question in chat
        ↓
App → Model Serving endpoint  { messages, session_id, user_role }
        ↓
Conversation Service    → retrieves prior session history from Delta
Retrieval Service       → RBAC filter: category whitelist by user_role
                        → Intent Router: document search or SQL query?
                        → Vector Search: hybrid ANN + BM25, top-k
                        → OR: NL-to-SQL against operational Delta tables
RAG Agent               → assembles context window
                        → LLM generates answer with inline citations
Governance Service      → 5 guardrails validated in priority order
        ↓
Response:  answer + sources + guardrail_status
        ↓
App renders:  answer text  ·  expandable citations  ·  👍/👎 feedback
Conversation Service    → appends exchange to session history
Evaluation Service      → records feedback if submitted
Override loop           → if UW changes AI decision, captures reason
```

---

## 5. Workbench Architecture

The Workbench is the primary user interface — not an afterthought bolted onto a chat UI. It is a first-class architectural component with its own data contracts and state management.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  WORKBENCH UI  (Streamlit on Databricks Apps)                                │
├────────────────┬──────────────────────────────┬──────────────────────────────┤
│  SUBMISSION    │  SUMMARY PANEL               │  COMPANION PANEL             │
│  QUEUE         │                              │                              │
│                │  Insured / Fleet / Hazard    │  CHAT INTERFACE              │
│  [Filter]      │  Loss History                │  ─────────────────           │
│  [Sort]        │  Document Status             │  Question input              │
│  [Search]      │  Risk Indicators             │  Response + citations        │
│                │  ─────────────────           │  Session history             │
│  Submission 1  │  AI Assessment + Confidence  │                              │
│  Submission 2  │  ─────────────────           │  ─────────────────           │
│  Submission 3  │  [Escalate] [Approve] [Decl] │  HISTORICAL SIMILAR RISKS    │
│  ...           │  ─────────────────           │  23 similar accounts         │
│                │  Override Reason (if any)    │  Avg loss ratio: 78%         │
│                │  [________________________]  │  Non-renewal rate: 71%       │
│                │                              │                              │
│                │                              │  ─────────────────           │
│                │                              │  EVIDENCE CITATIONS          │
│                │                              │  UW Manual §3.4              │
│                │                              │  Driver Qualif. §2.1         │
└────────────────┴──────────────────────────────┴──────────────────────────────┘
```

### Component Data Sources

| Component | Data source | Refresh |
|:---|:---|:---|
| Submission Queue | `submissions` table (operational) | On page load + manual refresh |
| Summary Panel | `submission_summaries` table | Generated on intake; cached |
| Risk Indicators | `submission_summaries.risk_indicators` (JSON) | Part of summary generation |
| Historical Similar Risks | Similarity Service → `historical_cohorts` | On-demand query when submission selected |
| Chat Interface | Model Serving endpoint | Real-time per message |
| Evidence Citations | Vector Search results metadata | Included in chat response |
| Override Capture | `feedback_overrides` table | Written on action button click |

### State Management

* **Session state**: Scoped to browser tab via `session_id` (generated at page load)
* **Selected submission**: Stored in Streamlit session state; drives Summary and Companion panels
* **Chat history**: Persisted in `conversation_sessions` Delta table; survives page refresh if same `session_id`
* **Override state**: Written immediately on action; no local buffering

---

## 6. Hierarchical Chunking

Insurance documents are long structured documents where section headings carry critical context. Flat chunking loses that context.

| Parameter | Value | Rationale |
|:---|:---|:---|
| Parent chunk size | 2,500 chars | Large enough to contain full sections with context |
| Child chunk size | 600 chars | Precise enough for targeted retrieval |
| Overlap | 100 chars | Preserves sentence continuity at boundaries |
| Section header patterns | 5 regex patterns | Detects numbered headers (§3.4), bold headers, ALL-CAPS headings |
| Index target | Child chunks | Child is the retrieval unit |
| Context assembly | Parent chunks | Parent is passed to the LLM as context |

**Why hierarchical?** When an underwriter asks "what is the referral threshold for HAZMAT fleet operators?", retrieval needs to find the specific threshold (child chunk precision) but the LLM needs the surrounding policy section to answer accurately (parent context). Flat 600-char chunks produce answers without policy context; flat 2,500-char chunks waste context window space on irrelevant text.

---

## 7. Hybrid Search

The Retrieval Service routes queries between two search strategies based on the query pattern:

| Query type | Strategy | Example |
|:---|:---|:---|
| Reference ID lookup | Exact keyword (BM25) | "Show me account ACI-2024-0892" |
| Semantic / conceptual | ANN vector search | "What are the referral triggers for refrigerated fleets?" |
| Mixed | Hybrid (ANN + BM25) | Most production queries |

Reference ID patterns detected by regex: `ACI-`, `CLM-`, `SUB-`, `INS-`, `DRV-` prefixes trigger BM25 routing. All other queries use hybrid scoring.

---

## 8. Similarity Search Design

Historical learning ("what happened the last time we insured companies like this?") requires a dedicated similarity search architecture distinct from the document retrieval path.

### Approach: Hybrid Vector + Structured Filters

Pure vector similarity on unstructured text does not work for risk matching — two fleets can have similar document language but vastly different risk profiles. The Similarity Service uses a hybrid approach:

1. **Structured pre-filter**: Narrow candidates to accounts matching hard constraints (same state, same NAICS sector, fleet size within ±30%)
2. **Vector similarity**: Rank filtered candidates by embedding similarity on the structured risk profile
3. **Outcome enrichment**: Join matched accounts to `loss_runs` and `policies` tables to retrieve historical outcomes

### Similarity Fields

| Field | Source table | Weight | Notes |
|:---|:---|:---|:---|
| NAICS code (2-digit sector) | `insureds` | High | Same industry sector required |
| Fleet size band | `insureds` | High | Bands: 1–10, 11–25, 26–50, 51–100, 100+ |
| State | `insureds` | Medium | Same primary operating state |
| Commodity type | `insureds` | Medium | Dry van, refrigerated, flatbed, tanker, etc. |
| Years in operation | `insureds` | Low | Bands: <2, 2–5, 5–10, 10+ |
| Loss ratio band | `loss_ratios` | High | Bands: <50%, 50–75%, 75–100%, >100% |

### Embedding Strategy

The Similarity Service embeds the structured risk profile as a composite vector:

```python
# Pseudocode — actual implementation in 04_memory_and_rbac
profile_text = f"""
Industry: {naics_sector}
Fleet size: {fleet_size_band}
State: {state}
Commodity: {commodity_type}
Years: {years_band}
Loss ratio: {loss_ratio_band}
"""
embedding = embed(profile_text)  # Same embedding model as document retrieval
```

### Matching Threshold

Default similarity threshold: **0.75** (configurable in `company_config.yaml`)

Matches below threshold are excluded from results. The UI displays the top 10 matches sorted by similarity score, with loss ratio and outcome for each.

### Data Source

Similarity search runs against the `historical_cohorts` table — a curated snapshot of historical accounts prepared and validated by the actuarial team. This is not a live query against `insureds`; the cohort table is refreshed quarterly or after significant portfolio changes.

---

## 9. Pricing Intelligence Service (v3)

Underwriting is not just knowledge retrieval — it also involves pricing. The Pricing Intelligence Service is a planned v3 capability that suggests premium bands based on historical data.

### Inputs

| Input | Source |
|:---|:---|
| Risk profile | Current submission (fleet size, commodity, state, NAICS) |
| Similar historical accounts | Similarity Service output |
| Historical premiums | `policies` table (premium field) |
| Historical loss ratios | `loss_ratios` table |
| Exposure factors | `insureds` table (unit count, radius, driver count) |

### Output

```
Suggested Premium Band:  $85,000 – $110,000
Confidence:              78%
Basis:                   23 similar accounts, median premium $94,500

Supporting Evidence:
- Similar fleet size (38–45 units): median premium $92,000
- Same commodity class (refrigerated): +8% vs dry van
- Loss ratio > 80%: historically priced 15–20% above segment median

Comparable Accounts:
  Coastal Cold Chain   │ 38 u. │ $91,000 │ 71% LR │ Renewed
  Pacific Freight      │ 41 u. │ $98,000 │ 68% LR │ Renewed
  Western Reefer       │ 45 u. │ $88,000 │ 94% LR │ Non-renewed
```

### Design Constraints

* **Advisory only**: Pricing suggestions are informational; they do not auto-populate quote systems
* **Explainability required**: Every band must cite the comparable accounts and factors that produced it
* **Confidence thresholds**: Suggestions below 60% confidence are not displayed
* **Audit trail**: All pricing suggestions logged to `pricing_suggestions` table for model governance

This service is not implemented in v1 or v2. It is included here to signal that the architecture supports pricing intelligence as a natural extension.

---

## 10. Guardrail Pipeline

Five validators run on every LLM response before delivery. Applied in priority order — a BLOCK at step 1 terminates the pipeline immediately.

| Priority | Guardrail | What triggers it | Action |
|:---|:---|:---|:---|
| 1 | Binding Opinion Blocker | Response attempts to bind, approve, or decline a risk | BLOCK — replaced with standard redirect |
| 2 | Prohibited Topic Filter | Competitor pricing, legal advice, employment advice, regulatory violation | BLOCK |
| 3 | PII Redactor | SSNs, CDL numbers, DOBs, phone numbers detected in response | REDACT patterns + DELIVER |
| 4 | Coverage Disclaimer | Response interprets policy coverage terms | APPEND standard disclaimer |
| 5 | Citation Enforcer | Factual claims present without a source citation | APPEND reminder to check source |

Guardrail trigger rates are monitored in MLflow. A sustained rise in any guardrail rate is an early signal of prompt drift, corpus contamination, or model version change.

---

## 11. Role-Based Access Control

Document access is enforced at the Vector Search query layer — not the application layer.

```python
# Applied in Retrieval Service — 04_memory_and_rbac
RBAC_POLICY = {
    "underwriter":        ["all"],
    "senior_underwriter": ["all"],
    "claims_adjuster":    ["Claims Procedures", "Claim Files", "Loss Runs",
                           "Regulatory & Compliance", "Product Guides"],
    "claims_director":    ["Claims Procedures", "Claim Files", "Loss Runs",
                           "Regulatory & Compliance", "Meeting Minutes"],
    "broker":             ["Product Guides", "Underwriting Guidelines",
                           "Policy Documents"],
    "loss_control":       ["Fleet Inspections", "Loss Control Reports",
                           "Reference Materials"],
    "compliance_officer": ["Regulatory & Compliance", "Policy Documents",
                           "Claims Procedures"],
    "executive":          ["all"],
}
```

**v1:** Role passed from UI dropdown.  
**v2:** Role resolved from Databricks group membership via SCIM. UI dropdown replaced by read-only role display.

---

## 12. Session Memory

```
Table: conversation_sessions
Columns: session_id, user_id, user_role, created_at, last_active,
         message_history (JSON array), compressed_summary (string)

MAX_MESSAGES_IN_WINDOW = 10
COMPRESSION_THRESHOLD  = 20   ← When history exceeds 20 exchanges,
                                 compress oldest 10 into a summary string
                                 and retain the most recent 10 verbatim
```

Sessions are scoped to browser tab via `session_id` generated at app load. Session history is preserved in Delta and available on re-open if the same `session_id` is passed.

---

## 13. Feedback and Override Tables

```
Table: copilot_feedback
Columns: feedback_id, session_id, query, response, rating (1/-1),
         comment, user_id, user_role, timestamp

Table: feedback_overrides
Columns: override_id, submission_id, ai_recommendation, uw_decision,
         override_reason, override_reason_text, user_id, user_role,
         timestamp, exported_to_eval (boolean)
```

The Evaluation Service exports `rating = -1` rows from `copilot_feedback` and all rows from `feedback_overrides` to the curated eval dataset weekly. Override rows are higher-weight examples — they represent real underwriting decisions, not chat quality ratings.

---

## 14. AI Observability

Production AI requires operational monitoring beyond offline evaluation. The following metrics are tracked continuously and surfaced in a Databricks dashboard.

### Latency Metrics

| Metric | Source | Target | Alert threshold |
|:---|:---|:---|:---|
| End-to-end response time (p95) | Model Serving logs | < 5 sec | > 8 sec |
| Time to first token (p95) | Model Serving logs | < 2 sec | > 4 sec |
| Retrieval latency (p95) | VS query timing | < 500 ms | > 1 sec |
| Guardrail processing time | Governance Service logs | < 200 ms | > 500 ms |

### Quality Metrics

| Metric | Source | Target | Alert threshold |
|:---|:---|:---|:---|
| Citation coverage | Evaluation Service (sampled) | > 95% | < 90% |
| Hallucination rate | Evaluation Service (sampled) | < 2% | > 5% |
| Retrieval precision | Evaluation Service (sampled) | > 90% | < 85% |
| User satisfaction (thumbs up %) | `copilot_feedback` table | > 90% | < 80% |

### Operational Metrics

| Metric | Source | Target | Alert threshold |
|:---|:---|:---|:---|
| Guardrail trigger rate (any) | Governance Service logs | < 10% | > 20% |
| Binding Opinion blocks | Guardrail #1 logs | < 1% | > 3% |
| Override rate | `feedback_overrides` table | Monitored | Rising trend |
| Vector hit rate | VS results metadata | > 80% | < 70% |

### Cost Metrics

| Metric | Source | Tracking |
|:---|:---|:---|
| Tokens per conversation (avg) | Model Serving logs | Daily aggregate |
| Cost per conversation (avg) | Billing API + token counts | Daily aggregate |
| VS queries per day | VS endpoint metrics | Daily aggregate |
| Serving endpoint utilisation | Model Serving metrics | Hourly |

### Model Drift Detection

Weekly automated evaluation runs compare current model performance against the baseline established at deployment. A degradation of > 5% on any quality metric triggers an alert for human review.

Drift signals:
* Citation accuracy dropping
* Hallucination rate rising
* Retrieval precision declining
* Guardrail trigger rates increasing

---

## 15. Operational Model

### Five Automated Jobs (DAB Bundle)

| Job | Trigger | Purpose |
|:---|:---|:---|
| `{prefix}-pipeline-setup` | Manual — once on day 1 | Schema creation, VS index build, chain deploy, app deploy, baseline eval |
| `{prefix}-intake` | Every 15 min | Auto Loader — new S3 files → parsed → chunked → indexed |
| `{prefix}-infra-start` | 8 AM weekdays | Recreates VS endpoint + index from Delta; recreates serving endpoint |
| `{prefix}-infra-stop` | 8 PM weekdays | Deletes VS endpoint; pauses serving endpoint |
| `{prefix}-app-deploy` | Manual — after app changes | Redeploys Databricks App only |

### Cost Management

| Resource | Billing model | Strategy |
|:---|:---|:---|
| Vector Search endpoint | Hourly when online | Stopped 8 PM – 8 AM weekdays; off weekends |
| VS index re-sync | Billable compute (~20 min) | Runs automatically on infra-start |
| Model Serving endpoint | Hourly when provisioned | Stopped 8 PM – 8 AM weekdays |
| Databricks App | Usage only | Scales to zero — no stop job needed |
| Intake job cluster | Per-run (serverless) | Short-lived; exits after backlog clears |

**Note:** VS index re-sync takes ~20 minutes after infra-start — CoPilot is unavailable during this window. Consider starting infra at 7:40 AM to be ready by 8:00 AM, or keep the index online and pause only the serving endpoint.

---

## 16. Pipeline Stage Reference

| Stage | File | Source component |
|:---|:---|:---|
| `00_config.py` | Loads YAML, derives all resource names, sets Spark conf | `rag_pipeline/00_config` |
| `01_ingest_batch` | Bulk-ingests historical PDFs from `sample_data/` or S3 | `01_ingest_and_parse` |
| `01b_ingest_stream` | Auto Loader — ongoing S3 intake, scheduled every 15 min | NEW |
| `02_chunk_and_index` | HierarchicalChunker → `document_chunks` → VS index build | `07_hierarchical_chunking` + `02_prepare_vector_index` |
| `03_rag_chain` | `UWCopilotAgent` — hybrid search, intent router, LLM chain | `03_rag_chain` + `01_hybrid_search` |
| `04_memory_and_rbac` | SessionManager, RBAC filter at query time | `02_conversation_memory` + `03_rbac_retrieval` |
| `05_structured_data` | NL-to-SQL intent router, SCHEMA_CONTEXT assembly | `04_structured_data_integration` |
| `06_guardrails` | GuardrailPipeline — 5 validators in priority order | `05_guardrails` |
| `07_evaluate` | LLM judge scoring, MLflow logging | `04_evaluate` |
| `08_feedback_loop` | FeedbackManager, `copilot_feedback`, `feedback_overrides` | `06_feedback_loop` |
| `09_deploy` | UC model registration, serving endpoint creation, app deploy | `05_deploy_v3` |
| `uw_copilot_agent.py` | MLflow code artifact — `UWCopilotAgent` class | `atlas_rag_agent.py` (renamed) |

---

## 17. Delta Tables Inventory

### Pipeline Tables

| Table | Description | Key columns |
|:---|:---|:---|
| `parsed_documents` | One row per source PDF after ai_parse_document() | doc_id, source_path, category_label, parsed_text, page_count, ingested_at |
| `document_chunks` | One row per chunk — source for VS index | chunk_id, doc_id, chunk_text, chunk_type (parent/child), parent_chunk_id, category_label |
| `conversation_sessions` | Session memory for the Conversation Service | session_id, user_id, user_role, message_history (JSON), compressed_summary |
| `copilot_feedback` | Thumbs up/down from the Workbench | feedback_id, session_id, query, response, rating, user_id, timestamp |
| `feedback_overrides` | Underwriter decision overrides | override_id, submission_id, ai_recommendation, uw_decision, override_reason, exported_to_eval |
| `submission_summaries` | Auto-generated summaries on intake (v2) | summary_id, submission_id, risk_indicators (JSON), assessment, confidence, generated_at |
| `historical_cohorts` | Curated historical accounts for similarity matching | cohort_id, insured_id, profile_embedding, naics_sector, fleet_band, state, commodity, loss_ratio_band |
| `pricing_suggestions` | Pricing band suggestions audit trail (v3) | suggestion_id, submission_id, suggested_band, confidence, comparable_accounts (JSON), timestamp |

### Operational Tables — Atlas Reference

| Table | Description |
|:---|:---|
| `insureds` | Named insureds — fleet operators, business details |
| `drivers` | Driver roster — CDL, violations, CSA BASIC scores |
| `policies` | Policy records — effective/expiry dates, coverages, premiums |
| `claims` | Claims records — incident date, amounts, status |
| `loss_runs` | Loss run summaries — 3-year loss ratios by account |
| `submissions` | Submission tracking — broker, received date, status, assigned UW |
| `loss_ratios` | Computed annual loss ratios — used by the Analytics Service |
| `referrals` | Referral history — trigger, decision, outcome |

---

## 18. Configuration Model

### Naming Convention

```
company.short_name  +  company.domain  →  {short_name}_{domain}

atlas  +  insurance  →  atlas_insurance

  Catalog:    atlas
  Schema:     atlas_insurance_rag
  VS EP:      atlas_insurance_vs_endpoint
  Serving EP: atlas_insurance_rag_endpoint
  App:        atlas_insurance_uw_copilot_app
  UC Model:   atlas.atlas_insurance_rag.uw_copilot_rag_model
```

### `company_config.yaml` — Key Fields

```yaml
company:
  name:        "Atlas Commercial Insurance"
  short_name:  "atlas"           # ← drives all resource names
  domain:      "insurance"       # ← drives all resource names

catalog:       "atlas"

intake:
  s3_path:     "s3://atlas-submissions/"  # ← replaces all hardcoded paths
  schedule:    "*/15 * * * *"

models:
  chat:        "databricks-claude-sonnet-4"
  embedding:   "databricks-gte-large-en"

chunking:
  parent_size: 2500
  child_size:  600
  overlap:     100

similarity:
  threshold:   0.75              # ← minimum similarity score for historical matching
  max_results: 10

doc_categories:
  - id:    "01_uw_guidelines"
    label: "Underwriting Guidelines"
  - id:    "02_policy_docs"
    label: "Policy Documents"
  # ... (one entry per S3 subfolder)

rbac:
  underwriter:        ["all"]
  broker:             ["Product Guides", "Underwriting Guidelines", "Policy Documents"]
  # ... (one entry per role)
```

### Three Files Companies Edit

| File | What to change |
|:---|:---|
| `config/company_config.yaml` | Company identity, catalog, S3 path, categories, RBAC, model endpoints, chunking, similarity threshold |
| `prompts/system_prompt.md` | AI persona, brand name, domain-specific compliance rules |
| S3 bucket | Drop PDFs into subfolders matching the `id` fields in `doc_categories` |

---

## 19. Platform Portability

Core architectural concepts — retrieval-augmented generation, multi-turn conversation, role-based document access, guardrail pipelines, LLM evaluation, and feedback loops — are platform-independent patterns.

Databricks provides the reference implementation. Organizations on other platforms can adapt the design using equivalent services:

| This design | Equivalent on other platforms |
|:---|:---|
| Databricks Vector Search | Pinecone, Weaviate, Elasticsearch kNN, Azure AI Search |
| Delta Lake | Apache Iceberg, Apache Hudi, cloud object storage + Parquet |
| Unity Catalog | AWS Lake Formation, Azure Purview, GCP Dataplex |
| MLflow | Weights & Biases, Neptune, Kubeflow, SageMaker |
| Databricks Apps | Streamlit Cloud, Vercel, AWS App Runner |
| Model Serving | SageMaker Endpoints, Azure ML, Vertex AI |

The architectural principles — separation of retrieval and generation, guardrail pipelines, structured feedback capture, explainability requirements — outlast any specific technology stack.

---

## 20. Known Bugs — Fix Before Template Release

| # | Bug | Location | Fix |
|:---|:---|:---|:---|
| 1 | `infra_start` and `infra_stop` hardcode endpoint names, diverging from `00_config` | `infra_start`, `infra_stop` | Replace with `%run ./rag_pipeline/00_config` and use derived names |
| 2 | `SOURCE_PDF_PATH` in `00_config` is a hardcoded workspace path | `00_config` | Replace with `config.intake.s3_path` loaded from `company_config.yaml` |
| 3 | Class `AtlasInsuranceRAGAgent` is Atlas-specific | `atlas_rag_agent.py` | Rename file to `uw_copilot_agent.py`, class to `UWCopilotAgent` |
| 4 | `databricks-vectorsearch` package deprecated | `requirements.txt`, notebook installs | Replace with `databricks-ai-search` |
| 5 | Duplicate deploy notebooks: `05_deploy_v3` and proposed `09_deploy` | `rag_pipeline/` | Consolidate into `09_deploy` |

---

## 21. Deployment Setup Flow

1. **Admin: S3 External Location** — register the S3 submission bucket as a UC External Location (one-time; requires workspace admin)
2. **Edit config** — update `config/company_config.yaml` with company identity, catalog, and S3 path
3. **Edit prompt** — update `prompts/system_prompt.md` with company name and any domain-specific rules
4. **Deploy bundle** — `databricks bundle deploy` (creates all 5 jobs from `resources/jobs.yml`)
5. **Run setup job** — trigger `{prefix}-pipeline-setup` manually (schema creation, batch ingest, index build, chain deploy, app deploy, baseline eval)
6. **Verify** — open the Databricks App URL; run the smoke-test question set from `07_evaluate`

---

## 22. Open Decisions

| # | Decision | Options | Recommendation |
|:---|:---|:---|:---|
| 1 | Role resolution | (a) UI dropdown — v1, (b) Databricks group / SCIM — v2 | Ship (a); `user_role` must be a first-class API field from day one |
| 2 | Workbench in v1 | (a) Chat-first (current code), (b) Workbench-first with chat companion | (b) is the right product — build queue view before v1 ships |
| 3 | Submission Summary trigger | (a) Inline in Auto Loader job, (b) Separate async summary job | (b) — keeps ingestion fast; summary writes to `submission_summaries` async |
| 4 | Historical learning data | (a) Existing `loss_runs` + `policies` tables, (b) Dedicated `historical_cohorts` table | (b) for v2 — structured for vector similarity, not just lookup |
| 5 | Intake latency | (a) Every 15 min scheduled, (b) S3 Event → SNS → Jobs API trigger | (a) for v1; (b) when <5 min latency required |
| 6 | Atlas PDFs storage | (a) In `sample_data/` in repo, (b) Public S3, downloaded at setup | (b) — keeps repo lightweight; (a) acceptable if repo is private |
| 7 | Explainability format | (a) Prompt-engineered into LLM prose response, (b) Structured JSON output | (b) for v2 — structured output is parseable by the Workbench UI |
| 8 | Infra availability window | 20-min gap on infra-start while VS index re-syncs | Start infra at 7:40 AM; or keep index online and pause serving endpoint only |
| 9 | Pricing Intelligence | (a) In-scope for v2, (b) Deferred to v3 | (b) — v2 focuses on historical learning; pricing requires actuarial validation |

---

## Appendix A — Reference Implementation: Atlas Commercial Insurance

Atlas ships as `sample_data/atlas_commercial_insurance/` in the repo. Companies fork the template, run the setup job on Atlas data, interact with a working CoPilot, then swap in their own config and S3 bucket.

### Atlas Corpus

| Category | S3 subfolder | Documents |
|:---|:---|:---|
| Submissions | `07_submissions/` | 251 |
| Email Correspondence | `12_emails/` | 301 |
| Underwriter Notes | `13_uw_notes/` | 301 |
| Policy Documents | `02_policy_docs/` | 101 |
| Fleet Inspections | `06_fleet_inspections/` | 101 |
| Meeting Minutes | `14_meeting_minutes/` | 101 |
| Loss Runs | `08_loss_runs/` | 151 |
| Claim Files | `09_claim_files/` | 76 |
| Loss Control Reports | `05_loss_control/` | 76 |
| Claims Procedures | `04_claims_procedures/` | 12 |
| Product Guides | `03_product_guides/` | 11 |
| Regulatory & Compliance | `10_regulatory/` | 9 |
| Underwriting Guidelines | `01_uw_guidelines/` | 6 |
| Authority & Limits | `11_authority/` | 3 |
| Reference Materials | `15_reference/` | 2 |
| **Total** | | **1,502 PDFs — 2,268 chunks** |

### Live Atlas Infrastructure

| Resource | Value |
|:---|:---|
| Catalog | `atlas` |
| Schema | `atlas_insurance_rag` |
| VS endpoint | `atlas_insurance_vs_endpoint` |
| Serving endpoint | `atlas_insurance_rag_endpoint` (model v5, Claude Sonnet 4) |
| Databricks App | `atlas_insurance_uw_copilot_app` |
| Infra schedule | Start 8 AM ET weekdays / Stop 8 PM ET weekdays |

---

## Appendix B — Insurance Components and Terminology in Underwriting Journey Order

This appendix explains the key insurance concepts referenced throughout the architecture, ordered the way an underwriter actually experiences them in the submission lifecycle.

### 1. Submission Arrival and Intake

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Submission | A broker's package requesting a quote for a prospective insured | It is the primary unit of work in the Workbench queue |
| Broker | The intermediary representing the insured to the carrier | Broker emails, documents, and questions are part of the intake corpus |
| Insured | The company or person seeking insurance coverage | The core entity being evaluated for risk and pricing |
| ACORD form | Standard insurance application form used to submit structured applicant information | Often the first structured source for exposures, operations, and requested coverages |
| Loss runs | Historical claims summary for the insured, usually 3–5 years | Critical evidence for risk selection, pricing, and referral decisions |
| MVR | Motor Vehicle Report for a driver | Used to assess driver quality, prior violations, and referral triggers |
| Driver schedule | List of drivers included in the submission | Needed to evaluate driver experience, count, and MVR completeness |
| Vehicle schedule | List of vehicles/equipment to be insured | Used to assess fleet size, equipment type, age, and exposures |

### 2. Submission Triage and Completeness Review

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Triage | Initial sorting and prioritisation of incoming submissions | The Workbench ranks and flags submissions before detailed review |
| Submission summary | One-page AI-generated brief of the risk, missing items, and recommendation | Reduces time spent manually reading every document from scratch |
| Completeness check | Review of whether required documents and fields are present | Missing MVRs, loss runs, or schedules often prevent quote progression |
| Risk indicator | A specific factor that increases or decreases underwriting concern | Surfaced directly in the Summary Panel with evidence |
| Confidence score | AI estimate of how strongly the system supports a recommendation | Helps the underwriter judge whether to trust or challenge the recommendation |
| Open question | Missing information that must be clarified with the broker | Drives follow-up requests and underwriter workflow |

### 3. Risk Review and Appetite Evaluation

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Risk appetite | The types of business the carrier wants to write, avoid, or limit | Central to referral prediction and recommendation logic |
| Appetite match | The degree to which a submission aligns with the carrier's desired risk profile | Future v2 capability for proactive decision support |
| Hazard | A characteristic that increases likelihood or severity of loss | Used in summaries, explanations, and referral logic |
| Operating radius | Geographic scope of fleet operation (local, intermediate, long-haul) | Often changes loss exposure and underwriting appetite |
| Commodity | What the fleet is hauling | A key determinant of severity exposure and pricing |
| CSA BASIC score | FMCSA safety metric for motor carriers | Used as a structured risk signal for trucking underwriting |
| Referral trigger | Condition that requires escalation beyond the underwriter's local authority | The CoPilot highlights these proactively |
| Underwriter notes | Prior internal observations or commentary on the account | Valuable internal context beyond formal documents |

### 4. Historical Context and Comparative Risk Review

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Historical learning | Using prior accounts and outcomes to inform current underwriting | Distinguishes the platform from simple document Q&A |
| Similar risk | A prior insured with comparable industry, fleet size, state, commodity, and loss characteristics | Used by the Similarity Service to ground recommendations |
| Cohort | A grouped set of comparable historical accounts | Forms the basis for similarity matching and pricing evidence |
| Loss ratio | Incurred losses divided by earned premium | One of the strongest indicators of account profitability |
| Renewal outcome | Whether the account renewed, non-renewed, or was declined later | Provides practical evidence about portfolio behavior |
| Book of business | The carrier's portfolio of written policies | Historical learning and future portfolio intelligence operate at this level |

### 5. Pricing and Quotation

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Premium | Price charged for insurance coverage | Core output of the future Pricing Intelligence Service |
| Suggested pricing band | AI-recommended premium range rather than a single point estimate | More realistic and defensible than a false-precision number |
| Rate adequacy | Whether premium is sufficient for expected risk and expenses | Key pricing question for underwriting and actuarial review |
| Exposure basis | Unit used to measure risk for pricing, such as vehicles, payroll, or sales | Helps normalize premium comparisons across similar accounts |
| Pricing indication | A directional recommendation for where premium should land | Advisory input, not an automated quote |
| Quote | Formal offer of insurance terms and price to the broker | One of the downstream actions after underwriting review |

### 6. Referral, Authority, and Decisioning

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Underwriting authority | Limits within which an underwriter may approve, decline, or modify terms | AI can recommend, but authority remains human-controlled |
| Referral | Escalation of a submission to a more senior underwriter or specialist | Captured as a structured Workbench state and recommendation |
| Escalation | Broader routing to a specialist, manager, or alternate workflow | Often triggered by authority limits, hazardous classes, or poor experience |
| Approve | Underwriter determines the account can proceed to quote | The system may recommend approval but cannot execute it |
| Decline | Underwriter determines the risk should not be offered terms | Requires clear reasoning and remains a human action |
| Bind | Formal acceptance of the risk and activation of coverage | Explicitly out of scope for AI automation |

### 7. Policy Issuance and Ongoing Relationship

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Policy | The formal insurance contract once coverage is bound | Stored in operational data and referenced in future servicing workflows |
| Coverage | Specific protection granted under the policy | Responses about coverage require disclaimers and careful citation |
| Endorsement | Mid-term change to policy terms, exposures, or limits | Future servicing use case for the same platform |
| Renewal | Re-underwriting an existing account for the next policy term | A major future AI workflow beyond new business submissions |
| Retention | Keeping an account on the book at renewal | Future Portfolio Intelligence capability |
| Non-renewal | Decision not to continue the account at renewal | Useful as a historical outcome in Similarity and Portfolio Intelligence |

### 8. Claims, Loss Experience, and Feedback Signals

| Term | Meaning | Why it matters in the CoPilot |
|:---|:---|:---|
| Claim | Notice of loss under a policy | Claims history is central to underwriting decisions |
| Claim severity | Financial magnitude of an individual claim | Helps explain poor loss experience |
| Claim frequency | How often claims occur for an account or segment | Strong indicator of future risk quality |
| Loss control report | Inspection or engineering report about safety practices and hazards | Frequently changes underwriting view beyond raw loss data |
| Override | Human change to the AI recommendation | The highest-value learning signal in the system |
| Feedback loop | Process of capturing thumbs up/down and overrides into evaluation data | Enables continuous improvement without autonomous decisioning |

### 9. Roles Across the Journey

| Role | Primary responsibility in the UW journey | Relevance to platform design |
|:---|:---|:---|
| Broker | Packages submission, answers follow-up questions, receives quote | Drives intake documents and broker-facing follow-up workflow |
| Underwriter | Reviews risk, requests missing info, recommends price/terms | Primary end user of the Workbench |
| Senior Underwriter | Reviews referrals and exceptions | Receives escalated submissions flagged by AI |
| Actuary | Validates pricing logic and similarity cohorts | Governs pricing intelligence and historical learning methodology |
| Compliance Officer | Ensures rules, disclosures, and governance controls are followed | Owns regulatory confidence in the AI system |
| Claims / Loss Control teams | Provide loss and inspection data that shape risk evaluation | Important secondary data producers for the platform |

### 10. How These Terms Map to the UW CoPilot Architecture

| Journey stage | Primary architecture components |
|:---|:---|
| Submission arrival | Ingestion Service, S3 intake, Auto Loader |
| Completeness and triage | Workbench Queue, Submission Summary, Similarity Service |
| Risk and appetite review | Retrieval Service, Analytics Service, Similarity Service |
| Pricing support | Pricing Intelligence Service (v3), historical cohorts, policies/loss ratios |
| Referral and decision support | Workbench actions, Explainability, Guardrails, Override Capture |
| Ongoing learning | Evaluation Service, AI Observability, feedback and override tables |

---

*For project file structure and repository layout, see the GitHub repository README.*

*End of Technical Architecture & Engineering Design. Version 3.1*  
*Companion: UW_COPILOT_TEMPLATE_SPEC.md (Executive Architecture)*
