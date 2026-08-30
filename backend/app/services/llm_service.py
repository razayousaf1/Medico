"""
LLM service — talks to the Google Gemini API for prescription understanding.

Responsibilities
----------------
1. `extract_prescription` — takes noisy OCR text and returns a structured
   JSON analysis (corrected medicine names, generics, strengths, frequency
   interpretations, alternative brands, summary, warnings).
2. `suggest_alternatives` — for medicines that were NOT found in the
   pharmacy database, proposes alternative brands commonly available in
   Pakistan.

Both methods ask the model for JSON only and parse defensively
(markdown fences stripped, substring extraction, one retry on bad JSON).
"""

import base64
import json
import logging
import re
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised for any Gemini API / parsing failure."""


EXTRACTION_SYSTEM_PROMPT = """You are the prescription analysis engine of Medico, a medicine availability platform used in Pakistan. You have the expertise of a senior clinical pharmacist.

You receive raw OCR text extracted from a prescription image. OCR output is noisy: words can be broken or merged, letters misrecognised (rn/m, l/I, 0/O, cl/d), spacing lost and lines shuffled.

Your tasks:
1. Silently correct OCR mistakes and reconstruct the intended prescription content.
2. Identify EVERY medicine prescribed: the brand name as written (corrected) and its generic name / active composition.
3. Extract the strength (e.g. "625 mg"), the form (tablet / capsule / syrup / inhaler / injection / cream / drops) and the duration if stated.
4. Interpret the dosage frequency, including South Asian prescription abbreviations:
   SOS = when needed, OD = once daily, BD = twice daily, TDS = three times daily,
   QID = four times daily, HS = at bedtime, PRN = as needed, AC = before meals,
   PC = after meals, STAT = immediately, and numeric patterns such as
   1-0-1 (morning and night), 1-1-1 (morning, afternoon, night), 0-0-1 (night only), 2-2-2.
5. Suggest up to 4 alternative brands of the same generic that are commonly stocked in Pakistani pharmacies (manufacturers such as GSK, Getz, Hilton, Abbott, Searle, Highnoon, Martin Dow, Sami, Cipla, Barrett Hodgson, Novartis).
6. Write a short patient-friendly summary (2-4 sentences) of what this prescription treats and how it should be taken.
7. List safety warnings you notice (duplicate therapy, unusual dose, controlled medicine, missing duration).

Rules:
- NEVER invent medicines that are not supported by the OCR text.
- If a field is unknown or illegible, use null.
- confidence: a 0-1 score of how certain you are about each medicine (based on OCR quality and clarity).
- overall_confidence: a 0-1 score for the whole analysis.
- Respond with ONLY a valid JSON object. No markdown, no code fences, no commentary.

JSON schema:
{
  "patient_name": string | null,
  "doctor_name": string | null,
  "prescribed_date": string | null,
  "summary": string,
  "overall_confidence": number,
  "warnings": string[],
  "medicines": [
    {
      "name": string,
      "generic_name": string | null,
      "strength": string | null,
      "form": string | null,
      "frequency_raw": string | null,
      "frequency_interpretation": string | null,
      "times_per_day": integer | null,
      "abbreviation_meanings": [{"abbreviation": string, "meaning": string}],
      "duration": string | null,
      "instructions": string | null,
      "confidence": number,
      "alternative_brands": string[]
    }
  ]
}"""

ALTERNATIVES_SYSTEM_PROMPT = """You are a Pakistani pharmacy expert assisting the Medico platform. You know which brands local pharmacies in Pakistan stock, from manufacturers such as GSK, Getz, Hilton, Abbott, Searle, Highnoon, Martin Dow, Sami, Cipla, Barrett Hodgson and Novartis.

You will receive a list of medicines that were NOT found in the platform's pharmacy database. For each one, suggest up to 4 alternative BRAND names for the same generic composition and strength that are commonly available in Pakistan.

