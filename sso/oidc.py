from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def discovery_url(server_url):
    """Return the provider discovery URL for an issuer or explicit metadata URL."""
    if "/.well-known/" in server_url:
        return server_url
    return f"{server_url.rstrip('/')}/.well-known/openid-configuration"


def merged_claims(extra_data):
    """Combine ID-token and userinfo claims, preferring userinfo values."""
    if not isinstance(extra_data, Mapping):
        return {}

    id_token = extra_data.get("id_token")
    userinfo = extra_data.get("userinfo")
    if isinstance(id_token, Mapping) or isinstance(userinfo, Mapping):
        claims = {}
        if isinstance(id_token, Mapping):
            claims.update(id_token)
        if isinstance(userinfo, Mapping):
            claims.update(userinfo)
        return claims
    return dict(extra_data)


def claim_at_path(claims, path):
    """Resolve a dotted claim path such as ``realm_access.roles``."""
    value = claims
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def append_query_parameters(url, parameters):
    """Add logout parameters while retaining any query supplied by the IdP."""
    scheme, netloc, path, query, fragment = urlsplit(url)
    query_values = parse_qsl(query, keep_blank_values=True)
    query_values.extend(parameters.items())
    return urlunsplit((scheme, netloc, path, urlencode(query_values), fragment))
