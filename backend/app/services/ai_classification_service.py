import os
import json


AI_RESPONSE_KEYS = {
    "problem_type",
    "category",
    "priority",
    "urgency",
    "required_skills",
    "confidence_score",
    "ai_explanation",
}


def _attachment_metadata(issue) -> list[dict]:
    return [
        {
            "file_type": attachment.file_type,
            "content_type": attachment.content_type,
            "original_filename": attachment.original_filename,
            "size_bytes": attachment.size_bytes,
        }
        for attachment in getattr(issue, "attachments", [])
    ]


def _build_prompt(issue) -> str:
    payload = {
        "title": issue.title,
        "description": issue.description,
        "location": issue.location,
        "pin_code": issue.pin_code,
        "attachments": _attachment_metadata(issue),
    }

    return (
        "You are an AI triage assistant for a home-service expert matching platform. "
        "Run a 4-stage pipeline: problem detection, category mapping, urgency detection, "
        "and assignment payload generation. Return ONLY valid JSON with these keys: "
        "problem_type, category, urgency, required_skills, confidence_score, ai_explanation. "
        "urgency must be one of: low, medium, high, critical. "
        "confidence_score must be a number from 0.0 to 1.0. "
        f"Issue payload: {json.dumps(payload, ensure_ascii=True)}"
    )


def _normalize_ai_response(data: dict) -> dict:
    urgency = str(data.get("urgency") or data.get("priority") or "low").lower()
    if urgency not in {"low", "medium", "high", "critical"}:
        urgency = "low"

    confidence = data.get("confidence_score", 50.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.5
    if confidence > 1.0:
        confidence = confidence / 100.0
    confidence = max(0.0, min(confidence, 1.0))

    required_skills = data.get("required_skills") or data.get("suggested_expert_skills") or "general technician"
    if not isinstance(required_skills, list):
        required_skills = [skill.strip() for skill in str(required_skills).split(",") if skill.strip()]

    problem_type = str(data.get("problem_type") or data.get("problem") or data.get("appliance") or "General")
    category = str(data.get("category") or data.get("category_prediction") or "General")
    explanation = str(
        data.get("ai_explanation")
        or data.get("explanation")
        or f"Classified as {category} based on the provided issue details."
    )

    return {
        "problem_type": problem_type,
        "category": category,
        "priority": urgency,
        "urgency": urgency,
        "required_skills": required_skills,
        "confidence_score": confidence,
        "ai_explanation": explanation,
    }


def _parse_json_response(content: str) -> dict | None:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            return None


def _keyword_classification(issue) -> dict:
    text = f"{issue.title} {issue.description}".lower()

    rules = [
        (("ac", "air conditioner"), "Air Conditioner", "Electrical", "electrician"),
        (("fan", "switch", "socket"), "Electrical Fixture", "Electrical", "electrician"),
        (("refrigerator", "washing machine"), "Home Appliance", "Electrical", "appliance technician"),
        (("tap", "pipe", "leak", "water tank", "water"), "Water Leakage", "Plumbing", "plumber"),
        (("door", "latch", "window", "furniture"), "Door or Furniture", "Carpentry", "carpenter"),
        (("tile", "floor", "wall crack", "cement"), "Civil Repair", "Civil", "mason"),
        (("tv", "speaker", "home theater"), "Electronics", "Electronics", "electronics technician"),
    ]

    problem_type = "General"
    category = "General"
    skill = "general technician"
    for keywords, mapped_problem, mapped_category, mapped_skill in rules:
        if any(keyword in text for keyword in keywords):
            problem_type = mapped_problem
            category = mapped_category
            skill = mapped_skill
            break

    if any(word in text for word in ("fire", "sparking", "shock", "burst", "flood")):
        urgency = "critical"
    elif any(word in text for word in ("urgent", "tonight", "immediately", "emergency", "leaking", "not working")):
        urgency = "high"
    elif any(word in text for word in ("soon", "today", "tomorrow")):
        urgency = "medium"
    else:
        urgency = "low"

    return {
        "problem_type": problem_type,
        "category": category,
        "priority": urgency,
        "urgency": urgency,
        "required_skills": [skill],
        "confidence_score": 0.72 if category != "General" else 0.45,
        "ai_explanation": (
            f"Classified as {category} because the issue text contains signals "
            f"that match {skill} work. Urgency is {urgency} based on timing and risk words."
        ),
    }


def _classify_with_openai(issue) -> dict | None:
    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON for service issue classification.",
                },
                {
                    "role": "user",
                    "content": _build_prompt(issue),
                },
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
    except Exception:
        return None

    parsed = _parse_json_response(content)
    return _normalize_ai_response(parsed) if parsed else None


def _classify_with_gemini(issue) -> dict | None:
    if not os.getenv("GEMINI_API_KEY"):
        return None

    try:
        import google.generativeai as genai
    except ImportError:
        return None

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        response = model.generate_content(_build_prompt(issue))
        content = getattr(response, "text", "") or "{}"
    except Exception:
        return None

    parsed = _parse_json_response(content)
    return _normalize_ai_response(parsed) if parsed else None


def classify_issue_content(issue) -> dict:
    return (
        _classify_with_openai(issue)
        or _classify_with_gemini(issue)
        or _keyword_classification(issue)
    )
