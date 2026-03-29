# ---------------------------------------------------------------------------
# Load .env file if present
# ---------------------------------------------------------------------------
if (Test-Path .env) {
    Get-Content .env | Where-Object { $_ -match '^\s*([^#][^=]+)=(.*)$' } | ForEach-Object {
        $name, $value = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
    }
}

# ---------------------------------------------------------------------------
# Configuration — edit these before first deploy
# ---------------------------------------------------------------------------
$PROJECT_ID  = "rex-allergy-checker"
$REGION      = "us-central1"
$SERVICE     = "allergy-checker"
$IMAGE       = "gcr.io/$PROJECT_ID/$SERVICE"

# GEMINI_API_KEY must be set in your environment before running this script:
#   $env:GEMINI_API_KEY = "AIza..."
# ---------------------------------------------------------------------------
if (-not $env:GEMINI_API_KEY) {
    Write-Error "GEMINI_API_KEY environment variable is not set."
    exit 1
}

Write-Host "==> Building and pushing image via Cloud Build..." -ForegroundColor Cyan
gcloud builds submit ./backend `
    --tag $IMAGE `
    --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) { Write-Error "Build failed."; exit 1 }

Write-Host "==> Deploying to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $SERVICE `
    --image $IMAGE `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --timeout 60 `
    --set-env-vars "GEMINI_API_KEY=$env:GEMINI_API_KEY" `
    --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) { Write-Error "Deploy failed."; exit 1 }

Write-Host "==> Done. Service URL:" -ForegroundColor Green
gcloud run services describe $SERVICE `
    --platform managed `
    --region $REGION `
    --project $PROJECT_ID `
    --format "value(status.url)"
