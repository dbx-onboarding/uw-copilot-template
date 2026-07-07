# UW CoPilot — Executive Architecture

| | |
|:---|:---|
| **Version** | 6.0 |
| **Status** | Draft — for review by technical and business stakeholders |
| **Author** | Solution Architecture |
| **Reference Implementation** | Atlas Commercial Insurance |
| **Platform** | Databricks on AWS |
| **Companion document** | UW_COPILOT_TECHNICAL_DESIGN.md |

---

> **An AI-powered underwriting intelligence platform that helps underwriters spend more time making decisions and less time searching for information.**

---

> This is not another enterprise chatbot. It is an AI-powered underwriting intelligence layer that combines institutional knowledge, operational data, and historical outcomes to support consistent, explainable underwriting decisions — at scale.

---

## Part I — The Business Case

---

## 1. A Day in the Life

*Before the CoPilot, this is a typical underwriter's morning.*

Seventeen new submissions in the queue. Each one is a folder of PDFs — ACORD forms, loss runs, driver schedules, broker emails. The underwriter opens the first file. Twenty minutes later they are still reading. They have not written a single note.

*With the CoPilot, the same morning looks like this.*

**8:05 AM** — 17 submissions arrive in S3.
The intake pipeline runs automatically. Within minutes, every PDF is parsed, indexed, and summarised.

**8:20 AM** — The underwriter opens the Workbench.
All 17 submissions are ranked by AI risk score. Four are flagged as referrals. Three have missing documents. Two have loss ratios that exceed appetite.

**8:25 AM** — They click ABC Trucking (AI Score: 92 / High Risk).
The submission summary is already there — fleet profile, loss history, missing documents, referral reasons, and a comparison to similar historical accounts.

The underwriter reads the summary, adds a note, escalates. Two minutes instead of twenty.

**Later that morning** — All 17 submissions have been reviewed.
In pilot deployments, routine review work that previously filled most of the week can often be completed substantially faster. Actual results depend on submission complexity, corpus quality, and how deeply underwriters integrate the tool into their workflow.

---

## 2. Business Problem

| Underwriter pain point | Impact |
|:---|:---|
| Searching across PDFs to answer a single question | 20–30 min per lookup |
| Re-reading the same guidelines for every new submission | Inconsistent decisions across underwriters |
| Cross-referencing loss data, MVR scores, and documents manually | Errors from context switching |
| No memory across conversation turns | Friction and repeated context |
| New underwriter ramp-up | 6 months to learn guidelines and appetite |
| Submission summaries written from scratch | 1–2 hours per submission |
| No access to historical outcomes for similar risks | Decisions based on instinct, not data |

---

## 3. Business Value

Target outcomes based on comparable AI-assisted underwriting deployments. Figures are directional — actual results depend on corpus quality, user adoption, and workflow integration.

| Metric | Before | Target with CoPilot | Change |
|:---|:---|:---|:---|
| Submission review time | 2–3 hours | 20–30 minutes | ~85% reduction |
| Document search time | 20–30 min | < 30 seconds | ~98% reduction |
| New underwriter ramp-up | 6 months | 6 weeks | ~75% faster |
| Daily submission capacity | ~40/day | ~90/day | ~2x throughput |
| Guideline consistency | Variable | Citation-enforced | Standardised |
| Time to index new submission | Manual, hours/days | Automatic, 5–20 min | Near real-time |

---

## Part II — The Product

---

## 4. What This Is — And What It Isn't

### v1 — Knowledge Assistant

v1 is an **AI-powered knowledge assistant**. It retrieves, synthesises, and explains information from documents and operational data. It does not autonomously underwrite.

It answers questions like:
- *"What does our UW manual say about HAZMAT operations?"*
- *"What is Lone Star's loss ratio over the last 3 years?"*
- *"Show me the referral triggers for fleets with CSA BASIC scores above 65."*
- *"What documents are missing from this submission?"*

### What a full UW CoPilot becomes

