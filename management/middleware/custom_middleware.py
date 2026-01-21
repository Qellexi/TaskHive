from django.shortcuts import redirect
from django.urls import reverse


class RequireOrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        #apply only to authenticated users
        if request.user.is_authenticated:
            #check if organization field is missing
            if not getattr(request.user, 'organization', None) or not getattr(request.user, 'organization', None):
                allowed_paths = [
                    reverse("logout"),
                    reverse("assign-organization"),
                ]
                if request.path not in allowed_paths:
                    return redirect("assign-organization")
        response = self.get_response(request)
        return response
