# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AllergyChecker is a Google Cloud Run service that accepts an ingredients list and a JPG of a product label, OCRs the label via Gemini, and returns which ingredients from the list appear in the label text.

## Structure

```
backend/
  main.py           # FastAPI app — single POST /check endpoint + GET /health
  requirements.txt
  Dockerfile
  .dockerignore
deploy_backend.ps1  # Build (via Cloud Build) and deploy to Cloud Run
```

## Development Commands

```bash
# Install dependencies locally
cd backend
pip install -r requirements.txt

# Run locally (requires GEMINI_API_KEY in environment)
uvicorn main:app --reload --port 8080
```

## Deploy

```powershell
# Set your key, then run the deploy script
$env:GEMINI_API_KEY = "AIza..."
.\deploy_backend.ps1
```

Edit the `$PROJECT_ID`, `$REGION`, and `$SERVICE` variables at the top of `deploy_backend.ps1` before first use.

## API

**POST /check** — multipart/form-data

| Field         | Type | Description |
|---------------|------|-------------|
| `ingredients` | text | JSON array `["milk","eggs"]` or comma-separated string |
| `image`       | file | JPG/PNG of the ingredients label |

Response:
```json
{
  "matched":   ["milk"],
  "unmatched": ["eggs"],
  "ocr_text":  "...raw text from Gemini..."
}
```

## Key Design Decisions

- **Matching** uses whole-word regex (`\b...\b`) so e.g. `"oil"` does not match `"foil"`.
- The image is kept entirely in-memory (`io.BytesIO`) — never written to disk.
- `GEMINI_API_KEY` is injected via Cloud Run environment variable; it is never baked into the image.
- Memory is set to **1 Gi** in the deploy script to comfortably handle large JPGs in-memory.
