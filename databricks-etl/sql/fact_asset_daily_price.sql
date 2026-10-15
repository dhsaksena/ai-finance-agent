CREATE TABLE IF NOT EXISTS finance_assist.silver.fact_asset_price_daily (
    asset_id          BIGINT NOT NULL,
    trading_date      DATE NOT NULL,
    exchange          STRING NOT NULL,
    series            STRING,
    open_price        DECIMAL(18,4),
    high_price        DECIMAL(18,4),
    low_price         DECIMAL(18,4),
    close_price       DECIMAL(18,4),
    prev_close_price  DECIMAL(18,4),
    volume            BIGINT,
    traded_value      DECIMAL(24,4),

    source_system     STRING NOT NULL,
    ingested_at       TIMESTAMP NOT NULL
)
USING DELTA
PARTITIONED BY (trading_date);