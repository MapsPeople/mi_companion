def clean_str(s: str) -> str:
    import re

    return re.compile(r"\W+").sub(" ", s).strip()[:200]

    # return s.translate({ord("\n"): None})
