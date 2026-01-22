# Stripe Subscription Webhook Service V3

This FastAPI service receives subscription event data from Stripe, processes it, and performs an upsert operation into a standardized GraphQL KV object store.

---

## 📁 Project Structure

```text
stripe-subscription-webhook/
├── fastapi_app/
│   └── main.py               # FastAPI app refactored for Stripe events
├── .env                     # Local environment variables
├── .dockerignore            # Docker ignore list
├── Dockerfile               # Docker container setup
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
└── deploy.sh                # GCR deploy script
```

### *note: you must make the deploy.sh file executable to run it*

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## ⚙️ Environment Variables

These are required for local and deployed environments:

| Variable              | Purpose                                   |
|----------------------|-------------------------------------------|
| `SHOPIFY_WEBHOOK_TOKEN` | Token used to validate incoming requests |
| `GRAPHQL_ENDPOINT`     | URL of the GraphQL API                   |
| `JWT_SECRET`           | Secret key to sign the JWT used for GraphQL auth |

---
note: graphQL endpoint for floframe = <https://graphql-object-service-673677548773.us-central1.run.app>
  graphQL endpoint for landmanager = <https://graphql-object-service-265175461748.us-central1.run.app/>

## 🚀 Run Locally

### 1. Set up the project

```bash
git clone <your-repo-url>
cd shopify-subscription-webhook
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Create `.env` file

```env
SHOPIFY_WEBHOOK_TOKEN=ErnICLWuD1M7JxlvqBU2lwUxF2bGGh1yKeYwMc7Oc1k=
GRAPHQL_ENDPOINT=https://your-graphql-url/graphql
JWT_SECRET=a-string-secret-at-least-256-bits-long
```

**note: use the following bash command to generate a secure JWT secret:**

```bash
    openssl rand -base64 32
```

### 3. Start FastAPI app

```bash
uvicorn fastapi_app.main:app --reload
```

### 4. Test locally using curl

Note the port 8000.

```bash
curl -X POST http://localhost:8000/webhook/shopify \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Token: ErnICLWuD1M7JxlvqBU2lwUxF2bGGh1yKeYwMc7Oc1k=" \
  -d @sample_payload.json
```

---

## 🐳 Build and Run with Docker

### Build the image

```bash
docker build -t shopify-webhook .
```

### Run the container locally

Note the port 8080

```bash
docker run -it --rm -p 8080:8080 --env-file .env shopify-webhook
```

---

## ☁️ Deploy to Google Cloud Run

### Set project config and build

#### FloFrame (bach-455721)

```bash
gcloud config set project bach-455721
gcloud builds submit --tag us-south1-docker.pkg.dev/bach-455721/docker-repo/shopify-subscription-webhook
```

note: if you get a 'user must reauthenticate' message with a password prompt, ctrl-c to break out,  
... then:

```bash
gcloud auth login
```

... then

```bash
gcloud config set project bach-455721
# or 'project-landmanager'
```

#### -old image pointer-

```bash
gcloud builds submit --tag gcr.io/bach/shopify-subscription-webhook
```

#### Landmanager (project-landmanager)

```bash
# for landmanager...
gcloud builds submit --tag us-south1-docker.pkg.dev/project-landmanager/docker-repo/shopify-subscription-webhook
```

### Deploy

#### -new image pointer-

```bash
# for bach
gcloud run deploy shopify-subscription-webhook-service \
  --image us-south1-docker.pkg.dev/bach-455721/docker-repo/shopify-subscription-webhook \
  --region us-south1 \

  --allow-unauthenticated \
  --update-env-vars SHOPIFY_WEBHOOK_TOKEN=EnaED+LupC8OM4dW0AM2LlCpOTcmr/Rs/9i3CFZihis=, \
    JWT_SECRET=a-string-secret-at-least-256-bits-long, \
    GRAPHQL_ENDPOINT=https://graphql-object-service-673677548773.us-central1.run.app/
```

```bash
# for landmanager
gcloud run deploy shopify-subscription-webhook-service \
  --image us-south1-docker.pkg.dev/project-landmanager/docker-repo/shopify-subscription-webhook \
  --region us-south1
```

##### -old image pointer- (floframe)

```bash
gcloud run deploy shopify-subscription-webhook-service \
  --image gcr.io/bach-455721/shopify-subscription-webhook \
  --region us-south1 \
  --allow-unauthenticated \
  --update-env-vars SHOPIFY_WEBHOOK_TOKEN=EnaED+LupC8OM4dW0AM2LlCpOTcmr/Rs/9i3CFZihis=,JWT_SECRET=a-string-secret-at-least-256-bits-long,GRAPHQL_ENDPOINT=https://graphql-object-service-673677548773.us-central1.run.app/
```

---

### 4. CURL Test on gcloud <https://shopify-subscription-webhook-service-293419854814.us-south1.run.app>

```bash
curl -X POST https://shopify-subscription-webhook-service-293419854814.us-south1.run.app/webhook/shopify \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Token: EnaED+LupC8OM4dW0AM2LlCpOTcmr/Rs/9i3CFZihis=" \
  -d @sample_payload.json
```

---

---

## 📄 License

MIT License
