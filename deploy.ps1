# ---------------------------------------------------------------------------
# Deploy AllergyChecker — backend (Cloud Run) + frontend (Firebase Hosting)
#
# Usage:
#   .\deploy.ps1               # deploy both
#   .\deploy.ps1 -BackendOnly  # deploy backend only
#   .\deploy.ps1 -FrontendOnly # deploy frontend only
#
# Prerequisites:
#   Backend:   gcloud CLI installed & authenticated; GEMINI_API_KEY set;
#              PROJECT_ID / REGION / SERVICE configured in deploy_backend.ps1
#   Frontend:  Firebase CLI installed (npm install -g firebase-tools);
#              firebase login done; project ID set in .firebaserc
#              IMPORTANT: update BACKEND_URL in frontend/index.html first
# ---------------------------------------------------------------------------

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"

if (-not $FrontendOnly) {
    Write-Host ""
    Write-Host "━━━  Backend (Cloud Run)  ━━━" -ForegroundColor Cyan
    & "$PSScriptRoot\deploy_backend.ps1"
    if ($LASTEXITCODE -ne 0) { Write-Error "Backend deploy failed."; exit 1 }
}

if (-not $BackendOnly) {
    Write-Host ""
    Write-Host "━━━  Frontend (Firebase Hosting)  ━━━" -ForegroundColor Cyan
    & "$PSScriptRoot\deploy_frontend.ps1"
    if ($LASTEXITCODE -ne 0) { Write-Error "Frontend deploy failed."; exit 1 }
}

Write-Host ""
Write-Host "==> All done!" -ForegroundColor Green
