# Databricks notebook source
# MAGIC %md
# MAGIC # 07 — Evaluate
# MAGIC
# MAGIC Runs a curated 15-question eval set through the deployed serving endpoint,
# MAGIC evaluates with MLflow GenAI scorers, and logs metrics to an MLflow experiment.
# MAGIC
# MAGIC **Scorers used:** faithfulness, relevance_to_query, safety (built-in)
# MAGIC
# MAGIC **Quality gates:**
# MAGIC - relevance >= 0.80
# MAGIC - safety >= 0.95
# MAGIC - faithfulness >= 0.75
# MAGIC
# MAGIC **Prerequisites:** 09_deploy must have run (serving endpoint must be ONLINE)

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

import mlflow
import pandas as pd
from databricks.sdk       import WorkspaceClient
from uw_copilot.config    import Config

mlflow.set_registry_uri("databricks-uc")

cfg = Config()
w   = WorkspaceClient()

EXPERIMENT_NAME = f"/Users/{w.current_user.me().user_name}/uw_copilot_eval_{cfg.prefix}"
mlflow.set_experiment(EXPERIMENT_NAME)

print(f"Serving endpoint: {cfg.serving_endpoint}")
print(f"Experiment: {EXPERIMENT_NAME}")

# COMMAND ----------

# MAGIC %md ## Evaluation Dataset (15 questions)

# COMMAND ----------

eval_questions = [
    # Underwriting Guidelines
    "What are the referral triggers for HAZMAT fleet operations?",
    "What is the maximum fleet size eligible for standard rate filing?",
    "What CSA BASIC percentile thresholds require senior UW referral?",
    "What are the driver qualification requirements for new operators?",
    # Claims Procedures
    "What is the claims handling process for losses over $250,000?",
    "How long does the insured have to report a new claim?",
    "What triggers a large-loss review by the claims director?",
    "What is the SIU referral threshold for suspicious claims?",
    # Product Guides
    "What lines of business are available under the commercial auto program?",
    "What is the minimum liability limit for long-haul fleets?",
    "Does the MTC coverage include reefer breakdown?",
    # Authority & Limits
    "What is the authority limit for an underwriter to bind without referral?",
    # Regulatory
    "What are the FMCSA filing requirements for commercial auto policies?",
    # Cross-domain
    "What is Heartland Express's loss ratio and do they require a referral?",
    # Identity lookup
    "Show me the details for claim CLM-25-3891045",
]

print(f"Eval set: {len(eval_questions)} questions")

# COMMAND ----------

# MAGIC %md ## Query Serving Endpoint

# COMMAND ----------

# DBTITLE 1,Query serving endpoint
from databricks.sdk.service.serving import ChatMessage as SDKMsg, ChatMessageRole

results = []
for i, q in enumerate(eval_questions, 1):
    try:
        resp = w.serving_endpoints.query(
            name        = cfg.serving_endpoint,
            messages    = [SDKMsg(role=ChatMessageRole.USER, content=q)],
            max_tokens  = 1000,
            temperature = 0.1,
        )
        answer = resp.choices[0].message.content if resp.choices else ""
        results.append({"request": q, "response": answer[:2000]})
        print(f"  [{i:>2}/{len(eval_questions)}] OK  {q[:60]}")
    except Exception as e:
        results.append({"request": q, "response": f"ERROR: {e}"})
        print(f"  [{i:>2}/{len(eval_questions)}] ERR {q[:55]}: {type(e).__name__}")

results_df = pd.DataFrame(results)
print(f"\nCollected {len(results_df)} responses")
print(f"Errors:   {results_df['response'].str.startswith('ERROR:').sum()}")

# COMMAND ----------

# MAGIC %md ## MLflow GenAI Evaluation

# COMMAND ----------

QUALITY_THRESHOLDS = {
    "relevance_to_query/mean": 0.80,
    "safety/mean":             0.95,
    "faithfulness/mean":       0.75,
}

try:
    from mlflow.genai.scorers import (
        faithfulness,
        relevance_to_query,
        safety,
    )

    with mlflow.start_run(run_name=f"eval_{cfg.prefix}"):
        mlflow.log_params({
            "n_questions":       len(eval_questions),
            "serving_endpoint":  cfg.serving_endpoint,
            "chat_model":        cfg.chat_model,
            "embedding_model":   cfg.embedding_model,
        })

        eval_result = mlflow.genai.evaluate(
            data=results_df.rename(columns={"request": "inputs"}),
            scorers=[faithfulness(), relevance_to_query(), safety()],
        )

        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        for metric, value in sorted(eval_result.metrics.items()):
            threshold = QUALITY_THRESHOLDS.get(metric)
            if threshold:
                status = "✅ PASS" if value >= threshold else "❌ FAIL"
                print(f"  {status}  {metric:<35} {value:.3f}  (threshold: {threshold})")
            else:
                print(f"         {metric:<35} {value:.3f}")

        mlflow.log_metrics(eval_result.metrics)

except ImportError:
    print("mlflow.genai.evaluate not available — logging manual metrics instead")
    # Fallback: just log the dataset
    with mlflow.start_run(run_name=f"eval_{cfg.prefix}"):
        mlflow.log_params({"n_questions": len(eval_questions)})
        spark.createDataFrame(results_df).write.mode("overwrite").saveAsTable(
            f"{cfg.catalog}.{cfg.schema}.eval_results_latest"
        )
        print(f"Results saved to {cfg.catalog}.{cfg.schema}.eval_results_latest")

# COMMAND ----------

display(spark.createDataFrame(results_df))
print("\n✅ Evaluation complete")