| Capability | Description |
|:---|:---|
| Submission summary | Auto-generated risk brief the moment a submission lands |
| Completeness check | Flags missing documents before the underwriter opens the file |
| Appetite matching | Compares submission against risk appetite, returns a fit score |
| Referral prediction | Predicts likely referral triggers before manual review |
| Historical learning | Finds similar historical accounts and their outcomes |
| Loss trend prediction | Projects future loss ratios from historical patterns |
| Pricing indication | Suggests premium range based on risk profile |
| Explainability | Every recommendation answers "why?" with cited evidence |
| Override learning | Captures decision overrides as high-value training signals |

**v1 is Phase 1.** Each capability above layers on top without requiring a rebuild.

---

## 5. Competitive Positioning

| Capability | Generic LLM | Sixfold / Cooper AI | UW CoPilot |
|:---|:---|:---|:---|
| Document Q&A | Yes | Yes | Yes |
| Submission workflow | No | Partial | Yes — Workbench |
| Historical risk learning | No | No | Yes (v2) |
| Explainability with citations | No | Partial | Yes |
| Appetite scoring | No | No | Yes (v2) |
| RBAC by document category | No | No | Yes |
| Guardrails (binding opinions, PII) | No | Partial | Yes — 5 validators |
| Underwriting-specific design | No | Yes | Yes |
| Runs on your own infrastructure | No | No | Yes — Databricks |
| Configurable for your corpus | No | No | Yes — 3 files |
| Open source / forkable | No | No | Yes |

**Why not a generic LLM?** A generic LLM answers questions from its training data. It has no knowledge of your guidelines, your appetite, your loss history, or your customers. It cannot be restricted to specific document categories by role. It has no guardrails against binding opinions or PII exposure. And it cannot be governed, audited, or tuned to your specific underwriting context.

**Why not Sixfold or Cooper?** Both are strong products for document Q&A and multi-turn conversation. Neither offers a workbench-first submission workflow, historical risk matching against your own book, or appetite scoring. Both run on their own infrastructure — your data leaves your perimeter. This platform runs entirely within your Databricks environment, governed by Unity Catalog.

---

## 6. AI Limitations

Transparency about AI limitations increases — not decreases — executive confidence. The goal is not to oversell the capability.

### What the AI cannot do

| Limitation | Why it matters |
|:---|:---|
| Approve policies or bind coverage | All bind decisions require human underwriting authority |
| Decline risks on behalf of the company | AI recommendation; human decision required |
| Replace underwriting authority sign-off | Authority matrix is enforced by humans, not AI |
| Interpret legal regulations or provide legal advice | Compliance review is a human function |
| Override human decisions | The underwriter always has the final word |
| Guarantee factual accuracy | All cited answers should be verified against source |
| Access real-time external data (v1) | External data connectors are a v3 capability |
| Learn from individual sessions in real time | The base LLM updates through the evaluation cycle, not on the fly |

### Design safeguards

These limitations are enforced architecturally, not by convention:
- The Binding Opinion Blocker guardrail intercepts and blocks any response that attempts to approve, decline, or bind a risk before it reaches the user
- Every factual response includes source citations — the underwriter can verify the source document in one click
- Every recommendation includes a confidence score and explicit reasoning — the underwriter reviews evidence, not a black-box verdict
- All decisions are logged with the underwriter's identity, not attributed to the AI

---

## 7. The Underwriter Workbench

