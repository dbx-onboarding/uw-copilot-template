# Databricks notebook source
# DBTITLE 1,01b — Stream Ingest (Auto Loader)
# MAGIC %md
# MAGIC # 01b — Stream Ingest (Auto Loader)
# MAGIC
# MAGIC Runs every 15 minutes via the `uw-copilot-intake` job.
# MAGIC Picks up new PDF files that have landed in `cfg.volume_path` since the last run,
# MAGIC parses them, and appends to `parsed_documents`.
# MAGIC
# MAGIC **How it works:** Auto Loader tracks which files it has already processed
# MAGIC using a checkpoint stored in `/tmp/uw_copilot_{prefix}_checkpoint/`.
# MAGIC Each run only processes net-new files — no re-processing.

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

# DBTITLE 1,Config and volume bootstrap
from uw_copilot.config import Config
from pyspark.sql import functions as F

cfg = Config()
C   = cfg.catalog
S   = cfg.schema

CHECKPOINT_PATH = f"/tmp/uw_copilot_{cfg.prefix}_ingest_checkpoint"
cat_map = {c["id"]: c["label"] for c in cfg.doc_categories}

vol_path = cfg.ensure_volume_exists(spark)
print(f"Volume source: {vol_path}")
print(f"Checkpoint:    {CHECKPOINT_PATH}")

# COMMAND ----------

# MAGIC %md ## Auto Loader — read new files only

# COMMAND ----------

# DBTITLE 1,Auto Loader — read new files from volume
# cloudFiles detects new files in the UC volume and resumes from checkpoint.
# trigger(availableNow=True) processes all currently-available new files
# and then stops the stream — suitable for scheduled jobs.

raw_stream = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "binaryFile")
    .option("pathGlobFilter", "*.pdf")
    .option("recursiveFileLookup", "true")
    .load(cfg.volume_path)
)

# Extract category_id from subfolder and map to label
cat_expr = F.coalesce(
    *[F.when(F.element_at(F.split(F.col("path"), "/"), -2) == k, F.lit(v))
      for k, v in cat_map.items()],
    F.element_at(F.split(F.col("path"), "/"), -2),
)

# COMMAND ----------

# MAGIC %md ## Parse and append to parsed_documents

# COMMAND ----------

def process_batch(batch_df, batch_id):
    """Parse each micro-batch and append to parsed_documents."""
    if batch_df.isEmpty():
        return

    batch_df.createOrReplaceTempView("v_stream_batch")

    parsed = spark.sql(f"""
        SELECT
            sha2(path, 256)                           AS doc_id,
            element_at(split(path, '/'), -1)          AS file_name,
            path                                      AS source_path,
            element_at(split(path, '/'), -2)          AS category_id,
            concat_ws('\\n',
                transform(
                    from_json(
                        to_json(ai_parse_document(content):document:elements),
                        'ARRAY<STRUCT<content:STRING, type:STRING>>'
                    ),
                    x -> x.content
                )
            )                                         AS parsed_text,
            size(from_json(
                to_json(ai_parse_document(content):document:pages),
                'ARRAY<STRUCT<page_id:INT>>'
            ))                                        AS page_count,
            length                                    AS file_size_bytes,
            current_timestamp()                       AS parsed_at,
            sha2(content, 256)                        AS content_hash
        FROM v_stream_batch
    """)

    cat_expr_local = F.coalesce(
        *[F.when(F.col("category_id") == k, F.lit(v)) for k, v in cat_map.items()],
        F.col("category_id"),
    )
    parsed = parsed.withColumn("category", cat_expr_local)

    parsed.createOrReplaceTempView("v_new_batch_docs")
    spark.sql(f"""
        MERGE INTO {C}.{S}.parsed_documents AS target
        USING v_new_batch_docs AS source
        ON target.doc_id = source.doc_id
        WHEN NOT MATCHED THEN INSERT *
    """)
    print(f"Batch {batch_id}: inserted {parsed.count()} documents")


query = (
    raw_stream
    .writeStream
    .foreachBatch(process_batch)
    .option("checkpointLocation", CHECKPOINT_PATH)
    .trigger(availableNow=True)   # process all new files, then stop
    .start()
)

query.awaitTermination()
print("✅ Intake run complete")

# COMMAND ----------

# Verify new documents count
total = spark.sql(f"SELECT COUNT(*) AS n FROM {C}.{S}.parsed_documents").collect()[0]["n"]
print(f"parsed_documents total: {total}")
