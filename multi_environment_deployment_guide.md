# Multi-Environment Deployment Guide

This guide explains how to deploy the `stripe-subscription-webhook-service` to different environments (e.g., `landmanager.us`, `floframe.io`) by leveraging the service's parameterized configuration.

## 📋 Prerequisites

1.  **Stripe Account**: Access to the Stripe dashboard for the target environment.
2.  **Cloudflare KV Worker**: A running Admin KV Storage API worker.
3.  **Google Cloud Project**: A GCP project with Cloud Run and Cloud Build APIs enabled.
4.  **gcloud CLI**: Installed and authenticated (`gcloud auth login`).

---

## ⚙️ Configuration (The `.env` file)

Each environment requires its own `.env` file. Use `.env.example` as a template.

### 1. Stripe Variables
- `STRIPE_SECRET_KEY`: Your Stripe secret API key (`sk_live_...` or `sk_test_...`).
- `STRIPE_WEBHOOK_SECRET`: The signing secret for your production webhook endpoint.
- `STRIPE_TEST_WEBHOOK_SECRET`: (Optional) The signing secret for your test webhook endpoint.

### 2. Persistence Layer
- `ADMIN_KV_API_URL`: The URL of the Cloudflare KV Worker API (e.g., `https://admin-kv-storage-api.jonathonchm.workers.dev`).
- `DEFAULT_OWNER_EMAIL`: The fallback email used if a Stripe event doesn't contain a customer email (e.g., `admin@floframe.io`).

### 3. Security
- `JWT_SECRET`: A secure string (at least 32 characters) used to sign internal JWTs for KV storage access.

---

## 🚀 Deployment to Google Cloud Run

The `deploy.sh` script is designed to be environment-agnostic. You can either update the local `.env` file or pass overrides directly.

### Option A: Using Environment Overrides (Recommended for CI/CD)

You can override the target GCP project and service name at runtime:

```bash
PROJECT_ID=bach-455721 \
SERVICE_NAME=floframe-stripe-webhook \
REGION=us-south1 \
./deploy.sh
```

### Option B: Using a Dedicated `.env` file

1. Create a file named `.env.floframe`.
2. run the deployment:
```bash
cp .env.floframe .env
./deploy.sh
```

---

## 🔗 Stripe Webhook Configuration

Once the service is deployed, you will get a Cloud Run URL (e.g., `https://floframe-stripe-webhook-xyz.a.run.app`).

1.  Go to **Stripe Dashboard > Developers > Webhooks**.
2.  Add a new endpoint with the URL: `{CLOUD_RUN_URL}/webhook/stripe`.
3.  Select the following events:
    - `customer.subscription.created`
    - `customer.subscription.updated`
    - `customer.subscription.deleted`
    - `customer.subscription.paused`
    - `customer.subscription.resumed`
4.  Copy the **Signing Secret** and update your `STRIPE_WEBHOOK_SECRET` in the environment configuration.

---

## 🛠️ Troubleshooting

- **Check Logs**: Use `gcloud run services logs tail {SERVICE_NAME}` to see real-time logs.
- **Portability Check**: Ensure no hardcoded strings remain by running `grep -r "landmanager" .` (excluding `.git` and `templates`).
- **Signature Verification**: If webhooks fail with 400, double-check that the `STRIPE_WEBHOOK_SECRET` matches the secret in the Stripe dashboard for that specific environment.
