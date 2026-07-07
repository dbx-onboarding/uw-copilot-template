# Databricks notebook source
# MAGIC %md
# MAGIC # Infrastructure Start
# MAGIC
# MAGIC Recreates all costly always-on assets that were shut down overnight.
# MAGIC
# MAGIC **Assets created:**
# MAGIC - Vector Search Endpoint (`cfg.vs_endpoint`)
# MAGIC - VS Delta Sync Index (`cfg.vs_index`)
# MAGIC - Model Serving Endpoint (`cfg.serving_endpoint`)
# MAGIC
# MAGIC **Scheduled:** 7:40 AM ET weekdays via `uw-copilot-infra-start` job.

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

from uw_copilot.config import Config

cfg = Config()
cfg.print_summary()

VS_ENDPOINT_NAME     = cfg.vs_endpoint
VS_INDEX_NAME        = cfg.vs_index
VS_INDEX_SOURCE_TABLE = f"{cfg.catalog}.{cfg.schema}.document_chunks"
SERVING_ENDPOINT     = cfg.serving_endpoint
EMBEDDING_MODEL      = cfg.embedding_model
PRIMARY_KEY          = "chunk_id"
EMBEDDING_COLUMN     = "chunk_text"
UC_MODEL_NAME        = cfg.uc_model

print(f"\n   VS endpoint:     {VS_ENDPOINT_NAME}")
print(f"   VS index:        {VS_INDEX_NAME}")
print(f"   Serving EP:      {SERVING_ENDPOINT}")
print(f"   Model:           {UC_MODEL_NAME}")

# COMMAND ----------

# MAGIC %md ## START 1 — Vector Search Endpoint

# COMMAND ----------

from databricks.ai_search.client import VectorSearchClient
import time

vsc = VectorSearchClient(disable_notice=True)

try:
    ep    = vsc.get_endpoint(name=VS_ENDPOINT_NAME)
    state = ep.get("endpoint_status", {}).get("state", "UNKNOWN")
    print(f"ℹ️ VS Endpoint already exists: {VS_ENDPOINT_NAME} ({state})")
except Exception:
    print(f"🚀 Creating Vector Search Endpoint: {VS_ENDPOINT_NAME}")
    vsc.create_endpoint(name=VS_ENDPOINT_NAME, endpoint_type="STANDARD")
    print(f"   Waiting for ONLINE...")
    for i in range(30):
        ep    = vsc.get_endpoint(name=VS_ENDPOINT_NAME)
        state = ep.get("endpoint_status", {}).get("state", "UNKNOWN")
        if state == "ONLINE":
            print(f"   ✅ ONLINE (~{i*10}s)")
            break
        print(f"   [{i*10}s] {state}")
        time.sleep(10)
    else:
        print("   ⚠️ Not online after 5 min — check UI, continuing...")

# COMMAND ----------

# MAGIC %md ## START 2 — Vector Search Index

# COMMAND ----------

try:
    idx = vsc.get_index(endpoint_name=VS_ENDPOINT_NAME, index_name=VS_INDEX_NAME)
    print(f"ℹ️ VS Index already exists: {VS_INDEX_NAME}")
except Exception:
    print(f"🚀 Creating VS Index: {VS_INDEX_NAME}")
    print(f"   Source: {VS_INDEX_SOURCE_TABLE}")
    print(f"   Embedding model: {EMBEDDING_MODEL}")
    vsc.create_delta_sync_index(
        endpoint_name=VS_ENDPOINT_NAME,
        index_name=VS_INDEX_NAME,
        source_table_name=VS_INDEX_SOURCE_TABLE,
        pipeline_type="TRIGGERED",
        primary_key=PRIMARY_KEY,
        embedding_source_column=EMBEDDING_COLUMN,
        embedding_model_endpoint_name=EMBEDDING_MODEL,
    )
    print("   ✅ Index created. Syncing (~20 min for initial sync)...")
    for i in range(150):
        idx    = vsc.get_index(endpoint_name=VS_ENDPOINT_NAME, index_name=VS_INDEX_NAME)
        ready  = idx.describe().get("status", {}).get("ready", False)
        if ready:
            n_vec = idx.describe().get("status", {}).get("num_rows", "?")
            print(f"   ✅ READY — {n_vec} vectors (~{i*10}s)")
            break
        if i % 6 == 0:
            print(f"   [{i*10}s] Syncing...")
        time.sleep(10)
    else:
        print("   ⚠️ Not ready after 25 min — sync continues in background.")

# COMMAND ----------

# MAGIC %md ## START 3 — Model Serving Endpoint

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ServedEntityInput, EndpointCoreConfigInput
from mlflow import MlflowClient
import mlflow

mlflow.set_registry_uri("databricks-uc")
w  = WorkspaceClient()
mc = MlflowClient()

# Get latest champion alias (set by 09_deploy)
try:
    alias_info    = mc.get_model_version_by_alias(name=UC_MODEL_NAME, alias="champion")
    model_version = alias_info.version
    print(f"   Champion model: {UC_MODEL_NAME} v{model_version}")
except Exception:
    versions      = mc.search_model_versions(f"name='{UC_MODEL_NAME}'")
    model_version = max(v.version for v in versions)
    print(f"   Latest model: {UC_MODEL_NAME} v{model_version} (no champion alias)")

try:
    ep = w.serving_endpoints.get(name=SERVING_ENDPOINT)
    print(f"ℹ️ Serving endpoint already exists: {SERVING_ENDPOINT} ({ep.state.ready})")
except Exception:
    print(f"🚀 Creating Model Serving Endpoint: {SERVING_ENDPOINT}")
    w.serving_endpoints.create_and_wait(
        name=SERVING_ENDPOINT,
        config=EndpointCoreConfigInput(
            served_entities=[
                ServedEntityInput(
                    entity_name=UC_MODEL_NAME,
                    entity_version=model_version,
                    scale_to_zero_enabled=True,
                    workload_size="Small",
                )
            ]
        ),
    )
    print("   ✅ Endpoint deployed and READY!")

print("\n" + "="*60)
print("✅ ALL INFRASTRUCTURE ONLINE")
print("="*60)
print(f"   VS Endpoint:  {VS_ENDPOINT_NAME}")
print(f"   VS Index:     {VS_INDEX_NAME}")
print(f"   Serving EP:   {SERVING_ENDPOINT} (v{model_version})")

# COMMAND ----------

# MAGIC %md ## Validation — Quick smoke test

# COMMAND ----------

try:
    resp = w.serving_endpoints.query(
        name=SERVING_ENDPOINT,
        dataframe_records=[{
            "messages": [{"role": "user", "content": "What is the referral trigger for HAZMAT fleets?"}]
        }]
    )
    answer = str(resp)[:200]
    print(f"✅ Endpoint responded: {answer}...")
except Exception as e:
    print(f"⚠️ Validation failed (endpoint may still be warming up): {e}")
