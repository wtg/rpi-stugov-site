import logging
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .oidc import append_query_parameters, discovery_url


logger = logging.getLogger(__name__)


@never_cache
@require_POST
def oidc_logout(request):
    """End the local session, then initiate provider logout when available."""
    logout(request)

    try:
        response = requests.get(
            discovery_url(settings.OIDC_SERVER_URL),
            timeout=settings.SOCIALACCOUNT_REQUESTS_TIMEOUT,
        )
        response.raise_for_status()
        end_session_endpoint = response.json().get("end_session_endpoint")
        if not isinstance(end_session_endpoint, str):
            raise ValueError("OIDC discovery has no end_session_endpoint")
        parsed_endpoint = urlsplit(end_session_endpoint)
        if parsed_endpoint.scheme != "https" or not parsed_endpoint.netloc:
            raise ValueError("OIDC end_session_endpoint must use HTTPS")

        return redirect(
            append_query_parameters(
                end_session_endpoint,
                {
                    "client_id": settings.OIDC_CLIENT_ID,
                    "post_logout_redirect_uri": settings.OIDC_POST_LOGOUT_REDIRECT_URI,
                },
            )
        )
    except (requests.RequestException, TypeError, ValueError):
        logger.warning("CMS logout unavailable", exc_info=True)
        return redirect(settings.OIDC_POST_LOGOUT_REDIRECT_URI)
