import webbrowser

from mi_companion.mi_editor.authentication.oauth import TEXT_BROWSERS


def _open_new_browser(url: str) -> bool:
    """Opens a web browser if possible, returning True when so."""
    try:
        browser = webbrowser.get()
        if hasattr(browser, "name") and browser.name in TEXT_BROWSERS:
            return False
    except webbrowser.Error:
        return False
    if url:
        webbrowser.open_new(url)
    return True
