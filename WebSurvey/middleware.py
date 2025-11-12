from .services import auto_close_due_surveys


class AutoCloseSurveyMiddleware:
    """Ensure surveys past their due date are marked closed on every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auto_close_due_surveys()
        response = self.get_response(request)
        return response
