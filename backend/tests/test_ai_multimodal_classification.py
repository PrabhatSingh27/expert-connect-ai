import base64
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.services.ai_classification_service import (
    _build_prompt,
    classify_issue_content,
    encode_image_as_data_url,
    transcribe_audio_file,
)
from app.schemas.issue import IssueClassificationResponse


class _TranscriptClient:
    class audio:
        class transcriptions:
            @staticmethod
            def create(**_kwargs):
                return SimpleNamespace(text="There is water leaking from the AC.")


class MultimodalClassificationTests(TestCase):
    def test_image_is_encoded_as_a_vision_data_url(self):
        with TemporaryDirectory() as directory:
            image = Path(directory) / "leak.png"
            image.write_bytes(b"image-content")
            data_url = encode_image_as_data_url(str(image))

        self.assertEqual(data_url, "data:image/png;base64," + base64.b64encode(b"image-content").decode())

    def test_audio_transcript_is_added_to_the_llm_prompt(self):
        issue = SimpleNamespace(title="AC issue", description="Please help", location=None, pin_code=None, attachments=[])
        with TemporaryDirectory() as directory:
            audio = Path(directory) / "report.mp3"
            audio.write_bytes(b"audio-content")
            transcript = transcribe_audio_file(str(audio), _TranscriptClient())

        self.assertIn(transcript, _build_prompt(issue, transcript))

    def test_model_failure_falls_back_to_text_classification(self):
        issue = SimpleNamespace(title="Leaking tap", description="Water is leaking urgently", attachments=[])
        with patch("app.services.ai_classification_service._classify_with_openai", return_value=None), \
             patch("app.services.ai_classification_service._classify_with_gemini", return_value=None):
            result = classify_issue_content(issue)

        self.assertEqual(result["category"], "🚰 Plumbing")
        self.assertEqual(result["assigned_expert"], "Plumber")
        self.assertEqual(result["urgency"], "high")

    def test_classification_response_exposes_dashboard_detected_and_response(self):
        response = IssueClassificationResponse.model_validate(
            {
                "id": 7,
                "problem_type": "Home Appliances",
                "category": "🧊 Home Appliances",
                "priority": "medium",
                "urgency": "medium",
                "required_skills": ["Appliance Technician"],
                "confidence_score": 0.9,
                "detected": "The symptoms indicate a washing machine motor or spin-cycle fault.",
                "response": "Matched the appliance and failure symptom to Home Appliances.",
            }
        )

        self.assertTrue(response.detected.startswith("The symptoms"))
        self.assertTrue(response.response.startswith("Matched the appliance"))
