import logging
import sys

# Configure logging
def setup_logger(name="DeviceFlasher"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(ch)

    return logger

logger = setup_logger()
