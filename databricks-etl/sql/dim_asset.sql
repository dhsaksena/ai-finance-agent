CREATE TABLE IF NOT EXISTS finance_assist.silver.dim_asset (
    asset_id BIGINT GENERATED ALWAYS AS IDENTITY,
    asset_name STRING NOT NULL,
    asset_type STRING NOT NULL,       -- STOCK, ETF, MUTUAL_FUND, BOND
    symbol STRING,                    -- NSE symbol or ticker
    isin STRING,                      -- International Securities Identification Number
    exchange STRING,                  -- NSE, BSE, etc.
    issuer STRING,                    -- Company or mutual fund AMC
    category STRING,                  -- Sector, fund category, etc.
    currency STRING DEFAULT 'INR',
    created_at TIMESTAMP DEFAULT current_timestamp(),
    updated_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported');