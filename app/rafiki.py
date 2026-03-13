import logging
from typing import Any


logger = logging.getLogger(__name__)

CHATBOT_AVAILABLE = False
_get_rafiki_answer = None
feedback_store: list[dict[str, Any]] = []

BUILTIN_RESPONSES = {
    "it office": """The **MOHI IT Office** is located at the **Pangani Head Office**.

**Contact Information:**
- Extension: **303** or **304**
- Location: Pangani Head Office, Nairobi

Feel free to reach out during working hours (8:00 AM - 5:00 PM). God bless!""",
    "locked": """I'm sorry to hear you're locked out of your portal! Here's how to get help:

**Steps to Resolve Portal Lockout:**
1. Contact the IT department at **Extension 303 or 304**
2. Provide your **Staff ID** and **Username**
3. Wait for password reset (usually within 30 minutes)

**Tip:** While waiting, verify your internet connection is stable.""",
    "leave": """Here's how to apply for leave through the MOHI Portal:

**Steps to Apply for Leave:**
1. Log into the **MOHI Staff Portal**
2. Navigate to **Employee** > **Leave Application**
3. Select the **Leave Type** (Annual, Sick, etc.)
4. Enter your **Start Date** and **End Date**
5. Add any required **Supporting Documents**
6. Click **Submit** and wait for supervisor approval

Need help? Contact HR at the Pangani office.""",
    "default": """Thank you for reaching out! I'm Rafiki, your friendly IT assistant for MOHI.

I'm currently in **limited mode**, but I can still help guide you.

- **IT Office Location**: Pangani (Ext 303/304)
- **Portal Issues**: Contact IT for password resets
- **Leave Applications**: Use **Employee** > **Leave** in the portal

For complex issues, please contact the IT department directly.""",
}


def load_chatbot() -> None:
    global CHATBOT_AVAILABLE, _get_rafiki_answer
    if _get_rafiki_answer is not None or CHATBOT_AVAILABLE:
        return

    try:
        from app.services.chatbot import get_rafiki_answer as chatbot_answer

        _get_rafiki_answer = chatbot_answer
        CHATBOT_AVAILABLE = True
        logger.info("Rafiki chatbot service loaded successfully")
    except Exception as exc:  # pragma: no cover
        CHATBOT_AVAILABLE = False
        logger.warning("Falling back to built-in Rafiki responses: %s", exc)


def get_builtin_response(message: str) -> str:
    message_lower = (message or "").lower()

    if "office" in message_lower and any(word in message_lower for word in ("it", "location", "where")):
        return BUILTIN_RESPONSES["it office"]
    if any(word in message_lower for word in ("lock", "password", "reset")):
        return BUILTIN_RESPONSES["locked"]
    if any(word in message_lower for word in ("leave", "apply", "vacation")):
        return BUILTIN_RESPONSES["leave"]
    return BUILTIN_RESPONSES["default"]


def get_chatbot_mode() -> str:
    load_chatbot()
    return "ai-powered" if CHATBOT_AVAILABLE else "builtin"


def get_answer(message: str, history: list[dict[str, Any]] | None = None) -> str:
    load_chatbot()
    if CHATBOT_AVAILABLE and _get_rafiki_answer:
        try:
            return _get_rafiki_answer(message, chat_history=history or [])
        except Exception as exc:  # pragma: no cover
            logger.warning("Chatbot error, using fallback response: %s", exc)
    return get_builtin_response(message)