The CoPilot is not chat-first. It is **workbench-first** — a structured queue where submissions are ranked, scored, and summarised before the underwriter touches them. Chat is the companion, not the entry point.

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  ATLAS UW COPILOT  ·  Maria Chen, Sr Underwriter  ·  Monday Jul 7  ·  17 pending    │
├──────────────────────┬───────────────────────────────────┬──────────────────────────┤
│  TODAY'S QUEUE       │  SUBMISSION SUMMARY               │  CHAT                    │
│                      │                                   │                          │
│  ● ABC Trucking   92 │  ABC Trucking Co.   SUB-001       │  Ask about this          │
│  ○ Blue Ridge     88 │  Score: 92  ·  High  ·  Refer     │  submission...           │
│  ○ Pacific Coast  76 │  ─────────────────────────────    │                          │
│  ○ Lone Star      44 │  Fleet: 38 units, dry van         │  ──────────────────────  │
│  ○ Arrow Transit  71 │  Loss Ratio: 91% (limit 75%)      │                          │
│  ○ Summit Haul    55 │  Missing: MVR reports (4 drvrs)   │  HISTORICAL RISKS        │
│  ─────────────────── │  ─────────────────────────────    │                          │
│  Filters             │  Risk Indicators                  │  23 similar accounts     │
│  ○ All  ● Referrals  │  ⚠ Loss ratio > appetite         │  Avg loss ratio: 78%     │
│  ○ Missing docs      │  ⚠ 2 drivers CSA score > 65      │  Non-renewal >80%: 71%   │
│  ○ High risk         │  ✅ Fleet age within appetite      │                          │
│                      │  ✅ Safety program documented      │  ──────────────────────  │
│                      │  ─────────────────────────────    │                          │
│                      │  Assessment:  REFER  ·  88%       │  EVIDENCE                │
│                      │                                   │                          │
│                      │  [Escalate]  [Approve]  [Decline] │  UW Manual §3.4          │
│                      │                                   │  Driver Qualif. §2.1     │
│                      │  Override reason (if changing):   │  Authority Matrix §1.2   │
│                      │  [__________________________]     │                          │
└──────────────────────┴───────────────────────────────────┴──────────────────────────┘
```

### Workbench States

| State | Meaning |
|:---|:---|
| New | Submission arrived, AI summary generated, not yet reviewed |
| Review | AI flagged for human attention (referral, missing docs, appetite concern) |
| In Progress | Underwriter has opened and is actively working |
| Escalated | Referred to senior underwriter or specialist |
| Approved | Underwriter approved to quote |
| Declined | Declined, reason recorded |

---

## 8. Submission Intelligence

Every time a new submission lands in S3, the system automatically generates a structured summary. The underwriter sees the completed risk brief — before they open a single PDF.

```
┌──────────────────────────────────────────────────────────────────┐
│  SUBMISSION SUMMARY — Auto-generated on intake                   │
│  SUB-26-11099  │  Pacific Coast Carriers  │  2026-07-01 08:14    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Insured          Pacific Coast Carriers Inc                     │
│  Fleet Size       42 units — long-haul refrigerated              │
│  Primary Hazard   Refrigerated cargo, interstate  CA/OR/WA/NV    │
│                                                                  │
│  Loss History     3-year loss ratio: 87%  (appetite limit: 75%)  │
│                   2 large losses > $100K in last 24 months       │
│                                                                  │
│  Document Status                                                 │
│  ✅ ACORD 125        ✅ Loss runs (3yr)    ✅ Driver schedule     │
│  ❌ MVR reports      ❌ Vehicle schedule   ⚠️  Financials (>2yr)  │
│                                                                  │
│  Risk Indicators                                                 │
│  ⚠️  Loss ratio exceeds appetite  (87% vs 75% limit)             │
│  ⚠️  2 drivers with MVR points > 5 (per driver schedule)         │
│  ✅ Fleet age within appetite (avg 4.2 yrs)                      │
│  ✅ Safety program documented                                     │
│                                                                  │
│  Initial Assessment    REFER to Senior Underwriter               │
│  Confidence            88%                                       │
│                                                                  │
│  Reasons for Referral                                            │
│  1. Loss ratio exceeds appetite — UW Manual §3.4                 │
│  2. MVR points above threshold — Driver Qualification §2.1       │
│  3. Missing MVR reports — Authority Matrix §1.2                  │
│                                                                  │
│  Suggested Next Steps                                            │
│  Request MVR reports for all drivers                             │
│  Request updated vehicle schedule                                │
│  Obtain loss control report for large loss Nov 2024              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. Historical Learning

Most copilots answer "what does the manual say?"

This one answers "what happened the last time we insured companies like this?"

Historical outcomes are the most valuable signal an underwriter has. The CoPilot makes that signal accessible on every submission.

