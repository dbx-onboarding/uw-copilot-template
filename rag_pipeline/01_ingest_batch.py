# Databricks notebook source
# DBTITLE 1,01 — Batch Ingest & Parse
# MAGIC %md
# MAGIC # 01 — Batch Ingest & Parse
# MAGIC
# MAGIC Reads all PDFs from the UC Volume at `cfg.volume_path`, parses them with `ai_parse_document()`,
# MAGIC and MERGEs results into the `parsed_documents` Delta table.
# MAGIC
# MAGIC **When to run:** One-time on initial setup, and after bulk volume uploads.
# MAGIC For ongoing intake, use `01b_ingest_stream` (Auto Loader, every 15 min).
# MAGIC
# MAGIC **Runtime:** ~10-15 min for 1,500 PDFs. Scales with corpus size.

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

# Build category_id → label mapping from config
cat_map = {c["id"]: c["label"] for c in cfg.doc_categories}

print(f"Catalog/schema: {C}.{S}")
vol_path = cfg.ensure_volume_exists(spark)
print(f"Volume path:    {vol_path}")
print(f"Categories:     {len(cat_map)}")

# COMMAND ----------

# MAGIC %md ## Step 1 — Read & Parse PDFs

# COMMAND ----------

# DBTITLE 1,Step 1 — Read & Parse PDFs from volume
# Scan the UC volume for all PDFs. read_files() handles the binaryFile format and
# passes each file's bytes to ai_parse_document() for Document AI extraction.
# The category_id is extracted from the first subfolder under the volume root.

parsing_df = spark.sql(f"""
    WITH raw AS (
        SELECT
            sha2(path, 256)                               AS doc_id,
            element_at(split(path, '/'), -1)              AS file_name,
            path                                          AS source_path,
            element_at(split(path, '/'), -2)              AS category_id,
            ai_parse_document(content)                    AS parsed,
            length                                        AS file_size_bytes,
            current_timestamp()                           AS parsed_at
        FROM read_files(
            '{cfg.volume_path}',
            format             => 'binaryFile',
            pathGlobFilter     => '*.pdf',
            recursiveFileLookup => true
        )
    )
    SELECT
        doc_id,
        file_name,
        source_path,
        category_id,
        concat_ws('\\n',
            transform(
                from_json(
                    to_json(parsed:document:elements),
                    'ARRAY<STRUCT<content:STRING, type:STRING>>'
                ),
                x -> x.content
            )
        )                                              AS parsed_text,
        size(from_json(
            to_json(parsed:document:pages),
            'ARRAY<STRUCT<page_id:INT>>'
        ))                                             AS page_count,
        file_size_bytes,
        parsed_at
    FROM raw
""")

# Map category_id → label using the config mapping
cat_expr = F.coalesce(
    *[F.when(F.col("category_id") == k, F.lit(v)) for k, v in cat_map.items()],
    F.col("category_id"),
)

parsing_df = (
    parsing_df
    .withColumn("category", cat_expr)
    .withColumn("content_hash", F.sha2(F.col("source_path"), 256))  # fallback hash
)

print(f"Parsed {parsing_df.count()} documents")

# COMMAND ----------

# MAGIC %md ## Step 2 — MERGE into parsed_documents

# COMMAND ----------

# MERGE is idempotent — re-running updates existing rows (e.g. if a PDF changed)
parsing_df.createOrReplaceTempView("v_new_docs")

spark.sql(f"""
MERGE INTO {C}.{S}.parsed_documents AS target
USING v_new_docs AS source
ON target.doc_id = source.doc_id
WHEN MATCHED AND target.content_hash != source.content_hash THEN
    UPDATE SET *
WHEN NOT MATCHED THEN
    INSERT *
""")

total = spark.sql(f"SELECT COUNT(*) AS n FROM {C}.{S}.parsed_documents").collect()[0]["n"]
print(f"parsed_documents now has {total} rows")

# COMMAND ----------

# MAGIC %md ## Step 3 — Validate

# COMMAND ----------

display(spark.sql(f"""
SELECT
    category,
    COUNT(*)                               AS doc_count,
    ROUND(AVG(LENGTH(parsed_text)), 0)     AS avg_text_len,
    SUM(CASE WHEN parsed_text IS NULL OR LENGTH(parsed_text) = 0 THEN 1 ELSE 0 END) AS empty_count
FROM {C}.{S}.parsed_documents
GROUP BY category
ORDER BY category
"""))
