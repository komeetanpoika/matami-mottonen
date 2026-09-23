import re
import secrets
import unicodedata

_ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return s[:100] or "event"


def make_slug(title: str, suffix: str | None = None) -> str:
    if suffix is None:
        suffix = "".join(secrets.choice(_ALPHABET) for _ in range(4))
    return f"{slugify(title)}-{suffix}"