```
Query: "Similar fleets to Pacific Coast Carriers — 42 units, refrigerated, CA-OR-WA"

23 comparable historical accounts found:

┌─────────────────────────┬────────┬────────────┬──────────────────┐
│  Account                │ Fleet  │ Loss Ratio │ Outcome          │
├─────────────────────────┼────────┼────────────┼──────────────────┤
│  Coastal Cold Chain     │ 38 u.  │    71%     │ Renewed — 3 yrs  │
│  Western Reefer Co.     │ 45 u.  │    94%     │ Non-renewed      │
│  Pacific Freight LLC    │ 41 u.  │    68%     │ Renewed — 2 yrs  │
│  Sierra Refrigerated    │ 39 u.  │    88%     │ Non-renewed      │
│  ...                    │  ...   │    ...     │ ...              │
├─────────────────────────┼────────┼────────────┼──────────────────┤
│  Segment average        │        │    78%     │                  │
│  Non-renewal rate >80%  │        │            │ 71%              │
└─────────────────────────┴────────┴────────────┴──────────────────┘

Accounts in this segment with loss ratios above 80% had a 71% non-renewal rate
within 2 policy periods. Pacific Coast at 87% sits in the high-risk cohort.
```

### Governance of Historical Learning

**How are "similar risks" defined?** Similarity is computed on structured risk profile fields — fleet size range, commodity class, operating radius, loss ratio band, and years in operation. It does not use PII, individual driver data, or geographic identifiers below the state level. The criteria are defined in `company_config.yaml` and are auditable.

**What algorithm is used?** Vector embedding similarity over the structured risk profile, matched against a dedicated `historical_cohorts` table seeded and maintained by the actuarial team. The matching threshold is configurable and defaults to 0.75.

**Who approves the similarity model?** The first deployment requires actuarial sign-off to validate that cohort criteria reflect company risk appetite. The criteria are human-readable YAML — not a black-box model — so actuaries can review and adjust directly.

**How do we prevent biased recommendations?** Historical outcomes reflect past decisions, which may contain historical bias. The system shows outcomes as observed data, not AI predictions. Matching explicitly excludes proxies for protected classes. The actuarial team reviews cohort composition before enabling the feature.

**How often does it need to be updated?** The `historical_cohorts` table refreshes on a configurable schedule — recommended quarterly or after a significant portfolio change.

---

## 10. Explainability

Every recommendation — referral, risk flag, completeness check, appetite score — must answer "why?" with cited evidence.

| Field | Example |
|:---|:---|
| Finding | "Loss ratio exceeds appetite" |
| Evidence | "87% 3-year loss ratio — source: loss_runs table, account INS-1002" |
| Rule | "UW Manual §3.4 — appetite limit 75% for long-haul fleets" |
| Confidence | 92% |
| Action | "Refer to senior underwriter" |

Every decision has a defensible audit trail. The underwriter validates reasoning rather than starting from scratch.

---

## 11. Underwriter Override Loop

Thumbs up/down captures sentiment. Underwriter overrides capture something more valuable: the cases where the AI and the human disagree — and why.

```
AI recommends:    Decline
                      ↓
Underwriter reviews:  Approved
                      ↓
Workbench prompts:    "What is the reason for this change?"

  ○ Established customer relationship
  ○ Risk characteristic not reflected in documents
  ○ Loss control plan in negotiation
  ○ Pricing adjustment planned
  ○ Other (free text)

                      ↓
Override captured → feedback_overrides Delta table
                      ↓
Weekly export → Evaluation Service (curated eval dataset)
                      ↓
Override patterns surfaced: "AI declined 14 accounts that underwriters
approved due to customer relationship — consider relationship tenure
as a context signal."
                      ↓
Continuous improvement without retraining the base LLM
```

Override patterns reveal systematic gaps in AI reasoning — through specific, labelled examples from real decisions. This is the highest-fidelity feedback signal the system collects.

---

## 12. AI Quality Standards

| Metric | Target | How measured |
|:---|:---|:---|
| Citation accuracy | > 95% | LLM judge: does the cited source actually support the answer? |
| Hallucination rate | < 2% | LLM judge: are all factual claims present in retrieved context? |
| Retrieval precision | > 90% | % of top-k retrieved chunks relevant to the question |
| User satisfaction | > 4.5 / 5 | Thumbs up/down ratio from Workbench feedback |
| Average response time | < 5 seconds | End-to-end from query submission to response delivery |
| Override rate | Monitored | Rising trend signals model drift |
| Guardrail trigger rate | Monitored | High rates indicate prompt or corpus issues |

