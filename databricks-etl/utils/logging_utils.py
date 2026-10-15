import logging

def get_logger(filename: str, level: str) -> logging.Logger:
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    
    logger = logging.getLogger("dim_asset_etl")
    
    return logger
