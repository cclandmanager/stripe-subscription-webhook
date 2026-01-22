import logging
import sys

# Configure root logger
# note: logging is part of python's standard library, so no need to install it separately
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("shopify_webhook")