Metrics are evaluated on every deployment (regression test), weekly (rolling sample of live queries), and on demand after corpus or prompt changes.

---

## Part III — The Architecture

---

## 13. Solution Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 4 — UNDERWRITING COPILOT                                     │
│                                                                     │
│  Workbench UI (Databricks App)    Submission Summary                │
│  Historical Learning              Explainability + Audit Trail      │
│  Role-based access                Override Learning Loop            │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 3 — AI WORKFORCE                                             │
│                                                                     │
│  Underwriter Assistant (v1)       Risk Assessment Agent (v2)        │
│  Document Agent (v2)              Appetite Agent (v2)               │
│  Compliance Agent (v3)            Pricing Agent (v3)                │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 2 — DATA FOUNDATION                                          │
│                                                                     │
│  Delta Lake (all tables)          Unity Catalog (governance)        │
│  Vector Search index              MLflow model registry             │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — PLATFORM                                                 │
│                                                                     │
│  Databricks on AWS                S3 (submission intake bucket)     │
│  Serverless compute               Databricks Apps (UI hosting)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 14. The AI Workforce

| Agent | Role | Phase |
|:---|:---|:---|
| **Underwriter Assistant** | Knowledge Q&A, document retrieval, citation | v1 ✅ |
| **Document Agent** | Extracts structured fields from PDFs — ACORD forms, limits, exposures | v2 |
| **Risk Assessment Agent** | Scores submissions against risk appetite, flags referral triggers | v2 |
| **Appetite Agent** | Matches submission profile against company appetite matrix | v2 |
| **Compliance Agent** | Checks regulatory requirements, jurisdiction rules, required documents | v3 |
| **Pricing Agent** | Suggests premium range from risk profile and historical outcomes | v3 |
| **Referral Agent** | Routes submissions to the right underwriter or team | v3 |
| **Intake Agent** | Monitors S3, classifies new files, triggers downstream agents | v2 |

In v1, only the Underwriter Assistant is active. In v2+, agents collaborate — Intake triggers Document, which feeds Risk Assessment, which routes to the Underwriter Assistant for final human review.

---

## 15. Phased Roadmap

```
Phase 1 — Knowledge Assistant                     v1 — this spec
  Underwriters ask questions in plain English.
  CoPilot retrieves and cites answers from documents + data.
  New submissions indexed automatically within 20 minutes.
  Guardrails prevent binding opinions, PII exposure, unsourced claims.

         ↓

Phase 2 — Decision Support                        v2
  Workbench-first UI: submission queue ranked by AI risk score.
  Auto-generated submission summaries on intake.
  Appetite scoring, completeness checks, referral prediction.
  Historical learning: similar risk lookup with outcomes.
  Explainability: every flag cites evidence + confidence score.
  Override loop: underwriter decisions captured as training signal.

         ↓

Phase 3 — Submission Automation                   v3
  Agentic intake: reads broker emails, extracts and classifies documents.
  Drafts broker correspondence and underwriting memos automatically.
  External data: D&B, catastrophe models, property data connectors.
  Routes submissions to the right underwriter based on risk type.

         ↓

Phase 4 — Autonomous Underwriter                  v4
  Full agent workforce: Intake → Document → Risk → Appetite → Pricing → Referral.
  Human underwriter reviews AI recommendation and approves or overrides.
  Full reasoning audit trail for compliance and model governance.
  Continuous learning from underwriter override history.

         ↓

Phase 5 — Portfolio Intelligence                  v5
  AI operates at the portfolio level, not the submission level.
  Portfolio mix recommendations: where the book is concentrated vs appetite.
  Book balancing: flag segments growing faster than loss performance warrants.
  Catastrophe exposure: aggregate modelled PML surfaced on renewal decisions.
  Renewal strategy: AI scores each renewal for retention priority vs pricing action.
  Loss trend prediction: forward-looking frequency and severity by segment.
  Appetite calibration: recommend appetite adjustments based on portfolio loss data.
```

