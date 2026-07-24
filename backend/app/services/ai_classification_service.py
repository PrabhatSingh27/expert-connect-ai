"""Fault-tolerant multimodal issue classification for persisted uploads."""

import base64
import json
import logging
import mimetypes
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)
BACKEND_ROOT = Path(__file__).resolve().parents[2]
MAX_VIDEO_FRAMES = 5

# Canonical routing contract. Categories and expert titles are intentionally
# kept verbatim so every model/provider produces the same backend value.
SERVICE_CATALOG = (
    ("⚡ Electrical", "Electrician", ("fan", "switch", "power outage", "wiring", "mcb", "socket", "spark", "circuit", "electric")),
    ("❄️ HVAC & Cooling", "AC/HVAC Technician", ("ac", "air conditioner", "cooler", "thermostat", "not cooling")),
    ("🧊 Home Appliances", "Appliance Technician", ("refrigerator", "fridge", "washing machine", "microwave", "dishwasher", "mixer", "induction cooktop")),
    ("🚰 Plumbing", "Plumber", ("tap", "drain", "pipe", "leak", "water heater", "clog", "plumbing")),
    ("🏠 Carpentry", "Carpenter", ("door lock", "window", "furniture", "hinge", "cabinet", "carpentry")),
    ("🎨 Painting & Wall Repair", "Painter/Mason", ("peeling paint", "damp wall", "ceiling damage", "paint", "wall crack")),
    ("🧱 Masonry & Flooring", "Mason", ("broken tile", "floor crack", "concrete", "flooring", "tile", "masonry")),
    ("🔐 Security Systems", "Security Technician", ("cctv", "smart lock", "doorbell", "alarm system", "security camera")),
    ("📡 Internet & Networking", "Network Technician", ("wi-fi", "wifi", "router", "lan", "internet", "network")),
    ("💻 Computers & Laptops", "Computer Technician", ("laptop", "slow pc", "operating system", "os installation", "printer", "computer")),
    ("📱 Mobile Devices", "Mobile Repair Expert", ("mobile", "phone", "screen replacement", "charging", "battery")),
    ("📺 Consumer Electronics", "Electronics Technician", ("tv", "speaker", "home theater", "gaming console", "electronics")),
    ("🌞 Solar & Power Backup", "Solar/Power Technician", ("solar", "inverter", "ups", "power backup", "battery backup")),
    ("🔥 Gas & Kitchen Equipment", "Kitchen Appliance Technician", ("gas stove", "chimney", "exhaust fan", "gas leak", "kitchen equipment")),
    ("🌳 Outdoor & Garden", "Garden Equipment Technician", ("water pump", "lawn", "irrigation", "garden")),
    ("🚗 Automobile", "Auto Mechanic", ("car", "vehicle", "puncture", "car battery", "servicing", "won't start")),
    ("🧹 Cleaning Services", "Cleaning Professional", ("deep cleaning", "sofa cleaning", "cleaning", "cleanup")),
    ("🐜 Pest Control", "Pest Control Expert", ("termite", "cockroach", "rodent", "mosquito", "pest")),
    ("🛡️ Pest & Hygiene", "Hygiene Specialist", ("sanitization", "mold removal", "mould", "hygiene")),
    ("❓ Other", "General Support", ()),
)


def _catalog_entry(value: str | None) -> tuple[str, str]:
    """Map model/provider variations to one exact catalog entry."""
    normalized = (value or "").casefold()
    for category, expert, _ in SERVICE_CATALOG:
        category_name = category.split(" ", 1)[-1].casefold()
        if normalized and (normalized == category.casefold() or category_name in normalized or expert.casefold() in normalized):
            return category, expert
    return SERVICE_CATALOG[-1][:2]


def _catalog_entry_for_text(text: str) -> tuple[str, str]:
    normalized = text.casefold()
    for category, expert, keywords in SERVICE_CATALOG[:-1]:
        if any(re.search(rf"\b{re.escape(keyword)}\b", normalized) for keyword in keywords):
            return category, expert
    return SERVICE_CATALOG[-1][:2]


def _resolve_local_path(saved_path: str | None) -> Path | None:
    if not saved_path or saved_path.startswith(("http://", "https://")):
        return None
    path = Path(saved_path)
    existing_path = next((candidate for candidate in (path, BACKEND_ROOT / path) if candidate.is_file()), None)
    if existing_path is not None:
        return existing_path

    # Preserve multimodal classification for issue records created before the
    # media folders were consolidated under uploads/issue_media.
    media_folder = path.parent.name.lower()
    media_folders = {"images": "images", "videos": "videos", "audio": "audios", "audios": "audios"}
    if media_folder in media_folders:
        for migrated_path in (
            BACKEND_ROOT / "uploads" / "users" / "issues" / media_folders[media_folder] / path.name,
            BACKEND_ROOT / "uploads" / "issue_media" / media_folder / path.name,
        ):
            if migrated_path.is_file():
                return migrated_path
    return None


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
        "You are a multimodal service-routing engine. Weigh the text, optional audio transcription, "
        "and supplied images/video frames together; clear visual evidence overrides a vague text description. "
        "Choose exactly one primary category and expert from this catalog: "
        + json.dumps(
            [{"category": category, "assigned_expert": expert} for category, expert, _ in SERVICE_CATALOG],
            ensure_ascii=False,
        )
        + ". Return ONLY valid JSON with: thought_process (a concise routing summary, not hidden reasoning), "
        "category, assigned_expert, confidence_score (0.0-1.0), reasoning, problem_type, priority, urgency, "
        "required_skills, ai_explanation. priority and urgency must each be low, medium, high, or critical. "
        "Issue payload: " + json.dumps(payload, ensure_ascii=True)
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
    category, assigned_expert = _catalog_entry(
        str(data.get("category") or data.get("category_prediction") or data.get("assigned_expert") or "")
    )
    reasoning = str(data.get("reasoning") or data.get("ai_explanation") or data.get("explanation") or
                    f"Classified as {category} based on the supplied issue evidence.")
    return {"problem_type": str(data.get("problem_type") or data.get("problem") or "General"),
            "category": category, "assigned_expert": assigned_expert,
            "thought_process": str(data.get("thought_process") or f"Matched the reported symptoms to {category}."),
            "reasoning": reasoning, "priority": priority, "urgency": urgency, "required_skills": [assigned_expert],
            "confidence_score": max(0.0, min(confidence, 1.0)),
            "ai_explanation": reasoning}


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
    category, assigned_expert = _catalog_entry_for_text(text)
    urgency = ("critical" if any(w in text for w in ("fire", "sparking", "shock", "burst", "flood")) else
               "high" if any(w in text for w in ("urgent", "tonight", "immediately", "emergency", "leaking", "not working")) else
               "medium" if any(w in text for w in ("soon", "today", "tomorrow")) else "low")
    confidence = 0.72 if category != "❓ Other" else 0.45
    reasoning = f"Reported symptoms best match {category}; urgency is {urgency}."
    return {"problem_type": category.split(" ", 1)[-1], "category": category,
            "assigned_expert": assigned_expert,
            "thought_process": f"Matched the text symptoms to {category}.",
            "reasoning": reasoning, "priority": urgency, "urgency": urgency,
            "required_skills": [assigned_expert], "confidence_score": confidence,
            "ai_explanation": reasoning}


def classify_issue_content(issue) -> dict:
    """Classify an already-persisted issue; all media work is optional and best-effort."""
    return _classify_with_openai(issue) or _classify_with_gemini(issue) or _keyword_classification(issue)
