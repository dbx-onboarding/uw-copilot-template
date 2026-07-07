# UW CoPilot — Template

> **An AI-powered underwriting intelligence platform that helps underwriters spend more time making decisions and less time searching for information.**

Built on Databricks. Fork, configure, and deploy in under a day.

---

## What it is

A production-ready Underwriting CoPilot accelerator. Atlas Commercial Insurance ships as the reference implementation — 1,502 PDFs across 15 document categories, 8 operational data tables, a working RAG pipeline, and a Streamlit Workbench UI.

**v1 delivers:** A knowledge assistant that retrieves, synthesises, and cites answers from documents and operational data. New submissions are indexed automatically within 20 minutes of landing in S3.

**The roadmap delivers:** Submission summaries on intake, appetite scoring, historical risk matching, referral prediction, pricing intelligence, and an agentic workflow across specialised AI agents.

---

## Quick Start

### Prerequisites

- Databricks workspace on AWS
- Unity Catalog enabled
- S3 bucket for submissions, registered as a UC External Location
- A SQL Warehouse (for the Workbench UI queries)

### Setup

**1. Clone this repo into your Databricks workspace:**

In the Databricks UI: Workspace → Add → Git folder → paste this repo URL.

**2. Edit three files:**

| File | What to change |
|---|---|
| `config/company_config.yaml` | `company`, `catalog`, `warehouse_id`, `intake.volume_name`, `doc_categories`, `rbac` |
| `prompts/system_prompt.md` | AI persona, company branding, domain rules |
| S3 bucket | Drop PDFs in subfolders matching the `id` fields in `doc_categories` |

**3. Install the package and deploy:**

```bash
pip install -e ".[dev]"
databricks bundle deploy
```

**4. Run the one-time setup job:**

```bash
databricks jobs run-now --job-name uw-copilot-pipeline-setup
# or: make setup
```

**5. Open the Workbench:**

The setup job output includes the Databricks App URL.

---

## Naming Convention

Set two fields. Everything else is derived automatically — never set resource names manually.

```yaml
company:
  short_name: "atlas"
  domain:     "insurance"
```

| Resource | Derived name |
|---|---|
| Schema | `atlas_insurance_rag` |
| Vector Search endpoint | `atlas_insurance_vs_endpoint` |
| Model Serving endpoint | `atlas_insurance_rag_endpoint` |
| Databricks App | `atlas_insurance_uw_copilot_app` |
| UC Model | `atlas.atlas_insurance_rag.uw_copilot_rag_model` |

---

## Development Setup

```bash
# Clone and install in editable mode with dev dependencies
git clone https://github.com/your-org/uw-copilot-template
cd uw-copilot-template
pip install -e ".[dev,app]"

# Verify config loads correctly
make config-check

# Run tests
make test

# Lint
make lint
```

The `uw_copilot` package lives in `src/`. Import it anywhere:

```python
from uw_copilot.config    import Config
from uw_copilot.retrieval import HybridRetriever
from uw_copilot.guardrails import GuardrailPipeline
from uw_copilot.chunker   import HierarchicalChunker
from uw_copilot.session   import SessionManager
from uw_copilot.agent     import UWCopilotAgent
```

---

## Repository Structure