---

## 16. Architecture Decisions

| Decision | Choice | Rationale |
|:---|:---|:---|
| Vector database | Databricks Vector Search | Native Delta Sync; same UC governance as all other data; no additional infrastructure |
| Index sync | Delta Sync (automatic) | New documents auto-picked up — no manual re-index triggers |
| UI framework | Streamlit on Databricks Apps | Ships in under a day; SSO included; no separate hosting or VPN |
| Agent framework | MLflow ChatAgent | Versioned, UC-registered, production-grade serving; same ML stack throughout |
| LLM | Claude Sonnet 4 | Best reasoning on long-context insurance documents; available natively on Databricks; no data leaves the workspace |
| Chunking | Hierarchical (parent/child) | Long UW manuals lose section context when split flat; child chunks are precise retrieval targets; parent provides the surrounding context |
| Intake | Auto Loader (`cloudFiles`) | Checkpoint-based incremental processing; handles S3 at any scale; no custom file-tracking logic needed |

---

## 17. Target Users

| Role | Primary use case | Document access |
|:---|:---|:---|
| Underwriter | Submission review, guideline questions, loss data queries | All categories |
| Senior Underwriter | Authority review, referral decisions | All categories |
| Claims Adjuster | Claims procedures, loss runs, regulatory guidance | Claims, Loss Runs, Regulatory, Product Guides |
| Claims Director | Portfolio-level review | Claims + management docs |
| Broker | Product and coverage questions | Product Guides, UW Guidelines (public), Policy Docs |
| Loss Control | Fleet inspections, loss control guidance | Fleet Inspections, Loss Control, Reference |
| Compliance Officer | Regulatory and policy review | Regulatory, Policies, Claims Procedures |
| Executive | Portfolio overview, AI quality metrics | All categories |

---

## 18. Cost Estimates

Rough estimates based on business-hours operation (weekdays 8 AM – 8 PM, infra off overnight and weekends).

| Environment | Description | Est. Monthly Cost |
|:---|:---|:---|
| Development | Single developer, limited hours, small corpus | ~$800 / month |
| Pilot | 1–2 underwriting teams, full corpus, normal usage | ~$3,000 / month |
| Production | 25+ users, full corpus, business hours operation | ~$12,000 / month |

Primary cost drivers: Vector Search endpoint, Model Serving endpoint, LLM API calls per token.
Primary cost levers: Infra start/stop schedule, serverless intake jobs, model selection for lower-traffic periods.

Full operational detail — jobs, configuration, deployment steps, and Delta table schema — is in the companion document: **UW_COPILOT_TECHNICAL_DESIGN.md**.

---

## Part IV — The Vision

---

## 19. Enterprise AI Platform

The UW CoPilot is the first application of a reusable enterprise AI platform. The architecture does not change between applications — only the domain knowledge, prompts, and workflows change.

```
Platform (unchanged across all applications)
  Databricks · Unity Catalog · Delta Lake · Vector Search · MLflow · Databricks Apps

       ↓ configure, don't rebuild ↓

┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│  Underwriting CoPilot   Claims Assistant   Loss Control Assistant │
│                                                                   │
│  Compliance Assistant   Broker Portal      Policy Servicing AI    │
│                                                                   │
│  Customer Service AI    Renewal Assistant  Portfolio Analyst      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

For each new application, a team edits three files:
- `config/company_config.yaml` — domain identity, document categories, RBAC
- `prompts/system_prompt.md` — AI persona and domain-specific rules
- S3 bucket — the domain knowledge corpus

The platform handles the rest: ingestion, chunking, indexing, retrieval, memory, guardrails, evaluation, serving, and the Workbench UI.

This is how successful enterprise AI products evolve. The first application proves the architecture. Every subsequent application builds on it, costs less to deliver, and inherits the governance, security, and evaluation frameworks already in place.

The UW CoPilot is not the destination. It is the foundation.

---

*End of Executive Architecture. Version 6.0*
*Companion: UW_COPILOT_TECHNICAL_DESIGN.md*
