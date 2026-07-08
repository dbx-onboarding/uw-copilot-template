# UW CoPilot — Executive Demo Runbook

A 10-minute demo script and pre-flight checklist for presenting the Atlas Commercial
Insurance **UW CoPilot** (Databricks App) to a Chief Underwriting Officer / CEO.

> Present the **React web app** (this `webapp/` folder), not the older Streamlit app.
> Deploy `webapp/` from the repo root so `../config` and `../src` are included.

---

## 1. Pre-flight checklist (do this ~15 min before)

1. **Deploy the right build.** Rebuild and deploy the React app:
   ```
   npm --prefix frontend install && npm --prefix frontend run build
   # deploy the webapp/ folder as the Databricks App (uvicorn server.main:app)
   ```
1a. **Re-run the schema notebooks** (`schema/01_create_tables.py` then
   `schema/02_seed_data.py`) so the new **`account_intel`** table and the Dixie Express
   renewal history are present. Without this, the Authority & Safety tab is empty.
2. **Warm the services** (or the AI story falls flat). Open **Settings** in the app —
   all three should read **Connected**:
   - SQL Warehouse (running, not cold)
   - Model Serving endpoint (powers the CoPilot)
   - Vector Search index (so CoPilot answers cite real documents)
3. **Confirm identity** shows your name/email/role in the top-right (from Databricks
   Apps SSO headers).
4. **Open the browser full-screen** on a laptop (the left rail + workbench are
   desktop-optimized).

If a warehouse is **not** connected, the app still runs on representative demo data —
fine for a UI walk-through, but say so, and expect the CoPilot to show its demo
fallback message.

---

## 2. The golden path (what to click, in order)

1. **Home** — lead with the five KPI tiles (Active Queue, New Submissions, High Risk
   Alerts, Pending Referral, **Portfolio Score**). Ask the **CoPilot** a portfolio
   question from the suggested chips (e.g., *"What's driving the high-risk alerts?"*).
2. **Submissions** — the working queue. Point out AI Score, Risk badge, Loss Ratio,
   Status. Click a **company name** to open its workbench.
3. **Submission workbench (detail)** — the centerpiece:
   - **AI Recommendation** — evidence-first: verdict (APPROVE / REVIEW / REFER), a
     qualitative **Confidence** (High/Moderate/Low — no fake %), a plain-language
     **rationale**, and an **evidence list** where each factor cites the Atlas rule that
     fired (RA-0001 §4.2, UW-0001 §6, AUTH-0001…). It explains itself and doesn't anchor.
   - **Recommended Next Steps** and **Recommended Subjectivities** (quote conditions).
   - Tabs: **Pricing · Authority & Safety · Claims · Loss Development · Drivers · Documents**.
     - **Pricing** — indicated premium, rate need vs. expiring, rate taken, and an
       **Adequate / Marginal / Inadequate** verdict with per-unit metrics.
     - **Authority & Safety** — authority age (new-authority flag), prior carrier, **why
       in market**, filings (MCS-150 / MCS-90 / BMC-91), and FMCSA SMS OOS rates vs.
       national average with ⚠ alerts + data as-of dates.
     - **Loss Development** — trend, severity, open reserves, large-loss count, and the
       **valued-as-of** date on every figure.
   - **CoPilot** (right) — answers are grounded in the account's documents and end with a
     **Sources:** line (document + page). Multiple **chat tabs** keep parallel threads.
   - Take a decision: **Refer to Senior UW** → records to the audit log (demo notice if
     no warehouse).
4. **Claims** — portfolio-wide claim inventory; click a claim for the detail modal
   (narrative, incurred/paid, reserve, litigation).
5. **Loss Control** — fleet safety / CSA posture per insured; click a row for the
   safety profile + loss-control assessment.
6. **Analytics** — live portfolio breakdowns (by risk, operation, status; premium at
   risk; avg loss ratio; derived Portfolio Score).
7. **Settings** — show the live connections (proof it's real Databricks infrastructure).

---

## 3. Talking points (the narrative)

- **One workbench on the Lakehouse.** Submissions, claims, drivers, loss runs, and
  1,500+ documents all live in **Unity Catalog Delta tables** and a **Vector Search**
  index — no data movement.
- **AI where it matters.** Every submission is scored with Atlas underwriting rules;
  the CoPilot answers questions grounded in the account's own documents (RAG on
  **Model Serving**), with a thumbs up/down feedback loop.
- **Governed & auditable.** Identity and role come from Databricks SSO; underwriting
  decisions write to an audit table; access is controlled by Unity Catalog.
- **Portfolio Score** is a derived health metric (100 minus penalties for average loss
  ratio and high-risk / referral concentration) — it moves with the book.

---

## 4. What to avoid / have an answer for

- **Cold services.** A cold warehouse or unconfigured serving endpoint is the only
  thing that looks broken — verify in Settings first (step 1.2).
- **"Not persisted" on a decision.** Expected without a warehouse write-path; say the
  audit table is wired in the full deployment.
- **Scheduled vs. on-file drivers.** A submission may show *"8 scheduled · N on file"* —
  this is intentional (not all MVRs uploaded yet), not a bug.

---

## 5. Suggested CoPilot questions that demo well

Ask **guideline / appetite / procedure** questions — these are answerable from the
1,500-doc corpus and return grounded, cited answers:

- "What are Atlas's referral triggers for an account like this?"
- "What's our risk appetite for long-haul general freight?"
- "What conditions would you recommend to quote this risk?"
- "What are the driver qualification requirements?"

**Avoid** account-specific *numeric* questions ("summarize this account's loss history") —
those numbers live in the structured tables (Loss Development tab), not the document
corpus, so the CoPilot can't cite them. Read loss history from the **Loss Development** tab.

---

*Atlas Commercial Insurance · UW CoPilot · Databricks Apps · demo runbook v1.0*
