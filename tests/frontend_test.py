"""End-to-end UI tests driving a real browser via Playwright."""

from __future__ import annotations

import pathlib

from tests.constants_test import (
    AUTOPREVIEW_CHECKBOX,
    BOLD_BUTTON,
    CLEAR_STORAGE_SCRIPT,
    DEFAULT_NAME,
    EDITOR_SELECT,
    EMAIL_INPUT,
    NAME_INPUT,
    SECTION_ADD_BUTTON,
    SECTION_ADD_SELECT,
    SECTION_CARDS,
    SECTION_TITLES_SCRIPT,
    SUMMARY_TEXTAREA,
    TAG_NAME_SCRIPT,
    THEME_SELECT,
    TITLE_INPUT,
    TOAST_SELECTOR,
)


def _wait_preview(page):
    page.wait_for_function(
        "() => { const f = document.getElementById('preview');"
        " return f && f.src && f.src.startsWith('blob:'); }",
        timeout=20000,
    )


def test_page_loads_and_preview_renders(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    assert 'Resume Studio' in page.title()
    _wait_preview(page)
    # First loaded section title comes from the YAML key, title-cased.
    first_title = page.locator(SECTION_CARDS).first.locator(TITLE_INPUT)
    assert first_title.input_value() == 'Summary'


def test_fill_name_updates_without_error(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    page.locator(NAME_INPUT).fill('Playwright Test User')
    page.wait_for_timeout(1500)
    assert page.locator('#toast.error').count() == 0
    _wait_preview(page)


def test_add_custom_section_and_rename(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(SECTION_ADD_SELECT)
    page.select_option(SECTION_ADD_SELECT, 'custom')
    page.locator(SECTION_ADD_BUTTON).click()
    last = page.locator(SECTION_CARDS).last
    last.locator(TITLE_INPUT).fill('Awards')
    page.wait_for_timeout(600)
    assert last.locator(TITLE_INPUT).input_value() == 'Awards'
    # the custom entry editor exposes a Title field
    assert last.locator("input[placeholder='Item title']").count() == 1


def test_el_helper_creates_elements(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    result = page.evaluate("""() => {
      const el = window.el;
      const withChildren = el('div', { class: 'bar' }, 'a', null, 'b');
      const btn = el('button', { type: 'button', onclick: () => {} }, 'Click');
      const hidden = el('input', { hidden: true });
      return {
        childCount: withChildren.childNodes.length,
        firstText: withChildren.childNodes[0] && withChildren.childNodes[0].nodeValue,
        lastText: withChildren.childNodes[withChildren.childNodes.length - 1] && withChildren.childNodes[withChildren.childNodes.length - 1].nodeValue,
        btnTag: btn.tagName,
        btnText: btn.textContent,
        hiddenAttr: hidden.hasAttribute('hidden'),
      };
    }""")
    assert result['childCount'] == 2
    assert result['firstText'] == 'a'
    assert result['lastText'] == 'b'
    assert result['btnTag'] == 'BUTTON'
    assert result['btnText'] == 'Click'
    assert result['hiddenAttr'] is True


def test_reorder_sections(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(SECTION_CARDS)
    cards = page.locator(SECTION_CARDS)
    before_first = cards.nth(0).locator(TITLE_INPUT).input_value()
    before_second = cards.nth(1).locator(TITLE_INPUT).input_value()
    cards.nth(0).locator("button[title='Move down']").click()
    page.wait_for_timeout(500)
    after = page.locator(SECTION_CARDS)
    assert after.nth(0).locator(TITLE_INPUT).input_value() == before_second
    assert after.nth(1).locator(TITLE_INPUT).input_value() == before_first


def test_skills_details_is_wrapping_textarea(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(SECTION_CARDS)
    area = page.locator("textarea[placeholder^='Python']").first
    assert area.evaluate(TAG_NAME_SCRIPT) == 'TEXTAREA'
    area.fill('x' * 240)
    page.wait_for_timeout(300)
    # wrapped: content taller than the visible box
    assert area.evaluate('el => el.scrollHeight > el.clientHeight + 2')


def test_experience_highlights_is_wrapping_textarea(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(SECTION_CARDS)
    # Experience is the 3rd section in defaults (index 2).
    exp = page.locator(SECTION_CARDS).nth(2)
    exp.locator("button:has-text('Add highlight')").first.click()
    ta = exp.locator("textarea[placeholder='Achievement or responsibility']").first
    assert ta.evaluate(TAG_NAME_SCRIPT) == 'TEXTAREA'


def test_validation_error_shown(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EMAIL_INPUT)
    page.locator(EMAIL_INPUT).fill('not-an-email')
    page.locator('#preview-btn').click()
    page.wait_for_selector('#toast.error', timeout=8000)
    assert 'email' in page.locator(TOAST_SELECTOR).inner_text().lower()


def test_download_pdf(page, base_url, tmp_path: pathlib.Path):
    page.goto(base_url)
    _wait_preview(page)
    with page.expect_download() as dl:
        page.locator('#download-btn').click()
    download = dl.value
    target = tmp_path / 'resume.pdf'
    download.save_as(str(target))
    assert target.exists()
    assert target.read_bytes()[:4] == b'%PDF'


def test_bold_button_wraps_selection(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    area = page.locator(SUMMARY_TEXTAREA).first
    area.fill('Hello world test')
    area.evaluate('el => { el.setSelectionRange(6, 11); el.focus(); }')
    page.locator(BOLD_BUTTON).click()
    assert area.input_value() == 'Hello **world** test'


def test_italic_button_wraps_selection(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    area = page.locator(SUMMARY_TEXTAREA).first
    area.fill('Hello world test')
    area.evaluate('el => { el.setSelectionRange(6, 11); el.focus(); }')
    page.locator(".format-toolbar--global [data-action='italic']").click()
    assert area.input_value() == 'Hello *world* test'


def test_bold_button_inserts_markers_at_cursor(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    area = page.locator(SUMMARY_TEXTAREA).first
    area.fill('Hello')
    area.evaluate('el => { el.setSelectionRange(5, 5); el.focus(); }')
    page.locator(BOLD_BUTTON).click()
    assert area.input_value() == 'Hello****'
    assert area.evaluate('el => el.selectionStart') == 7
    assert area.evaluate('el => el.selectionEnd') == 7


def test_bold_button_works_on_any_textarea(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(SECTION_CARDS)
    skills_details = page.locator("textarea[placeholder^='Python']").first
    skills_details.fill('Python Go Rust')
    skills_details.evaluate('el => { el.setSelectionRange(7, 9); el.focus(); }')
    page.locator(BOLD_BUTTON).click()
    assert skills_details.input_value() == 'Python **Go** Rust'


def test_bold_button_works_on_text_input(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    company = page.locator("input[placeholder='Acme Inc.']").first
    company.fill('Acme Corp')
    company.evaluate('el => { el.setSelectionRange(5, 9); el.focus(); }')
    page.locator(BOLD_BUTTON).click()
    assert company.input_value() == 'Acme **Corp**'


def test_form_data_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(EDITOR_SELECT)
    page.locator(NAME_INPUT).fill('Alice Smith')
    page.locator("input[placeholder='Software Engineer']").fill('Senior Developer')
    page.reload()
    _wait_preview(page)
    assert page.locator(NAME_INPUT).input_value() == 'Alice Smith'
    assert page.locator("input[placeholder='Software Engineer']").input_value() == 'Senior Developer'


def test_theme_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(THEME_SELECT)
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'moderncv', accent: '#4f46e5', pageSize: 'a4', showFooter: false }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    assert page.locator(THEME_SELECT).input_value() == 'moderncv'


def test_accent_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector('#accent-color')
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'engineeringresumes', accent: '#ff0000', pageSize: 'a4', showFooter: false }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    saved = page.evaluate("() => JSON.parse(localStorage.getItem('rendercv_state') || '{}')")
    assert saved.get('design', {}).get('accent') == '#ff0000'
    assert page.locator('#accent-color').input_value().lower() == '#ff0000'


def test_sections_persist_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(SECTION_CARDS)
    page.select_option(SECTION_ADD_SELECT, 'custom')
    page.locator(SECTION_ADD_BUTTON).click()
    page.wait_for_selector(SECTION_CARDS)
    last_title = page.locator(SECTION_CARDS).last.locator("input[placeholder='Section title']")
    last_title.fill('Awards')
    page.wait_for_timeout(500)
    page.reload()
    _wait_preview(page)
    values = page.evaluate(SECTION_TITLES_SCRIPT)
    assert 'Awards' in values


def test_empty_form_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(EDITOR_SELECT)
    page.reload()
    _wait_preview(page)
    assert page.locator(NAME_INPUT).input_value() == DEFAULT_NAME
    assert page.locator(EMAIL_INPUT).input_value() == 'xyz@gmail.com'


def test_special_characters_persist_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(EDITOR_SELECT)
    page.locator(NAME_INPUT).fill('José García 日本語 🎉')
    page.reload()
    _wait_preview(page)
    assert page.locator(NAME_INPUT).input_value() == 'José García 日本語 🎉'


def test_bold_on_empty_selection_inserts_markers(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    area = page.locator(SUMMARY_TEXTAREA).first
    area.fill('Hello world')
    area.evaluate('el => { el.setSelectionRange(0, 0); el.focus(); }')
    page.locator(BOLD_BUTTON).click()
    assert area.input_value() == '****Hello world'


def test_italic_on_empty_selection_inserts_markers(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    area = page.locator(SUMMARY_TEXTAREA).first
    area.fill('Hello world')
    area.evaluate('el => { el.setSelectionRange(0, 0); el.focus(); }')
    page.locator(".format-toolbar--global [data-action='italic']").click()
    assert area.input_value() == '**Hello world'


def test_remove_section_and_persist(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(SECTION_CARDS)
    initial_count = page.locator(SECTION_CARDS).count()
    cards = page.locator(SECTION_CARDS)
    cards.nth(0).locator('button.card-remove').click()
    page.wait_for_timeout(500)
    assert page.locator(SECTION_CARDS).count() == initial_count - 1
    page.reload()
    _wait_preview(page)
    assert page.locator(SECTION_CARDS).count() == initial_count - 1


def test_multiple_sections_persist(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(SECTION_CARDS)
    for label in ['Projects', 'Certifications', 'Custom']:
        page.select_option(SECTION_ADD_SELECT, label.lower())
        page.locator(SECTION_ADD_BUTTON).click()
        page.wait_for_selector(SECTION_CARDS)
    page.reload()
    _wait_preview(page)
    titles = page.evaluate(SECTION_TITLES_SCRIPT)
    assert 'Projects' in titles
    assert 'Certifications' in titles
    assert 'Custom Section' in titles


def test_corrupted_localstorage_falls_back_to_defaults(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.setItem('rendercv_state', 'not-json')")
    page.reload()
    _wait_preview(page)
    assert page.locator(NAME_INPUT).input_value() == DEFAULT_NAME


def test_autopreview_toggle_persists(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(AUTOPREVIEW_CHECKBOX)
    page.uncheck(AUTOPREVIEW_CHECKBOX)
    page.wait_for_timeout(500)
    saved = page.evaluate("() => JSON.parse(localStorage.getItem('rendercv_state') || '{}')")
    assert saved.get('ui', {}).get('autopreview') == False
    page.goto(base_url)
    _wait_preview(page)
    assert not page.locator(AUTOPREVIEW_CHECKBOX).is_checked()


def test_partial_state_merges_with_defaults(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(THEME_SELECT)
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'moderncv', accent: '#ff0000', pageSize: 'a4', showFooter: false }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    assert page.locator(THEME_SELECT).input_value() == 'moderncv'
    assert page.locator(NAME_INPUT).input_value() == DEFAULT_NAME
    assert page.locator(EMAIL_INPUT).input_value() == 'xyz@gmail.com'


def test_empty_new_section_entries_do_not_break_render(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(SECTION_ADD_SELECT)
    page.select_option(SECTION_ADD_SELECT, 'custom')
    page.locator(SECTION_ADD_BUTTON).click()
    page.wait_for_selector(SECTION_CARDS)
    page.reload()
    _wait_preview(page)
    titles = page.evaluate(SECTION_TITLES_SCRIPT)
    assert 'Custom Section' in titles


def test_corrupted_design_state_falls_back_to_defaults(page, base_url):
    page.goto(base_url)
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'nonexistent-theme' }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    assert page.locator(THEME_SELECT).input_value() == 'engineeringresumes'
    assert page.locator(NAME_INPUT).input_value() == DEFAULT_NAME


def test_toast_is_output_element_not_div_with_role(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(TOAST_SELECTOR)
    tag = page.locator(TOAST_SELECTOR).evaluate(TAG_NAME_SCRIPT)
    assert tag.lower() == 'output'
    assert page.locator('#toast[role="status"]').count() == 0


def test_uid_uses_crypto_getrandomvalues(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    uses_crypto = page.evaluate("""() => {
      const src = typeof uid === 'function' ? uid.toString() : '';
      return src.includes('crypto.getRandomValues');
    }""")
    assert uses_crypto is True


def test_el_helper_rejects_html_injection(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    result = page.evaluate("""() => {
      const el = window.el;
      // Attempt to inject markup via a would-be 'html' attribute.
      const node = el('div', { class: 'x', html: '<img src=x onerror=alert(1)>' }, 'safe');
      return {
        inner: node.innerHTML,
        childCount: node.childNodes.length,
        text: node.textContent,
      };
    }""")
    # The 'html' attribute must be ignored: no <img> injected, only text child.
    assert '<img' not in result['inner']
    assert result['childCount'] == 1
    assert result['text'] == 'safe'


def test_toast_renders_error_text_without_html_injection(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    result = page.evaluate("""() => {
      const t = document.getElementById('toast');
      // Simulate a validation error message containing HTML metacharacters.
      const msg = '<script>alert(1)</script> & <b>bold</b>';
      showToast(msg, true);
      return {
        inner: t.innerHTML,
        hasScriptChild: !!t.querySelector('script'),
        hasBChild: !!t.querySelector('b'),
        firstText: t.textContent,
      };
    }""")
    # Error text must be shown as literal text, never parsed into elements.
    assert result['hasScriptChild'] is False
    assert result['hasBChild'] is False
    # textContent holds the raw string; innerHTML shows it HTML-escaped.
    assert '<script>alert(1)</script> & <b>bold</b>' in result['firstText']
    assert '&lt;script&gt;' in result['inner']


# ---------------------------------------------------------------------------
# XSS hardening suite — every DOM-write sink is exercised with both a
# positive (escaping works) and a negative (injection attempt is blocked) case.
# ---------------------------------------------------------------------------

XSS_PAYLOADS = [
    '<script>alert(1)</script>',
    '<img src=x onerror=alert(1)>',
    '<svg/onload=alert(1)>',
    "\"><img src=x onerror=alert(1)>",
    'javascript:alert(1)',
    '<iframe src=javascript:alert(1)>',
]


def test_el_html_branch_is_removed(page, base_url):
    """Negative: the removed 'html' attribute must not inject markup."""
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    for payload in XSS_PAYLOADS:
        result = page.evaluate("""(p) => {
          const el = window.el;
          const node = el('div', { class: 'x', html: p }, 'safe');
          return { inner: node.innerHTML, count: node.childNodes.length };
        }""", payload)
        assert '<img' not in result['inner']
        assert '<script' not in result['inner']
        assert '<svg' not in result['inner']
        assert '<iframe' not in result['inner']
        assert result['count'] == 1  # only the text child


def test_el_rejects_inline_event_handler_strings(page, base_url):
    """Negative: string-valued on* attributes must be ignored (no inline JS)."""
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    result = page.evaluate("""() => {
      const el = window.el;
      // Attempt an inline handler via the 'html'-style onload string.
      const node = el('img', { src: 'x', onload: 'window.__xss=1' });
      return {
        hasHandler: '__xss' in window,
        outer: node.outerHTML,
      };
    }""")
    assert result['hasHandler'] is False
    assert 'onload' not in result['outer']


def test_el_text_children_are_not_parsed(page, base_url):
    """Positive: string children render as text nodes, not parsed HTML."""
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    for payload in XSS_PAYLOADS:
        result = page.evaluate("""(p) => {
          const el = window.el;
          const node = el('div', {}, p);
          return {
            text: node.textContent,
            hasImg: !!node.querySelector('img'),
            hasScript: !!node.querySelector('script'),
          };
        }""", payload)
        assert result['text'] == payload
        assert result['hasImg'] is False
        assert result['hasScript'] is False


def test_toast_escapes_all_xss_payloads(page, base_url):
    """Positive + negative: toast shows raw text, never parsed elements."""
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    for payload in XSS_PAYLOADS:
        result = page.evaluate("""(p) => {
          const t = document.getElementById('toast');
          showToast(p, true);
          return {
            text: t.textContent,
            hasImg: !!t.querySelector('img'),
            hasScript: !!t.querySelector('script'),
            hasSvg: !!t.querySelector('svg'),
            hasIframe: !!t.querySelector('iframe'),
          };
        }""", payload)
        assert result['text'] == payload
        assert result['hasImg'] is False
        assert result['hasScript'] is False
        assert result['hasSvg'] is False
        assert result['hasIframe'] is False


def test_download_filename_is_sanitized(page, base_url):
    """Negative: a malicious name must not produce a dangerous filename."""
    page.goto(base_url)
    page.wait_for_selector(EDITOR_SELECT)
    for payload in XSS_PAYLOADS + ['../../etc/passwd', 'a/b\\c:d*e?f']:
        result = page.evaluate("""(p) => {
          return sanitizeFilename(p);
        }""", payload)
        # No path traversal, no slashes, no control chars, always .pdf.
        assert '/' not in result
        assert '\\' not in result
        assert '..' not in result
        assert result.endswith('.pdf')


def test_form_injection_does_not_execute_on_preview(page, base_url):
    """End-to-end negative: typing XSS into fields never injects into the DOM."""
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(EDITOR_SELECT)
    payload = '<img src=x onerror=window.__pwned=1>'
    page.locator(NAME_INPUT).fill(payload)
    page.locator(SUMMARY_TEXTAREA).first.fill(payload)
    page.wait_for_timeout(1200)
    _wait_preview(page)
    pwned = page.evaluate('() => window.__pwned === 1')
    assert pwned is False
    # The name input must still hold the literal text.
    assert page.locator(NAME_INPUT).input_value() == payload
    # No stray <img> injected anywhere in the editor.
    assert page.locator(f"{EDITOR_SELECT} img").count() == 0


def test_long_text_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate(CLEAR_STORAGE_SCRIPT)
    page.wait_for_selector(EDITOR_SELECT)
    long_text = 'A' * 5000
    page.locator(SUMMARY_TEXTAREA).first.fill(long_text)
    page.reload()
    _wait_preview(page)
    assert page.locator(SUMMARY_TEXTAREA).first.input_value() == long_text
