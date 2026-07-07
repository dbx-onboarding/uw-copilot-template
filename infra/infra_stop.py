# Databricks notebook source
# MAGIC %md
# MAGIC # Infrastructure Stop
# MAGIC
# MAGIC Pauses all always-on assets to reduce overnight costs.
# MAGIC Deletes the serving endpoint, VS index, and VS endpoint.
# MAGIC Data is untouched — run infra_start to recreate.
# MAGIC
# MAGIC **Scheduled:** 8 PM ET weekdays via `uw-copilot-infra-stop` job.

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

from databricks.ai_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient
from uw_copilot.config import Config

cfg = Config()
VS_ENDPOINT_NAME = cfg.vs_endpoint
VS_INDEX_NAME    = cfg.vs_index
SERVING_ENDPOINT = cfg.serving_endpoint

print(f"Stopping infrastructure for: {cfg.prefix}")
print(f"   VS endpoint: {VS_ENDPOINT_NAME}")
print(f"   VS index:    {VS_INDEX_NAME}")
print(f"   Serving EP:  {SERVING_ENDPOINT}")

w   = WorkspaceClient()
vsc = VectorSearchClient(disable_notice=True)

# --- STOP 1: Model Serving Endpoint ---
try:
    w.serving_endpoints.get(name=SERVING_ENDPOINT)
    w.serving_endpoints.delete(name=SERVING_ENDPOINT)
    print(f"✅ Deleted serving endpoint: {SERVING_ENDPOINT}")
except Exception as e:
    print(f"ℹ️ Serving EP already offline: {e}")

# --- STOP 2: Vector Search Index ---
try:
    vsc.get_index(endpoint_name=VS_ENDPOINT_NAME, index_name=VS_INDEX_NAME)
    vsc.delete_index(endpoint_name=VS_ENDPOINT_NAME, index_name=VS_INDEX_NAME)
    print(f"✅ Deleted VS index: {VS_INDEX_NAME}")
except Exception as e:
    print(f"ℹ️ VS index already offline: {e}")

# --- STOP 3: Vector Search Endpoint ---
try:
    vsc.delete_endpoint(name=VS_ENDPOINT_NAME)
    print(f"✅ Deleted VS endpoint: {VS_ENDPOINT_NAME}")
except Exception as e:
    print(f"ℹ️ VS endpoint already offline: {e}")

print("\n🌙 All infrastructure stopped. Costs paused until next START.")
