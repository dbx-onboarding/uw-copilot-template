# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Chunk & Index
# MAGIC
# MAGIC Produces hierarchical parent/child chunks from `parsed_documents` and
# MAGIC loads them into a Vector Search Delta Sync index.
# MAGIC
# MAGIC **Chunking strategy (parent/child):**
# MAGIC - Parent chunks (~2500 chars): section-level context passed to the LLM
# MAGIC - Child chunks (~600 chars): precise retrieval targets indexed in VS
# MAGIC - Retrieval flow: search children → expand to parent → send parent to LLM
# MAGIC
# MAGIC **Atlas stats:** 1,502 documents → 2,268 child chunks
# MAGIC
# MAGIC **Run after:** 01_ingest_batch (or automatically when called from pipeline-setup)

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

from uw_copilot.config  import Config
from uw_copilot.chunker import HierarchicalChunker
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

cfg     = Config()
C       = cfg.catalog
S       = cfg.schema
chunker = HierarchicalChunker(
    parent_size=cfg.parent_chunk_size,
    child_size=cfg.child_chunk_size,
    overlap=cfg.chunk_overlap,
)

print(f"Catalog/schema: {C}.{S}")
print(f"Parent size:    {cfg.parent_chunk_size} chars")
print(f"Child size:     {cfg.child_chunk_size}  chars")
print(f"Overlap:        {cfg.chunk_overlap}  chars")

# COMMAND ----------

# MAGIC %md ## Step 1 — Produce chunks from parsed_documents

# COMMAND ----------

parsed_docs = spark.table(f"{C}.{S}.parsed_documents").filter("parsed_text IS NOT NULL AND LENGTH(parsed_text) > 0")
doc_count   = parsed_docs.count()
print(f"Documents to chunk: {doc_count}")

# Chunk via Pandas UDF for scalability
schema = StructType([
    StructField("chunk_id",   StringType(),  False),
    StructField("parent_id",  StringType(),  True),
    StructField("chunk_type", StringType(),  False),
    StructField("chunk_text", StringType(),  True),
    StructField("doc_id",     StringType(),  False),
    StructField("category",   StringType(),  True),
    StructField("source_path",StringType(),  True),
    StructField("char_start", IntegerType(), True),
    StructField("char_end",   IntegerType(), True),
])

import pandas as pd

@F.pandas_udf(returnType=schema, functionType=F.PandasUDFType.GROUPED_MAP)
def chunk_document(pdf: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in pdf.iterrows():
        chunks = chunker.chunk(
            text=row["parsed_text"] or "",
            doc_id=row["doc_id"],
            category=row.get("category", ""),
            source_path=row.get("source_path", ""),
        )
        for c in chunks:
            rows.append({
                "chunk_id":    c.chunk_id,
                "parent_id":   c.parent_id,
                "chunk_type":  c.chunk_type,
                "chunk_text":  c.text,
                "doc_id":      c.doc_id,
                "category":    c.category,
                "source_path": c.source_path,
                "char_start":  c.char_start,
                "char_end":    c.char_end,
            })
    return pd.DataFrame(rows, columns=[f.name for f in schema])

chunks_df = (
    parsed_docs
    .select("doc_id", "parsed_text", "category", "source_path")
    .groupby("doc_id")
    .apply(chunk_document)
)

child_count  = chunks_df.filter("chunk_type = 'child'").count()
parent_count = chunks_df.filter("chunk_type = 'parent'").count()
print(f"Generated {parent_count} parent + {child_count} child chunks")

# COMMAND ----------

# MAGIC %md ## Step 2 — Write to document_chunks (MERGE)

# COMMAND ----------

chunks_df.createOrReplaceTempView("v_new_chunks")

spark.sql(f"""
MERGE INTO {C}.{S}.document_chunks AS target
USING (SELECT *, current_timestamp() AS created_at FROM v_new_chunks) AS source
ON target.chunk_id = source.chunk_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")

total = spark.sql(f"SELECT COUNT(*) AS n FROM {C}.{S}.document_chunks").collect()[0]["n"]
print(f"document_chunks now has {total} rows")

# COMMAND ----------

# MAGIC %md ## Step 3 — Create VS Endpoint (idempotent)

# COMMAND ----------

import time
from databricks.ai_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)

try:
    ep    = vsc.get_endpoint(name=cfg.vs_endpoint)
    state = ep.get("endpoint_status", {}).get("state", "UNKNOWN")
    print(f"VS endpoint already exists: {cfg.vs_endpoint} ({state})")
except Exception:
    print(f"Creating VS endpoint: {cfg.vs_endpoint}")
    vsc.create_endpoint(name=cfg.vs_endpoint, endpoint_type="STANDARD")
    for i in range(30):
        ep    = vsc.get_endpoint(name=cfg.vs_endpoint)
        state = ep.get("endpoint_status", {}).get("state", "UNKNOWN")
        if state == "ONLINE":
            print(f"  ✅ ONLINE (~{i*10}s)")
            break
        time.sleep(10)

# COMMAND ----------

# MAGIC %md ## Step 4 — Create / Sync VS Index

# COMMAND ----------

try:
    idx = vsc.get_index(endpoint_name=cfg.vs_endpoint, index_name=cfg.vs_index)
    print(f"Index exists: {cfg.vs_index}. Triggering sync...")
    idx.sync()
    print("  Sync triggered. Will complete in background (~10 min).")
except Exception:
    print(f"Creating Delta Sync index: {cfg.vs_index}")
    vsc.create_delta_sync_index(
        endpoint_name=cfg.vs_endpoint,
        index_name=cfg.vs_index,
        source_table_name=f"{C}.{S}.document_chunks",
        pipeline_type="TRIGGERED",
        primary_key="chunk_id",
        embedding_source_column="chunk_text",
        embedding_model_endpoint_name=cfg.embedding_model,
    )
    print("  Index created. Initial sync will take ~20 min.")
    # Wait up to 25 min
    for i in range(150):
        idx   = vsc.get_index(endpoint_name=cfg.vs_endpoint, index_name=cfg.vs_index)
        ready = idx.describe().get("status", {}).get("ready", False)
        if ready:
            n = idx.describe().get("status", {}).get("num_rows", "?")
            print(f"  ✅ READY — {n} vectors (~{i*10}s)")
            break
        if i % 6 == 0:
            print(f"  [{i*10}s] Syncing...")
        time.sleep(10)

# COMMAND ----------

# MAGIC %md ## Validate

# COMMAND ----------

display(spark.sql(f"""
SELECT chunk_type, category, COUNT(*) AS chunks
FROM {C}.{S}.document_chunks
GROUP BY chunk_type, category
ORDER BY chunk_type, category
"""))
