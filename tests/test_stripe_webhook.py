import asyncio
import os
import json
import time
from unittest.mock import AsyncMock, patch, MagicMock
import stripe

# Mock Stripe Event Data
MOCK_STRIPE_SUB = {
    "id": "sub_1726354",
    "customer": "cus_98765",
    "status": "active",
    "start_date": int(time.time()),
    "current_period_end": int(time.time() + 2592000), # +30 days
    "plan": {
        "nickname": "Pro Plan",
        "amount": 2999,
        "currency": "usd"
    },
    "metadata": {
        "email": "stripe-tester@example.com"
    }
}

async def test_persist_stripe_subscription():
    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": {"upsertObject": "ok"}}
    mock_resp.text = json.dumps({"data": {"upsertObject": "ok"}})
    mock_client.post.return_value = mock_resp
    
    # Mock environment
    with patch.dict(os.environ, {
        "GRAPHQL_ENDPOINT_KV": "https://mock.gql/graphql",
        "JWT_SECRET": "test-secret-at-least-thirty-two-characters-long",
        "STRIPE_SECRET_KEY": "sk_test_mock",
        "STRIPE_WEBHOOK_SECRET": "whsec_mock",
        "HTTP_RETRIES": "0"
    }):
        # Mock stripe.Customer.retrieve to avoid network call
        with patch("stripe.Customer.retrieve") as mock_cust:
            mock_cust.return_value = {"email": "stripe-tester@example.com"}
            
            from fastapi_app.main import persist_stripe_subscription
            result = await persist_stripe_subscription(MOCK_STRIPE_SUB, mock_client)
            
            print(f"Result: {result}")
            assert result["status"] == "success"
            
            # Verify the call to the client
            args, kwargs = mock_client.post.call_args
            payload = kwargs["json"]
            variables = payload["variables"]
            
            print(f"Sent Variables: {json.dumps(variables, indent=2)}")
            
            assert variables["value"]["key"] == "sub_1726354"
            assert variables["value"]["owner"] == "stripe-tester@example.com"
            assert variables["value"]["type"] == "subscription"
            assert variables["value"]["object"]["id"] == "sub_1726354"

if __name__ == "__main__":
    asyncio.run(test_persist_stripe_subscription())
    print("✅ Stripe verification test passed!")
