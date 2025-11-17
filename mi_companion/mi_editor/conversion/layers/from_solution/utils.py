import re
import unicodedata

__all__ = ["sanitize_name"]


def sanitize_name(name: str) -> str:
    # Normalize accents/Unicode → ASCII
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    # Lowercase
    name = name.lower()

    # Replace all whitespace with underscores
    name = re.sub(r"\s+", "_", name)
    # Remove everything except letters, digits, and underscores
    name = re.sub(r"[^a-z0-9_]", "", name)
    # Collapse multiple underscores into one
    name = re.sub(r"_+", "_", name)

    # Strip leading/trailing underscores
    name = name.strip("_")

    return name
