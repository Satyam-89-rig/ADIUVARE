from urllib.parse import parse_qs

from ..core.models import RequestContext


def build_http_ctx(
    *,
    identity: str,
    payload: str | None,
    url: str,
    method: str,
    headers: dict,
    ip: str,
    endpoint: str,
    snapshot,
) -> RequestContext:
    return RequestContext(
        identity=identity,
        payload=payload,
        url=url,
        method=method,
        headers=headers,
        ip=ip,
        endpoint=endpoint,
        snapshot=snapshot,
    )


def ctx_payload(body_text: str | None, query_text: str | None) -> str | None:
    parts: list[str] = []
    if body_text:
        parts.append(body_text)
    if query_text:
        values = " ".join(
            value
            for group in parse_qs(query_text, keep_blank_values=True).values()
            for value in group
        ).strip()
        if values:
            parts.append(values)
    if not parts:
        return None
    return "\n".join(parts)
