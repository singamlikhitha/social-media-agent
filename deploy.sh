#!/bin/bash
set -e

PROJECT_ID="zbala-1"
REGION="us-central1"
BACKEND_SERVICE="social-media-backend"
FRONTEND_SERVICE="social-media-frontend"
DB_INSTANCE="social-media-db"
DB_NAME="social_media_agent"
DB_PASSWORD="${DB_PASSWORD:-changeme}"

echo "=== Deploying Social Media Agent to Cloud Run ==="
echo "Project: $PROJECT_ID | Region: $REGION"

# 1. Enable required services
echo ""
echo ">>> Enabling GCP services..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  --project=$PROJECT_ID

# 2. Create Cloud SQL instance (if not exists)
echo ""
echo ">>> Setting up Cloud SQL..."
if ! gcloud sql instances describe $DB_INSTANCE --project=$PROJECT_ID &>/dev/null; then
  echo "Creating Cloud SQL instance (this takes ~5 minutes)..."
  gcloud sql instances create $DB_INSTANCE \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --project=$PROJECT_ID \
    --root-password=$DB_PASSWORD \
    --storage-size=10GB \
    --storage-auto-increase

  # Create database
  gcloud sql databases create $DB_NAME \
    --instance=$DB_INSTANCE \
    --project=$PROJECT_ID

  # Set postgres user password
  gcloud sql users set-password postgres \
    --instance=$DB_INSTANCE \
    --password=$DB_PASSWORD \
    --project=$PROJECT_ID
else
  echo "Cloud SQL instance already exists."
fi

# Get the Cloud SQL connection name
SQL_CONNECTION=$(gcloud sql instances describe $DB_INSTANCE \
  --project=$PROJECT_ID \
  --format="value(connectionName)")
echo "SQL Connection: $SQL_CONNECTION"

DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${SQL_CONNECTION}"

# 3. Build and deploy backend
echo ""
echo ">>> Building & deploying backend..."
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$BACKEND_SERVICE \
  --project=$PROJECT_ID \
  --timeout=900

# Deploy backend to Cloud Run
gcloud run deploy $BACKEND_SERVICE \
  --image gcr.io/$PROJECT_ID/$BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --timeout 300 \
  --add-cloudsql-instances $SQL_CONNECTION \
  --set-env-vars "DATABASE_URL=${DATABASE_URL}" \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --set-env-vars "JWT_SECRET=${JWT_SECRET}" \
  --set-env-vars "TOKEN_ENCRYPTION_KEY=${TOKEN_ENCRYPTION_KEY}" \
  --set-env-vars "GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" \
  --set-env-vars "GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}" \
  --set-env-vars "LOG_LEVEL=INFO"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID \
  --format="value(status.url)")
echo "Backend URL: $BACKEND_URL"

# Update backend with correct URLs
gcloud run services update $BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID \
  --update-env-vars "FRONTEND_URL=${BACKEND_URL}" \
  --update-env-vars "GOOGLE_REDIRECT_URI=${BACKEND_URL}/api/oauth/google/callback" \
  --update-env-vars "META_REDIRECT_URI=${BACKEND_URL}/api/oauth/meta/callback" \
  --update-env-vars "TWITTER_REDIRECT_URI=${BACKEND_URL}/api/oauth/twitter/callback" \
  --update-env-vars "LINKEDIN_REDIRECT_URI=${BACKEND_URL}/api/oauth/linkedin/callback"

# 4. Build and deploy frontend
echo ""
echo ">>> Building & deploying frontend..."
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE \
  --project=$PROJECT_ID \
  --timeout=900 \
  -f Dockerfile.frontend \
  --substitutions="_NEXT_PUBLIC_API_URL=${BACKEND_URL}"

# Actually build with docker build args
gcloud builds submit \
  --config /dev/stdin \
  --project=$PROJECT_ID \
  --timeout=900 <<CLOUDBUILD
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-f'
      - 'Dockerfile.frontend'
      - '--build-arg'
      - 'NEXT_PUBLIC_API_URL=${BACKEND_URL}'
      - '-t'
      - 'gcr.io/$PROJECT_ID/$FRONTEND_SERVICE'
      - '.'
images:
  - 'gcr.io/$PROJECT_ID/$FRONTEND_SERVICE'
CLOUDBUILD

gcloud run deploy $FRONTEND_SERVICE \
  --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "NEXT_PUBLIC_API_URL=${BACKEND_URL}"

FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID \
  --format="value(status.url)")

# Update backend FRONTEND_URL to point to actual frontend
gcloud run services update $BACKEND_SERVICE \
  --platform managed \
  --region $REGION \
  --project=$PROJECT_ID \
  --update-env-vars "FRONTEND_URL=${FRONTEND_URL}"

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo ""
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "Share this URL with your users: $FRONTEND_URL"
echo ""
echo "IMPORTANT: Update your Google OAuth redirect URI in Google Cloud Console to:"
echo "  ${BACKEND_URL}/api/oauth/google/callback"
