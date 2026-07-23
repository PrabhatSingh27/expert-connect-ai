"""Fault-tolerant multimodal issue classification for persisted uploads."""

import base64
import json
import logging
import mimetypes
import os
from pathlib import Path

logger = logging.getLogger(__name__)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
MAX_VIDEO_FRAMES = 5


def _resolve_local_path(saved_path: str | None) -> Path | None:
    if not saved_path or saved_path.startswith(("http://", "https://")):
        return None
    path = Path(saved_path)
    return next((candidate for candidate in (path, BACKEND_ROOT / path) if candidate.is_file()), None)


def _attachment_metadata(issue) -> list[dict]:
    return [{"file_type": a.file_type, "content_type": a.content_type,
             "original_filename": a.original_filename, "size_bytes": a.size_bytes}
            for a in getattr(issue, "attachments", [])]


def _media_paths(issue, file_type: str) -> list[str]:
    """Read both legacy issue columns and the attachment records."""
    paths = [getattr(issue, f"{file_type}_path", None)]
    paths.extend(a.file_url for a in (getattr(issue, "attachments", []) or [])
                 if getattr(a, "file_type", None) == file_type and getattr(a, "file_url", None))
    return list(dict.fromkeys(path for path in paths if path))


def encode_image_as_data_url(image_path: str) -> str | None:
    """Base64-encode a saved image for a vision-capable LLM."""
    path = _resolve_local_path(image_path)
    if path is None:
        return None
    try:
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    except (OSError, ValueError) as error:
        logger.warning("Skipping unreadable image during classification: %s", error)
        return None


def extract_video_keyframes_as_data_urls(video_path: str, max_frames: int = MAX_VIDEO_FRAMES) -> list[str]:
    """Extract at most five evenly-spaced, in-memory JPEG frames from a video."""
    path = _resolve_local_path(video_path)
    if path is None or max_frames < 1:
        return []
    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV is unavailable; classifying the video issue from text only")
        return []
    capture = None
    try:
        capture = cv2.VideoCapture(str(path))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count <= 0:
            return []
        sample_count = min(max_frames, frame_count)
        positions = [round((frame_count - 1) * (i + 1) / (sample_count + 1)) for i in range(sample_count)]
        frames = []
        for position in dict.fromkeys(positions):
            capture.set(cv2.CAP_PROP_POS_FRAMES, position)
            ok, frame = capture.read()
            ok, jpeg = (cv2.imencode(".jpg", frame) if ok else (False, None))
            if ok:
                frames.append("data:image/jpeg;base64," + base64.b64encode(jpeg.tobytes()).decode("ascii"))
        return frames
    except Exception as error:
        logger.warning("Skipping corrupt/unreadable video during classification: %s", error)
        return []
    finally:
        if capture is not None:
            capture.release()


def transcribe_audio_file(audio_path: str, client) -> str | None:
    """Transcribe a saved audio file. Errors deliberately do not escape."""
    path = _resolve_local_path(audio_path)
    if path is None:
        return None
    try:
        with path.open("rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"), file=audio_file)
        return (getattr(result, "text", "") or "").strip() or None
    except Exception as error:
        logger.warning("Audio transcription failed; using text-only classification: %s", error)
        return None


def _build_prompt(issue, transcript: str | None = None) -> str:
    payload = {"title": issue.title, "description": issue.description,
               "location": issue.location, "pin_code": issue.pin_code,
               "attachments": _attachment_metadata(issue)}
    if transcript:
        payload["audio_transcription"] = transcript
    return (
        "You are an AI triage assistant for a home-service platform. Use the issue text, "
        "optional audio transcription, and optional images/video frames. Return ONLY valid JSON "
        "with: problem_type, category, priority, urgency, required_skills, confidence_score, "
        "ai_explanation. priority and urgency must each be low, medium, high, or critical; "
        "confidence_score must be 0.0-1.0. Issue payload: " + json.dumps(payload, ensure_ascii=True)
    )


