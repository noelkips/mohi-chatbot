import os

from django.http import HttpResponse


class SimpleCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allow_origin = os.getenv("DJANGO_CORS_ALLOW_ORIGIN", "*")
        self.allow_methods = "GET, POST, OPTIONS"
        self.allow_headers = "Content-Type"

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = self.allow_origin
        response["Access-Control-Allow-Methods"] = self.allow_methods
        response["Access-Control-Allow-Headers"] = self.allow_headers
        return response
