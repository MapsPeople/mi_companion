__all__ = ["clean_str"]


def clean_str(s: str) -> str:
    """

    :param s:
    :type s:
    :return:
    :rtype:
    """
    import re

    return re.compile(r"\W+").sub(" ", s).strip()[:200]

    # return s.translate({ord("\n"): None})
