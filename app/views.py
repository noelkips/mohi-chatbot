import json
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from app.rafiki import feedback_store, get_answer, get_chatbot_mode


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "app/index.html")


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "status": "online",
            "service": "Rafiki IT",
            "chatbot_mode": get_chatbot_mode(),
        }
    )


def _parse_json(request: HttpRequest) -> dict[str, Any] | None:
    try:
        body = request.body.decode("utf-8") if request.body else "{}"
        return json.loads(body or "{}")
    except json.JSONDecodeError:
        return None


@csrf_exempt
@require_http_methods(["POST"])
def chat(request: HttpRequest) -> JsonResponse:
    payload = _parse_json(request)
    if payload is None:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []
    return JsonResponse({"response": get_answer(message, history)})


@csrf_exempt
@require_http_methods(["POST"])
def feedback(request: HttpRequest) -> JsonResponse:
    payload = _parse_json(request)
    if payload is None:
        return JsonResponse({"success": False, "message": "Invalid JSON payload"}, status=400)
    feedback_store.append(
        {
            "messageIndex": payload.get("messageIndex"),
            "messageContent": payload.get("messageContent"),
            "feedbackType": payload.get("feedbackType"),
            "feedbackReason": payload.get("feedbackReason"),
            "timestamp": payload.get("timestamp"),
        }
    )
    return JsonResponse({"success": True, "message": "Thank you for your feedback!"})


@require_GET
def feedback_stats(request: HttpRequest) -> JsonResponse:
    if not feedback_store:
        return JsonResponse({"total": 0, "positive": 0, "negative": 0, "reasons": {}})

    positive = sum(1 for item in feedback_store if item["feedbackType"] == "positive")
    negative = sum(1 for item in feedback_store if item["feedbackType"] == "negative")
    reasons: dict[str, int] = {}

    for item in feedback_store:
        reason = item.get("feedbackReason")
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1

    return JsonResponse(
        {
            "total": len(feedback_store),
            "positive": positive,
            "negative": negative,
            "satisfaction_rate": round((positive / len(feedback_store)) * 100, 1),
            "reasons": reasons,
        }
    )
