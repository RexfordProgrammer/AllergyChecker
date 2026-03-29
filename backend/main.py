import os
import io
import json
import re

import google.generativeai as genai
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

app = FastAPI()

# Allow requests from Firebase Hosting (and local dev).
# Restrict allow_origins to your Firebase domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_model = genai.GenerativeModel("gemini-2.5-flash")

_OCR_PROMPT = (
    "Extract every word of text visible in this image exactly as written. "
    "This is likely a food product ingredients label. "
    "Return only the raw extracted text with no commentary."
)

# Second-pass prompt: LLM does the actual matching with common-sense reasoning.
_ANALYSIS_PROMPT = """\
You are a food allergy expert analyzing a product's ingredient label.

OCR text extracted from the label:
---
{ocr_text}
---

Check whether any of these allergen ingredients/derivatives appear in the label:
{ingredients}

Rules:
- Base your answer solely on what appears in the OCR text above.
- Apply common-sense reasoning. If the label explicitly states an ingredient is \
"derived from" or "made with" a NON-allergenic source (e.g. "xanthan gum (from \
sugarcane)"), do NOT flag it as a match for the allergen it commonly comes from.
- If the label states it IS "derived from" an allergenic source, DO flag it.
- Consider synonyms: "maize" = corn, "lactulose" is dairy-derived, etc.
- Put any nuanced or ambiguous findings in the "notes" field.

Respond ONLY with valid JSON — no markdown, no backticks, no extra text:
{{"matched": ["..."], "unmatched": ["..."], "notes": "explanation of ambiguous cases, or empty string"}}\
"""


def _parse_ingredients(raw: str) -> list[str]:
    """Accept either a JSON array or a comma-separated string."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(i).strip() for i in parsed if str(i).strip()]
    except (json.JSONDecodeError, ValueError):
        pass
    return [i.strip() for i in raw.split(",") if i.strip()]


def _regex_match(ingredient: str, ocr_text: str) -> bool:
    """Case-insensitive whole-word fallback match."""
    pattern = r"\b" + re.escape(ingredient.lower()) + r"\b"
    return bool(re.search(pattern, ocr_text.lower()))


@app.post("/check")
async def check_ingredients(
    ingredients: str = Form(
        ...,
        description="JSON array or comma-separated list of ingredients to search for.",
    ),
    image: UploadFile = File(..., description="JPG/PNG of the ingredients label."),
):
    ingredient_list = _parse_ingredients(ingredients)
    if not ingredient_list:
        raise HTTPException(status_code=422, detail="No ingredients provided.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=422, detail="Empty image file.")

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise HTTPException(status_code=422, detail="Could not decode image.")

    # Step 1: OCR
    try:
        ocr_response = _model.generate_content([_OCR_PROMPT, pil_image])
        ocr_text = ocr_response.text or ""
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini OCR error: {exc}")

    # Step 2: LLM analysis — smarter matching with common-sense reasoning.
    analysis_prompt = _ANALYSIS_PROMPT.format(
        ocr_text=ocr_text,
        ingredients="\n".join(f"- {i}" for i in ingredient_list),
    )
    try:
        analysis_response = _model.generate_content(analysis_prompt)
        analysis_text = (analysis_response.text or "").strip()
        # Strip markdown code fences in case Gemini wraps the JSON.
        if analysis_text.startswith("```"):
            analysis_text = re.sub(r"^```[a-z]*\n?", "", analysis_text)
            analysis_text = re.sub(r"\n?```$", "", analysis_text.strip())
        result = json.loads(analysis_text)
        matched = result.get("matched", [])
        unmatched = result.get("unmatched", [])
        notes = result.get("notes", "")
    except Exception:
        # Fallback to simple regex if the LLM analysis fails.
        matched = [i for i in ingredient_list if _regex_match(i, ocr_text)]
        unmatched = [i for i in ingredient_list if i not in matched]
        notes = "Used fallback regex matching — LLM analysis was unavailable."

    return JSONResponse(
        {
            "matched": matched,
            "unmatched": unmatched,
            "ocr_text": ocr_text,
            "notes": notes,
        }
    )


@app.get("/health")
def health():
    return {"status": "ok"}
