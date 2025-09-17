from django import template
from django.core import signing


register = template.Library()


def _encode(kind: str, numeric_id) -> str:
    try:
        return signing.dumps({"id": int(numeric_id)}, salt=f"yoyo:{kind}")
    except Exception:
        return ""


@register.filter(name="chat_token")
def chat_token(numeric_id) -> str:
    return _encode("chat", numeric_id)


@register.filter(name="gem_token")
def gem_token(numeric_id) -> str:
    return _encode("gem", numeric_id)


@register.filter(name="user_token")
def user_token(numeric_id) -> str:
    return _encode("user", numeric_id)


@register.filter(name="savedinfo_token")
def savedinfo_token(numeric_id) -> str:
    return _encode("savedinfo", numeric_id)


