# ---------------------------------------------------------------------------
# Deploy frontend to Firebase Hosting
# Prerequisites:
#   1. Firebase CLI installed: npm install -g firebase-tools
#   2. Authenticated:          firebase login
#   3. Project ID set in:      .firebaserc  (default project)
# ---------------------------------------------------------------------------

Write-Host "==> Deploying frontend to Firebase Hosting..." -ForegroundColor Cyan
firebase deploy --only hosting

if ($LASTEXITCODE -ne 0) { Write-Error "Firebase deploy failed."; exit 1 }

Write-Host "==> Frontend deployed. Visit your Firebase Hosting URL above." -ForegroundColor Green