```
uw-copilot-template/
├── README.md
├── pyproject.toml              ← Python package definition (src layout)
├── databricks.yml              ← DAB bundle manifest (5 jobs, no hardcoded variables)
├── Makefile                    ← install / test / lint / deploy / setup
│
├── src/
│   └── uw_copilot/             ← Installable Python package
│       ├── __init__.py
│       ├── config.py           ← Config class — reads YAML, derives all resource names
│       ├── chunker.py          ← HierarchicalChunker (parent + child chunks)
│       ├── retrieval.py        ← HybridRetriever — intent routing, RBAC filter
│       ├── guardrails.py       ← GuardrailPipeline — 5 validators in priority order
│       ├── session.py          ← SessionManager — Delta-backed conversation memory
│       └── agent.py            ← UWCopilotAgent (MLflow ChatModel) + log_and_register_agent()
│
├── tests/
│   ├── test_config.py          ← Naming convention, RBAC helpers, discovery
│   ├── test_guardrails.py      ← Block / redact / append correctness
│   └── test_retrieval.py       ← Intent routing, RBAC filter construction
│
├── config/
│   ├── company_config.yaml     ← PRIMARY CONFIG (edit this)
│   └── company_config.example.yaml
│
├── prompts/
│   ├── system_prompt.md        ← AI persona (edit this)
│   ├── guardrails_config.yaml  ← 5 guardrail rules
│   └── schema_context.md       ← Operational table docs for NL-to-SQL
│
├── app/
│   ├── app.py                  ← Streamlit Workbench UI (3-panel layout)
│   ├── app.yaml                ← Databricks Apps manifest
│   └── requirements.txt
│
├── rag_pipeline/               ← Databricks notebooks (pipeline stages)
│   ├── 00_config.py            ← %pip install + Config() — run at top of every notebook
│   ├── 01_ingest_batch         ← Bulk historical ingest via ai_parse_document()
│   ├── 01b_ingest_stream       ← Auto Loader (ongoing S3 intake, every 15 min)
│   ├── 02_chunk_and_index      ← HierarchicalChunker + VS index sync
│   ├── 03_rag_chain            ← UWCopilotAgent integration test
│   ├── 04_memory_and_rbac      ← SessionManager + RBAC smoke tests
│   ├── 05_structured_data      ← NL-to-SQL with schema_context.md
│   ├── 06_guardrails           ← GuardrailPipeline integration test
│   ├── 07_evaluate             ← LLM judge + MLflow metric logging
│   ├── 08_feedback_loop        ← FeedbackManager + override capture
│   ├── 09_deploy               ← log_and_register_agent() + endpoint + app deploy
│   └── uw_copilot_agent.py     ← DEPRECATED — import from uw_copilot.agent instead
│
├── schema/
│   ├── 01_create_tables        ← All Delta tables (pipeline + operational)
│   └── 02_seed_data            ← Atlas reference demo data
│
├── infra/
│   ├── infra_start             ← Recreates VS + serving endpoints
│   └── infra_stop              ← Pauses endpoints (cost saving)
│
├── resources/
│   ├── jobs.yml                ← 5 DAB job definitions (serverless compute)
│   └── clusters.yml            ← Reference config for job-cluster deployments
│
├── sample_data/
│   └── atlas_commercial_insurance/    ← Reference implementation PDFs
│
└── docs/
    ├── UW_COPILOT_TEMPLATE_SPEC.md            ← Executive Architecture
    └── UW_COPILOT_TECHNICAL_DESIGN.md         ← Technical Architecture & Engineering Design
```

---

## Using the Package in Notebooks

At the top of every pipeline notebook:

```python
# Install the package (serverless: runs per session)
%pip install -q -e /Workspace/Users/${current_user}/uw-copilot-template
dbutils.library.restartPython()

from uw_copilot.config import Config
cfg = Config()
cfg.print_summary()
```

Or use `%run ./00_config` for interactive development (re-exports flat names for convenience).

---

## Reference Implementation — Atlas Commercial Insurance

Atlas ships inside the repo as the working reference. Run the setup job on Atlas data, interact with a live CoPilot, and see exactly what a fully configured deployment looks like before loading your own data.

- 1,502 PDFs across 15 document categories
- 8 operational Delta tables pre-seeded with demo data
- Commercial trucking domain — dry van, refrigerated, flatbed, tanker operations

---

## Architecture

Two documents in `docs/`:

- **Executive Architecture** (`UW_COPILOT_TEMPLATE_SPEC.md`) — business case, product vision, workbench, AI workforce, roadmap, costs
- **Technical Architecture & Engineering Design** (`UW_COPILOT_TECHNICAL_DESIGN.md`) — security, AI services, pipeline, similarity search, guardrails, observability, configuration, deployment

---

## License

MIT — fork, configure, and ship.
