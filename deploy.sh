#!/bin/bash

# Exit immediately if a command fails
set -e

# Load environment variables from .env file
if [ -f .env ]; then
  echo "> Loading environment variables from .env"
  export $(grep -v '^#' .env | xargs)
else
  echo "❌ .env file not found. Aborting."
  exit 1
fi

# --- CONFIG ---
PROJECT_ID=${PROJECT_ID:-project-landmanager}
REGION=${REGION:-us-south1}
SERVICE_NAME=${SERVICE_NAME:-stripe-subscription-webhook-service}
IMAGE_URI=${IMAGE_URI:-gcr.io/$PROJECT_ID/$SERVICE_NAME}

# --- DEPLOYMENT ---
echo "> Setting Google Cloud project"
gcloud config set project $PROJECT_ID

echo "> Enabling Cloud Run API (if not already enabled)"
gcloud services enable run.googleapis.com

echo "> Building Docker image and submitting to GCR"
gcloud builds submit --tag $IMAGE_URI

echo "> Deploying to Cloud Run"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URI \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --update-env-vars STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY,STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET,STRIPE_TEST_WEBHOOK_SECRET=$STRIPE_TEST_WEBHOOK_SECRET,JWT_SECRET=$JWT_SECRET,ADMIN_KV_API_URL=$ADMIN_KV_API_URL

echo "> Fetching live service URL"
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)'

echo "> ✅ Deployment complete!"
