# fastapi_app/main.py v3.0 (Stripe)

from __future__ import annotations

from fastapi import FastAPI, Request, HTTPException, status, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import httpx
from jose import jwt
import datetime
import json
import stripe

# updates for new 'kv' endpoint object handling
import asyncio
from contextlib import asynccontextmanager
from typing import Tuple

# load environment variables
from dotenv import load_dotenv
load_dotenv()

# import logging setup
from fastapi_app.logging_setup import logger

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# --- FastAPI app initialization ---
app = FastAPI()

# --- configuration for HTTP client and retries ---
HTTP_TIMEOUT_S = float(os.getenv("HTTP_TIMEOUT_S", "7"))
HTTP_RETRIES = int(os.getenv("HTTP_RETRIES", "2"))

# Get all possible webhook secrets
STRIPE_WEBHOOK_SECRETS = [
    os.getenv("STRIPE_WEBHOOK_SECRET"),
    os.getenv("STRIPE_TEST_WEBHOOK_SECRET")
]
STRIPE_WEBHOOK_SECRETS = [s for s in STRIPE_WEBHOOK_SECRETS if s]

# --- Lifespan event to manage HTTP client lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=HTTP_TIMEOUT_S)
    try:
        yield
    finally:
        await app.state.http.aclose()

app.router.lifespan_context = lifespan

# --- JWT Token Generator ---
def generate_jwt(user_email: str) -> str:
    secret = os.getenv("JWT_SECRET")
    payload = {
        "sub": user_email,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=96)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

# ======== Object Access Methods ==================================
from fastapi_app.utils.adminKvClient import update_object_stor

async def persist_stripe_subscription(subscription: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
    """
    Persist Stripe subscription using standardized update_object_stor utility.
    Mapping Stripe fields to our storage schema.
    """
    sub_id = subscription.get("id")
    customer_id = subscription.get("customer")
    
    # 1. Improved Email Extraction
    # Strategy: metadata -> expanded customer object -> fallback
    owner_email = subscription.get("metadata", {}).get("email")
    
    if not owner_email and customer_id:
        try:
            customer = stripe.Customer.retrieve(customer_id)
            owner_email = customer.get("email")
            logger.info(f"Retrieved email '{owner_email}' for customer {customer_id}")
        except Exception as e:
            logger.warning(f"Could not retrieve customer email for {customer_id}: {e}")

    if not owner_email:
        # Check if email is in a different metadata field or fallback
        owner_email = subscription.get("metadata", {}).get("customer_email") or os.getenv("DEFAULT_OWNER_EMAIL", "unknown@example.com")

    # 2. Robust Date Handling
    # GraphQL requires endDate if startDate exists. Stripe timestamps are Unix ints.
    start_ts = subscription.get("start_date") or subscription.get("created") or datetime.datetime.now().timestamp()
    end_ts = subscription.get("current_period_end") 
    
    # Ensure end_ts is provided and valid (non-zero)
    if not end_ts or end_ts == 0:
        # Fallback: 1 month from start if missing
        end_ts = start_ts + (30 * 24 * 60 * 60)
        logger.warning(f"Missing current_period_end for {sub_id}, falling back to {end_ts}")

    # Construct standard 'props' for update_object_stor
    props = {
        "id": sub_id,
        "owner": owner_email,
        "authorizedUsers": [owner_email],
        "type": "subscription",
        "name": subscription.get("plan", {}).get("nickname") or "Stripe Subscription",
        "startDate": int(start_ts),
        "endDate": int(end_ts),
        "object": subscription, # Store the full Stripe payload
    }
    
    logger.info(f"Persisting to KV for {owner_email} with key {sub_id}")
    # logger.debug(f"Payload: {json.dumps(props)}") # Avoid logging full object in production unless needed
    
    token = generate_jwt(owner_email)
    result, status_code = await update_object_stor(props, token, client)
    
    if status_code != 200:
        logger.error(f"Persistence failed for {owner_email}: {result}")
        raise HTTPException(status_code=502, detail=result)
        
    return {"status": "success", "result": result}

# === END === Object Access Methods ===================================================
    
# --- GET endpoint for Health Check ---
@app.get("/healthz")
def health_check():
    logger.info("Health check OK")
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "message": "Stripe Subscription Webhook Service is running.",
        "endpoints": {
            "health": "/healthz",
            "webhook": "/webhook/stripe (POST only)"
        },
        "version": "3.0.1"
    }

# --- POST endpoint for Stripe Webhook ---
@app.post("/webhook/stripe")
async def receive_stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    if not STRIPE_WEBHOOK_SECRETS:
        logger.error("No Stripe webhook secrets configured")
        raise HTTPException(status_code=500, detail="Server configuration error")

    event = None
    last_error = None
    
    # Try verifying with available secrets (handling both Prod and Test)
    for secret in STRIPE_WEBHOOK_SECRETS:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
            break # Success!
        except stripe.error.SignatureVerificationError as e:
            last_error = e
            continue
        except ValueError as e:
            logger.warning(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")

    if not event:
        logger.warning(f"Signature verification failed for all secrets: {last_error}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info(f"Received Stripe event: {event['type']}")

    # Handle the event
    if event['type'] in [
        'customer.subscription.created', 
        'customer.subscription.updated',
        'customer.subscription.paused',
        'customer.subscription.resumed'
    ]:
        subscription = event['data']['object']
        result = await persist_stripe_subscription(subscription, request.app.state.http)
        logger.info(f"Persistence outcome for {subscription.get('id')}: {result}")
        return {"status": "success", "persistence": result}
    
    elif event['type'] == 'customer.subscription.deleted':
        # Optional: Handle deletion (e.g., update status to 'canceled' in KV)
        subscription = event['data']['object']
        logger.info(f"Subscription deleted: {subscription.get('id')}")
        # Add deletion logic here if needed
        return {"status": "ignored_deleted"}

    else:
        logger.info(f"Unhandled event type {event['type']}")
        return {"status": "ignored_type"}