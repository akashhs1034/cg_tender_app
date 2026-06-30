"""Visual-regression smoke test for Opporta tender/job/opportunity cards.

Why this exists
---------------
Cards are built as HTML strings and shown with ``st.markdown(..., unsafe_allow_html=True)``.
Streamlit feeds every markdown body through ``textwrap.dedent()`` + a CommonMark
renderer *even when* ``unsafe_allow_html=True``. If a multi-line card template keeps
its opening tag at column 0 (so ``dedent`` can't reduce the body) and an optional
``{fragment}`` renders empty, that line becomes whitespace-only. CommonMark then reads
a blank line, CLOSES the raw-HTML block, and renders the following indented lines as a
literal ``<code>`` block — leaking raw ``<div class="ocard-org">`` / ``<span class="tag
tag-cat">`` / ``<div class="ring ring-hi">88%</div>`` markup straight onto the page.

This test opens the public **Tender Portal** and **Government Jobs** pages with
Streamlit's official ``AppTest`` harness, re-renders every markdown body exactly the
way the browser does, and asserts the *visible* text never contains raw card markup.

Run directly:   python test_card_smoke.py
Run via pytest: pytest test_card_smoke.py
(requires the dev dependency ``markdown-it-py``; see requirements-dev.txt)
"""
from __future__ import annotations

import html as _html
import os
import re
import sys

from streamlit.string_util import clean_text  # the real dedent()+strip() Streamlit applies
from streamlit.testing.v1 import AppTest

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover - clear guidance instead of an opaque error
    sys.stderr.write(
        "markdown-it-py is required for the card smoke test.\n"
        "    pip install markdown-it-py   (or: pip install -r requirements-dev.txt)\n"
    )
    raise

# CommonMark with raw HTML passthrough — mirrors Streamlit's frontend markdown renderer.
_MD = MarkdownIt("commonmark", {"html": True})

# Always test the app.py sitting next to this test, regardless of the cwd it's run from.
APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

# Tokens that must NEVER appear in the *visible* text of a rendered card. The two
# CSS class names are unambiguous leak markers — they exist only inside our card
# templates and never inside scraped tender/job data.
FORBIDDEN = ["<div", "</div>", "<span", "</span>", "class=", "ocard-org", "ocard-tags"]

# Pages under test. The dispatcher routes on substring (`"Tenders" in page`,
# `"Jobs" in page`), so these exact session labels reach the public card lists.
PAGES = {
    "Tender Portal": "📄  Tenders",
    "Government Jobs": "💼  Jobs",
}


def visible_text(markdown_body: str) -> str:
    """Return the text a user actually SEES for one st.markdown body.

    Faithfully reproduces Streamlit: clean_text() then CommonMark render. We then
    drop the real HTML tags and unescape entities — so a correctly rendered card
    yields only its human-readable text, while a leaked card (rendered as an escaped
    ``<pre><code>`` block) surfaces its raw ``<div ...>`` markup as visible text.
    """
    rendered = _MD.render(clean_text(markdown_body))
    # Drop <style>/<script> blocks entirely — the browser never shows their contents,
    # so a CSS selector like `.ocard-org{...}` is invisible, not a leak.
    rendered = re.sub(
        r"<(style|script)\b[^>]*>.*?</\1>", "", rendered, flags=re.DOTALL | re.IGNORECASE)
    # Strip real tags FIRST (while any leaked tags are still entity-escaped), then unescape.
    without_tags = re.sub(r"<[^>]+>", "", rendered)
    return _html.unescape(without_tags)


def open_page(label: str) -> AppTest:
    """Boot app.py straight onto `label` with auth bypassed (offline CSV fallback ok)."""
    at = AppTest.from_file(APP_PATH, default_timeout=180)
    at.session_state["authenticated"] = True
    at.session_state["email"] = "smoketest@example.com"
    at.session_state["entered_platform"] = True
    at.session_state["current_page"] = label
    at.run()
    return at


def collect_leaks(at: AppTest) -> list[tuple[str, str]]:
    """Return (token, snippet) for every forbidden token visible on the page."""
    leaks: list[tuple[str, str]] = []
    for element in at.markdown:
        seen = visible_text(element.value or "")
        for token in FORBIDDEN:
            if token in seen:
                idx = seen.find(token)
                leaks.append((token, seen[max(0, idx - 30): idx + 60]))
    return leaks


def check_page(name: str, label: str) -> bool:
    """Smoke-test one page. Returns True on pass, prints a diagnostic on fail."""
    at = open_page(label)
    assert not at.exception, f"{name}: app raised on load -> {at.exception}"

    leaks = collect_leaks(at)
    if leaks:
        print(f"  [FAIL] {name}: raw HTML leaked into {len(leaks)} card(s):")
        for token, snippet in leaks[:8]:
            print(f"         {token!r} in …{snippet.strip()}…")
        return False

    print(f"  [OK]   {name}: {len(at.markdown)} markdown blocks, no raw HTML visible")
    return True


# ── pytest entry points ───────────────────────────────────────────────────────
def test_tender_portal_has_no_raw_html() -> None:
    at = open_page(PAGES["Tender Portal"])
    assert not at.exception, at.exception
    leaks = collect_leaks(at)
    assert not leaks, f"Tender Portal leaked raw HTML: {leaks[:5]}"


def test_government_jobs_has_no_raw_html() -> None:
    at = open_page(PAGES["Government Jobs"])
    assert not at.exception, at.exception
    leaks = collect_leaks(at)
    assert not leaks, f"Government Jobs leaked raw HTML: {leaks[:5]}"


def main() -> int:
    print("\n-- Opporta card rendering smoke test ---------------------------------")
    results = [check_page(name, label) for name, label in PAGES.items()]
    print("-" * 60)
    if all(results):
        print("  All card pages render cleanly — no raw HTML tags visible.\n")
        return 0
    print("  Raw HTML is leaking into cards — see failures above.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