def _normalize_ai_response(data: dict) -> dict:
    urgency = str(data.get("urgency") or data.get("priority") or "low").lower()
    urgency = urgency if urgency in {"low", "medium", "high", "critical"} else "low"
    priority = str(data.get("priority") or urgency).lower()
    priority = priority if priority in {"low", "medium", "high", "critical"} else urgency
    try:
        confidence = float(data.get("confidence_score", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = confidence / 100 if confidence > 1 else confidence
    skills = data.get("required_skills") or data.get("suggested_expert_skills") or "general technician"
    if not isinstance(skills, list):
        skills = [skill.strip() for skill in str(skills).split(",") if skill.strip()]
    category = str(data.get("category") or data.get("category_prediction") or "General")
    return {"problem_type": str(data.get("problem_type") or data.get("problem") or "General"),
            "category": category, "priority": priority, "urgency": urgency, "required_skills": skills,
            "confidence_score": max(0.0, min(confidence, 1.0)),
            "ai_explanation": str(data.get("ai_explanation") or data.get("explanation") or
                                  f"Classified as {category} from the supplied issue details.")}


def _parse_json_response(content: str) -> dict | None:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start, end = content.find("{"), content.rfind("}")
        try:
            return json.loads(content[start:end + 1]) if start >= 0 and end > start else None
        except json.JSONDecodeError:
            return None


def _classify_with_openai(issue) -> dict | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=20.0, max_retries=1)
        transcript = next((text for path in _media_paths(issue, "audio")
                           if (text := transcribe_audio_file(path, client))), None)
        image_urls = [url for path in _media_paths(issue, "image")
                      if (url := encode_image_as_data_url(path))]
        for video_path in _media_paths(issue, "video"):
            image_urls.extend(extract_video_keyframes_as_data_urls(video_path))
        content = [{"type": "text", "text": _build_prompt(issue, transcript)}]
        content.extend({"type": "image_url", "image_url": {"url": url, "detail": "low"}}
                       for url in image_urls)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "system", "content": "Return only valid JSON for service issue classification."},
                      {"role": "user", "content": content}],
            response_format={"type": "json_object"}, temperature=0.2)
        parsed = _parse_json_response(response.choices[0].message.content or "{}")
        return _normalize_ai_response(parsed) if parsed else None
    except Exception as error:
        logger.warning("OpenAI classification failed; using fallback classification: %s", error)
        return None


def _classify_with_gemini(issue) -> dict | None:
    if not os.getenv("GEMINI_API_KEY"):
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        response = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash")).generate_content(_build_prompt(issue))
        parsed = _parse_json_response(getattr(response, "text", "") or "{}")
        return _normalize_ai_response(parsed) if parsed else None
    except Exception as error:
        logger.warning("Gemini classification failed; using fallback classification: %s", error)
        return None


def _keyword_classification(issue) -> dict:
    text = f"{issue.title} {issue.description}".lower()
    rules = [(("ac", "air conditioner"), "Air Conditioner", "Electrical", "electrician"),
             (("fan", "switch", "socket"), "Electrical Fixture", "Electrical", "electrician"),
             (("refrigerator", "washing machine"), "Home Appliance", "Electrical", "appliance technician"),
             (("tap", "pipe", "leak", "water tank", "water"), "Water Leakage", "Plumbing", "plumber"),
             (("door", "latch", "window", "furniture"), "Door or Furniture", "Carpentry", "carpenter"),
             (("tile", "floor", "wall crack", "cement"), "Civil Repair", "Civil", "mason"),
             (("tv", "speaker", "home theater"), "Electronics", "Electronics", "electronics technician")]
    problem_type, category, skill = next(((p, c, s) for keywords, p, c, s in rules if any(k in text for k in keywords)),
                                         ("General", "General", "general technician"))
    urgency = ("critical" if any(w in text for w in ("fire", "sparking", "shock", "burst", "flood")) else
               "high" if any(w in text for w in ("urgent", "tonight", "immediately", "emergency", "leaking", "not working")) else
               "medium" if any(w in text for w in ("soon", "today", "tomorrow")) else "low")
    return {"problem_type": problem_type, "category": category, "priority": urgency, "urgency": urgency,
            "required_skills": [skill], "confidence_score": 0.72 if category != "General" else 0.45,
            "ai_explanation": f"Classified as {category} from the issue text; urgency is {urgency}."}


def classify_issue_content(issue) -> dict:
    """Classify an already-persisted issue; all media work is optional and best-effort."""
    return _classify_with_openai(issue) or _classify_with_gemini(issue) or _keyword_classification(issue)
