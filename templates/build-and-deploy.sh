# Authenticate with gcloud
gcloud auth login
gcloud config set project project-landmanager

# Build the container image
gcloud builds submit --tag gcr.io/project-landmanager/stripe-subscription-webhook-service

# Deploy to Cloud Run
gcloud run deploy stripe-subscription-webhook-service \
  --image gcr.io/project-landmanager/stripe-subscription-webhook-service \
  --region us-south1 \
  --allow-unauthenticated \
  --update-env-vars STRIPE_SECRET_KEY=replace-this-secret,STRIPE_WEBHOOK_SECRET=replace-this-secret,JWT_SECRET=a-string-secret-at-least-256-bits-long,ADMIN_KV_API_URL=https://admin-kv-storage-api.craig-3e9.workers.dev
