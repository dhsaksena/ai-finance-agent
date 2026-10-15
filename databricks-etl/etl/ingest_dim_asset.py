import csv
import io
import logging
import time

import requests
from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

from utils.logging_utils import get_logger
from integration.nse_data_provider import NSEDataProvider 

logger = get_logger("dim_asset_etl", "info")

source_table = "finance_assist.brownze.kotak_raw_stocks"
target_table = "finance_assist.silver.dim_asset"




start_time = time.time()

logger.info("Starting dim_asset ETL")
logger.info("Source table: %s", source_table)
logger.info("Target table: %s", target_table)

# Read from raw portfolio
raw_df = spark.table(source_table)
logger.info("Successfully read source table")

# Distinct symbols from the portfolio
symbols_df = (
    raw_df
    .filter(
        F.col("Name").isNotNull()
        & (F.trim(F.col("Name")) != "")
    )
    .select(
        F.upper(F.trim(F.col("Name"))).alias("symbol"),
        F.lit("STOCK").alias("asset_type"),
        F.lit("NSE").alias("exchange")
    )
    .distinct()
)

symbols = [r["symbol"] for r in symbols_df.select("symbol").collect()]
logger.info("Portfolio has %d distinct symbols", len(symbols))

# Download NSE's list, then keep only the portfolio's symbols.
# If NSE is unreachable, degrade instead of failing: new assets fall back to
# symbol as asset_name and existing names are left untouched.
try:
    provider = NSEDataProvider()
    nse_master = provider.fetch_nse_names()
    logger.info("NSE master list downloaded (%d rows, kept only for lookup)", len(nse_master))
except RuntimeError:
    logger.exception("NSE fetch failed; proceeding without NSE names")
    nse_master = {}

matched_rows, unmatched = [], []
for sym in symbols:
    key = resolve_nse_symbol(sym, nse_master)
    if key is None:
        unmatched.append(sym)
    else:
        matched_rows.append((sym, nse_master[key]))  # keyed by the portfolio symbol

logger.info("Matched %d of %d portfolio symbols on NSE", len(matched_rows), len(symbols))
if unmatched:
    logger.warning("%d symbol(s) not found in NSE list: %s", len(unmatched), sorted(unmatched))

nse_df = spark.createDataFrame(matched_rows, schema=NSE_SCHEMA)

# One row per portfolio symbol, so the join cannot fan out the merge source
source_df = symbols_df.join(F.broadcast(nse_df), on="symbol", how="left")

logger.info("Source transformation defined successfully")

# Merge into the dimension table
target = DeltaTable.forName(spark, target_table)

merge_builder = (
    target.alias("t")
    .merge(
        source_df.alias("s"),
        """
        t.symbol = s.symbol
        AND t.asset_type = s.asset_type
        """
    )
    # Backfill/refresh names for existing rows, only when NSE gave us a name
    .whenMatchedUpdate(
        condition="s.nse_name IS NOT NULL AND NOT (t.asset_name <=> s.nse_name)",
        set={"asset_name": "s.nse_name"}
    )
    .whenNotMatchedInsert(
        values={
            "asset_name": "COALESCE(s.nse_name, s.symbol)",
            "asset_type": "s.asset_type",
            "symbol": "s.symbol",
            "exchange": "s.exchange"
        }
    )
)

try:
    merge_builder.execute()

    logger.info("Delta merge completed successfully")

    # What the merge actually did
    metrics = target.history(1).select("operationMetrics").collect()[0][0]
    logger.info(
        "Merge metrics: inserted=%s updated=%s",
        metrics.get("numTargetRowsInserted"),
        metrics.get("numTargetRowsUpdated"),
    )

    # Portfolio symbols whose asset_name is still just the symbol
    still_symbol = [
        r["symbol"]
        for r in (
            spark.table(target_table)
            .join(symbols_df.select("symbol", "asset_type"), on=["symbol", "asset_type"])
            .filter(F.col("asset_name") == F.col("symbol"))
            .select("symbol")
            .collect()
        )
    ]
    logger.info("Portfolio rows in dim_asset with asset_name == symbol: %s", sorted(still_symbol))

    elapsed = round(time.time() - start_time, 2)
    logger.info(
        "dim_asset ETL completed successfully in %s seconds",
        elapsed
    )

except Exception:
    logger.exception("dim_asset ETL failed")
    raise