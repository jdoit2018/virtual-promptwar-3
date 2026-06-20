#!/usr/bin/env bash
# deploy-gcp.sh
# Deployment script for the AuraCarbon platform on Google Cloud Platform.

set -eo pipefail

# Configuration
GCP_PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-gcp-project-id}"
GCP_REGION="${GCP_REGION:-us-central1}"
ARTIFACT_REGISTRY_REPO="auracarbon-repo"

echo "============================================="
echo "  Deploying AuraCarbon to Google Cloud Run"
echo "============================================="
echo "Project ID: ${GCP_PROJECT_ID}"
echo "Region:     ${GCP_REGION}"
echo "============================================="

# 1. Set Google Cloud project
gcloud config set project "${GCP_PROJECT_ID}"

# 2. Enable Google Cloud APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudscheduler.googleapis.com \
    cloudtasks.googleapis.com

# 3. Create Artifact Registry repository if it doesn't exist
if ! gcloud artifacts repositories describe "${ARTIFACT_REGISTRY_REPO}" --location="${GCP_REGION}" &>/dev/null; then
    echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create "${ARTIFACT_REGISTRY_REPO}" \
        --repository-format=docker \
        --location="${GCP_REGION}" \
        --description="Docker repository for AuraCarbon services"
fi

# 4. Build and push Backend API Docker Image
echo "Building and pushing Backend API Docker Image..."
API_IMAGE_TAG="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/api:latest"
gcloud builds submit --tag "${API_IMAGE_TAG}" ./apps/api

# 5. Build and push Frontend Next.js Docker Image
echo "Building and pushing Frontend Next.js Docker Image..."
WEB_IMAGE_TAG="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/web:latest"
gcloud builds submit --tag "${WEB_IMAGE_TAG}" ./apps/web

# 6. Deploy Backend API to Cloud Run
echo "Deploying Backend API to Cloud Run..."
gcloud run deploy carbon-api \
    --image="${API_IMAGE_TAG}" \
    --region="${GCP_REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="NODE_ENV=production"

# 7. Deploy Frontend Web App to Cloud Run
echo "Deploying Frontend Web App to Cloud Run..."
gcloud run deploy carbon-web \
    --image="${WEB_IMAGE_TAG}" \
    --region="${GCP_REGION}" \
    --platform=managed \
    --allow-unauthenticated

echo "============================================="
echo "Deployment scripts ran successfully!"
echo "============================================="
