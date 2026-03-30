# AllergyChecker

A web app that checks a product's ingredient label for allergens. Upload a photo of the label, enter your allergens, and it tells you what to watch out for.

## How it works

1. You upload a photo of a product's ingredients label and provide a list of allergens to check for.
2. The backend OCRs the label image using **Gemini 2.5 Flash**.
3. Gemini then analyzes the extracted text with food-allergy-aware reasoning — handling synonyms (e.g. "maize" = corn), derivatives, and ambiguous cases.
4. The response tells you which allergens were matched, which weren't, and any nuanced notes.

## Stack

- **Backend** — FastAPI on Google Cloud Run
- **Frontend** — Static HTML/CSS/JS hosted on Firebase Hosting
- **AI** — Google Gemini 2.5 Flash (OCR + allergen analysis)

## API

**`POST /check`** — `multipart/form-data`

| Field         | Type | Description |
|---------------|------|-------------|
| `ingredients` | text | JSON array `["milk","eggs"]` or comma-separated string |
| `image`       | file | JPG or PNG of the ingredients label |

**Response:**
```json
{
  "matched":   ["milk"],
  "unmatched": ["eggs"],
  "ocr_text":  "...raw OCR text...",
  "notes":     "...explanation of any ambiguous matches..."
}
```

**`GET /health`** — returns `{"status": "ok"}`

## Deploy

### Backend (Cloud Run)

```powershell
$env:GEMINI_API_KEY = "AIza..."
.\deploy_backend.ps1
```

Edit `$PROJECT_ID`, `$REGION`, and `$SERVICE` at the top of `deploy_backend.ps1` before first use.

### Frontend (Firebase Hosting)

```powershell
.\deploy_frontend.ps1
```

### Local development

```bash
cd backend
pip install -r requirements.txt
GEMINI_API_KEY=your_key uvicorn main:app --reload --port 8080
```

## Design notes

- The image is processed entirely in-memory — never written to disk.
- `GEMINI_API_KEY` is injected via Cloud Run environment variable, never baked into the image.
- Matching falls back to whole-word regex (`\b...\b`) if the LLM analysis fails.
