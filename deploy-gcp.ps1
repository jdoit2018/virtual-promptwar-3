# deploy-gcp.ps1
# PowerShell Deployment script for the AuraCarbon platform on Google Cloud Platform.

$ErrorActionPreference = "Stop"

# Configuration
$GCP_PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
if (-not $GCP_PROJECT_ID) {
    $GCP_PROJECT_ID = "your-gcp-project-id"
}
$GCP_REGION = "us-central1"
$ARTIFACT_REGISTRY_REPO = "auracarbon-repo"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Deploying AuraCarbon to Google Cloud Run" -ForegroundColor Cyan
Write-Host "Project ID: $GCP_PROJECT_ID" -ForegroundColor Cyan
Write-Host "Region:     $GCP_REGION" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# 1. Set Google Cloud project
Write-Host "Setting gcloud project..."
gcloud config set project $GCP_PROJECT_ID

# 2. Enable Google Cloud APIs
Write-Host "Enabling required GCP APIs..."
gcloud services enable `
    run.googleapis.com `
    sqladmin.googleapis.com `
    secretmanager.googleapis.com `
    artifactregistry.googleapis.com `
    cloudscheduler.googleapis.com `
    cloudtasks.googleapis.com

# 3. Create Artifact Registry repository if it doesn't exist
$repoExists = $false
try {
    gcloud artifacts repositories describe $ARTIFACT_REGISTRY_REPO --location=$GCP_REGION | Out-Null
    $repoExists = $true
} catch {
    $repoExists = $false
}

if (-not $repoExists) {
    Write-Host "Creating Artifact Registry repository..."
    gcloud artifacts repositories create $ARTIFACT_REGISTRY_REPO `
        --repository-format=docker `
        --location=$GCP_REGION `
        --description="Docker repository for AuraCarbon services"
}

# 4. Build and push Backend API Docker Image
Write-Host "Building and pushing Backend API Docker Image..."
$API_IMAGE_TAG = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/api:latest"
gcloud builds submit --tag $API_IMAGE_TAG ./apps/api

# 5. Build and push Frontend Next.js Docker Image
Write-Host "Building and pushing Frontend Next.js Docker Image..."
$WEB_IMAGE_TAG = "${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/web:latest"
gcloud builds submit --tag $WEB_IMAGE_TAG ./apps/web

# 6. Deploy Backend API to Cloud Run
Write-Host "Deploying Backend API to Cloud Run..."
gcloud run deploy carbon-api `
    --image=$API_IMAGE_TAG `
    --region=$GCP_REGION `
    --platform=managed `
    --allow-unauthenticated `
    --set-env-vars="NODE_ENV=production"

# 7. Deploy Frontend Web App to Cloud Run
Write-Host "Deploying Frontend Web App to Cloud Run..."
gcloud run deploy carbon-web `
    --image=$WEB_IMAGE_TAG `
    --region=$GCP_REGION `
    --platform=managed `
    --allow-unauthenticated

Write-Host "=============================================" -ForegroundColor Green
Write-Host "Deployment scripts ran successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
