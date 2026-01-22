"""
verify_env.py
Ensures all required environment variables are present and valid before starting the FastAPI app.
"""

import os
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger("verify_env")

# Required environment variables and brief descriptions
REQUIRED_VARS = {
    "STRIPE_SECRET_KEY": "Stripe secret API key",
    "STRIPE_WEBHOOK_SECRET": "Stripe webhook endpoint secret (whsec_...)",
    "ADMIN_KV_API_URL": "Admin KV Storage API URL",
    "JWT_SECRET": "JWT signing secret (32+ bytes recommended)",
}

# Optional tunables
OPTIONAL_VARS = {
    "HTTP_TIMEOUT_S": "HTTP timeout in seconds (default 7)",
    "HTTP_RETRIES": "Number of HTTP retry attempts (default 2)",
}


def validate_url(url: str) -> bool:
    """Basic sanity check for HTTPS URLs."""
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except Exception:
        return False


def run_env_checks() -> None:
    missing = []
    invalid = []

    for var, desc in REQUIRED_VARS.items():
        val = os.getenv(var)
        if not val:
            missing.append(f"{var} ({desc})")
            continue

        if "ENDPOINT" in var and not validate_url(val):
            invalid.append(f"{var} invalid URL: {val}")

        if var == "JWT_SECRET" and len(val) < 32:
            invalid.append(f"{var} too short (<32 chars)")

    # Optional diagnostics (not fatal)
    for var, desc in OPTIONAL_VARS.items():
        if os.getenv(var) is None:
            logger.info(f"Optional var {var} not set; using default")
        else:
            logger.info(f"{var} = {os.getenv(var)}")

    if missing:
        msg = "\n".join(["Missing required environment variables:"] + missing)
        logger.error(msg)
        raise SystemExit(1)

    if invalid:
        msg = "\n".join(["Invalid environment variable values:"] + invalid)
        logger.error(msg)
        raise SystemExit(1)

    logger.info("✅ Environment variable check passed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_env_checks()
