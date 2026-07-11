import logging

logger = logging.getLogger(__name__)


def send_mock_email(to_email: str, subject: str, body: str) -> None:
    logger.info("mock_email to=%s subject=%s body=%s", to_email, subject, body)


def send_mock_sms(phone: str, message: str) -> None:
    logger.info("mock_sms phone=%s message=%s", phone, message)


def send_mock_whatsapp(phone: str, message: str) -> None:
    logger.info("mock_whatsapp phone=%s message=%s", phone, message)


def notify_expert_assigned(expert, issue) -> None:
    send_mock_email(
        expert.email,
        "New issue assigned",
        f"Issue #{issue.id} has been assigned to you.",
    )


def notify_issue_status_changed(issue, status: str) -> None:
    logger.info("issue_status_changed issue_id=%s status=%s", issue.id, status)