Respond with ONLY a valid JSON object, no markdown:
{"alternatives": [{"index": <the medicine index>, "brands": ["Brand 1", "Brand 2"]}]}"""


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMService:
    """Async client around the Gemini OpenAI-compatible chat completions API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.gemini_model
        self._client = httpx.AsyncClient(
            base_url=settings.gemini_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.gemini_api_key}"},
            timeout=httpx.Timeout(120.0, connect=15.0),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract_prescription(self, ocr_text: str) -> dict[str, Any]:
        """OCR text -> structured prescription analysis dict."""
        user_prompt = (
            f"OCR TEXT extracted from the prescription:\n"
            f'"""\n{ocr_text}\n"""\n\n'
            "Analyse this prescription now and respond with the JSON object only."
        )
        data = await self._chat_json(EXTRACTION_SYSTEM_PROMPT, user_prompt)

        if not isinstance(data, dict):
            raise LLMError("Gemini returned an unexpected JSON shape")
        data.setdefault("medicines", [])
        data.setdefault("warnings", [])
        data["medicines"] = [m for m in data["medicines"] if isinstance(m, dict) and m.get("name")]
        return data

    async def extract_prescription_from_image(
        self, image_bytes: bytes, content_type: Optional[str] = None
    ) -> dict[str, Any]:
        """Image bytes -> structured prescription analysis dict (no OCR needed)."""
        mime = (content_type or "image/jpeg").split(";")[0].strip()
        if mime not in ("image/jpeg", "image/jpg", "image/png", "image/webp"):
            mime = "image/jpeg"
        b64 = base64.b64encode(image_bytes).decode()

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                    {
                        "type": "text",
                        "text": "Analyse this prescription image and respond with the JSON object only.",
                    },
                ],
            },
        ]

        last_parse_error: Optional[ValueError] = None
        for _attempt in range(2):
            content = await self._complete(messages, json_mode=True)
            try:
                data = self._parse_json(content)
                break
            except ValueError as exc:
                last_parse_error = exc
                logger.warning("Gemini vision returned invalid JSON, retrying: %s", exc)
                messages = messages[:2] + [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": (
                            "Your previous reply was not valid JSON "
                            f"(error: {exc}). Respond again with ONLY the JSON object."
                        ),
                    },
                ]
        else:
            raise LLMError(f"Gemini vision returned invalid JSON after retry: {last_parse_error}")

        if not isinstance(data, dict):
            raise LLMError("Gemini returned an unexpected JSON shape")
        data.setdefault("medicines", [])
        data.setdefault("warnings", [])
        data["medicines"] = [m for m in data["medicines"] if isinstance(m, dict) and m.get("name")]
        return data

    async def suggest_alternatives(
        self, unavailable: list[dict[str, Any]]
    ) -> dict[int, list[str]]:
        """Ask Gemini for alternative Pakistani brands.

        `unavailable` items look like {"index": 0, "name": ..., "generic": ..., "strength": ...}.
        Returns {index: [brands...]}.
        """
        if not unavailable:
            return {}

        lines = []
        for item in unavailable:
            detail = " ".join(
                part for part in [item.get("name"), item.get("strength"), item.get("generic")] if part
            )
            lines.append(f'- index {item["index"]}: {detail} — not found in stock')

        user_prompt = (
            "The following prescribed medicines were NOT found in our pharmacy database:\n"
            + "\n".join(lines)
            + "\n\nSuggest alternative brands for each. Respond with the JSON object only."
        )
        data = await self._chat_json(ALTERNATIVES_SYSTEM_PROMPT, user_prompt)

        result: dict[int, list[str]] = {}
        for entry in data.get("alternatives", []):
            if not isinstance(entry, dict):
                continue
            try:
                index = int(entry.get("index"))
            except (TypeError, ValueError):
                continue
            brands = [str(b).strip() for b in entry.get("brands", []) if str(b).strip()]
            if brands:
                result[index] = brands[:4]
        return result

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Low-level chat helpers
    # ------------------------------------------------------------------

    async def _chat_json(self, system: str, user: str) -> Any:
        """Send a chat completion, parse the reply as JSON, retry once on bad JSON."""
        settings = get_settings()
        if not settings.gemini_configured:
            raise LLMError(
                "GEMINI_API_KEY is not configured on the backend. "
                "Add your Gemini API key to backend/.env (see .env.example)."
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        last_parse_error: Optional[ValueError] = None
        for _attempt in range(2):
            content = await self._complete(messages, json_mode=True)
            try:
                return self._parse_json(content)
            except ValueError as exc:
                last_parse_error = exc
                logger.warning("Gemini returned invalid JSON, retrying: %s", exc)
                messages = messages[:2] + [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": (
                            "Your previous reply was not valid JSON "
                            f"(error: {exc}). Respond again with ONLY the JSON object."
                        ),
                    },
                ]

        raise LLMError(f"Gemini returned invalid JSON after retry: {last_parse_error}")

    async def _complete(self, messages: list[dict[str, str]], json_mode: bool) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4000,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.post("/chat/completions", json=payload)
        except httpx.TimeoutException as exc:
            raise LLMError("Gemini API timed out. Please try again.") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not reach the Gemini API: {exc}") from exc

        # Some deployments reject response_format — retry once without it
        if response.status_code == 400 and "response_format" in response.text:
            payload.pop("response_format", None)
            try:
                response = await self._client.post("/chat/completions", json=payload)
            except httpx.HTTPError as exc:
                raise LLMError(f"Could not reach the Gemini API: {exc}") from exc

        if response.status_code == 401:
            raise LLMError("Gemini API rejected the API key. Check GEMINI_API_KEY in backend/.env.")
        if response.status_code == 404:
            raise LLMError(
                f"Model '{self._model}' was not found. Update GEMINI_MODEL in backend/.env."
            )
        if response.status_code == 429:
            raise LLMError("Gemini API rate limit reached. Please wait a moment and retry.")
        if response.status_code >= 400:
            raise LLMError(
                f"Gemini API error {response.status_code}: {response.text[:200]}"
            )

        try:
            return response.json()["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("Gemini API returned an unexpected response shape") from exc

    @staticmethod
    def _parse_json(content: str) -> Any:
        """Parse model output as JSON, tolerating code fences and prose wrappers."""
        text = (content or "").strip()
        if not text:
            raise ValueError("empty response")

        cleaned = _FENCE_RE.sub("", text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fall back to the outermost JSON object in the reply
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            candidate = cleaned[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise ValueError(str(exc)) from exc

        raise ValueError("no JSON object found in the reply")
