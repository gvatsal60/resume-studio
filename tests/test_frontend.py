"""End-to-end UI tests driving a real browser via Playwright."""

from __future__ import annotations

import pathlib


SECTION_CARDS = ".card:has(button[title='Move down'])"
TITLE_INPUT = "input[placeholder='Section title']"


def _wait_preview(page):
    page.wait_for_function(
        "() => { const f = document.getElementById('preview');"
        " return f && f.src && f.src.startsWith('blob:'); }",
        timeout=20000,
    )


def test_page_loads_and_preview_renders(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    assert "Resume Studio" in page.title()
    _wait_preview(page)
    # First loaded section title comes from the YAML key, title-cased.
    first_title = page.locator(SECTION_CARDS).first.locator(TITLE_INPUT)
    assert first_title.input_value() == "Summary"


def test_fill_name_updates_without_error(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    page.locator("input[placeholder='Jane Doe']").fill("Playwright Test User")
    page.wait_for_timeout(1500)
    assert page.locator("#toast.error").count() == 0
    _wait_preview(page)


def test_add_custom_section_and_rename(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector(".section-add select")
    page.select_option(".section-add select", "custom")
    page.locator(".section-add .btn.primary").click()
    last = page.locator(SECTION_CARDS).last
    last.locator(TITLE_INPUT).fill("Awards")
    page.wait_for_timeout(600)
    assert last.locator(TITLE_INPUT).input_value() == "Awards"
    # the custom entry editor exposes a Title field
    assert last.locator("input[placeholder='Item title']").count() == 1


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
    assert area.evaluate("el => el.tagName") == "TEXTAREA"
    area.fill("x" * 240)
    page.wait_for_timeout(300)
    # wrapped: content taller than the visible box
    assert area.evaluate("el => el.scrollHeight > el.clientHeight + 2")


def test_experience_highlights_is_wrapping_textarea(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(SECTION_CARDS)
    # Experience is the 3rd section in defaults (index 2).
    exp = page.locator(SECTION_CARDS).nth(2)
    exp.locator("button:has-text('Add highlight')").first.click()
    ta = exp.locator("textarea[placeholder='Achievement or responsibility']").first
    assert ta.evaluate("el => el.tagName") == "TEXTAREA"


def test_validation_error_shown(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("input[placeholder='you@example.com']")
    page.locator("input[placeholder='you@example.com']").fill("not-an-email")
    page.locator("#preview-btn").click()
    page.wait_for_selector("#toast.error", timeout=8000)
    assert "email" in page.locator("#toast").inner_text().lower()


def test_download_pdf(page, base_url, tmp_path: pathlib.Path):
    page.goto(base_url)
    _wait_preview(page)
    with page.expect_download() as dl:
        page.locator("#download-btn").click()
    download = dl.value
    target = tmp_path / "resume.pdf"
    download.save_as(str(target))
    assert target.exists()
    assert target.read_bytes()[:4] == b"%PDF"


def test_bold_button_wraps_selection(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    area = page.locator("textarea[placeholder='Write a short professional summary…']").first
    area.fill("Hello world test")
    area.evaluate("el => { el.setSelectionRange(6, 11); el.focus(); }")
    page.locator(".format-toolbar--global [data-action='bold']").click()
    assert area.input_value() == "Hello **world** test"


def test_italic_button_wraps_selection(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    area = page.locator("textarea[placeholder='Write a short professional summary…']").first
    area.fill("Hello world test")
    area.evaluate("el => { el.setSelectionRange(6, 11); el.focus(); }")
    page.locator(".format-toolbar--global [data-action='italic']").click()
    assert area.input_value() == "Hello *world* test"


def test_bold_button_inserts_markers_at_cursor(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    area = page.locator("textarea[placeholder='Write a short professional summary…']").first
    area.fill("Hello")
    area.evaluate("el => { el.setSelectionRange(5, 5); el.focus(); }")
    page.locator(".format-toolbar--global [data-action='bold']").click()
    assert area.input_value() == "Hello****"
    assert area.evaluate("el => el.selectionStart") == 7
    assert area.evaluate("el => el.selectionEnd") == 7


def test_bold_button_works_on_any_textarea(page, base_url):
    page.goto(base_url)
    page.wait_for_selector(SECTION_CARDS)
    skills_details = page.locator("textarea[placeholder^='Python']").first
    skills_details.fill("Python Go Rust")
    skills_details.evaluate("el => { el.setSelectionRange(7, 9); el.focus(); }")
    page.locator(".format-toolbar--global [data-action='bold']").click()
    assert skills_details.input_value() == "Python **Go** Rust"


def test_bold_button_works_on_text_input(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    company = page.locator("input[placeholder='Acme Inc.']").first
    company.fill("Acme Corp")
    company.evaluate("el => { el.setSelectionRange(5, 9); el.focus(); }")
    page.locator(".format-toolbar--global [data-action='bold']").click()
    assert company.input_value() == "Acme **Corp**"


def test_form_data_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#editor")
    page.locator("input[placeholder='Jane Doe']").fill("Alice Smith")
    page.locator("input[placeholder='Software Engineer']").fill("Senior Developer")
    page.reload()
    _wait_preview(page)
    assert page.locator("input[placeholder='Jane Doe']").input_value() == "Alice Smith"
    assert page.locator("input[placeholder='Software Engineer']").input_value() == "Senior Developer"


def test_theme_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#theme-select")
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'moderncv', accent: '#4f46e5', pageSize: 'a4', showFooter: false }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    assert page.locator("#theme-select").input_value() == "moderncv"


def test_accent_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#accent-color")
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'engineeringresumes', accent: '#ff0000', pageSize: 'a4', showFooter: false }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    saved = page.evaluate("() => JSON.parse(localStorage.getItem('rendercv_state') || '{}')")
    assert saved.get("design", {}).get("accent") == "#ff0000"
    assert page.locator("#accent-color").input_value().lower() == "#ff0000"


def test_sections_persist_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector(SECTION_CARDS)
    page.select_option(".section-add select", "custom")
    page.locator(".section-add .btn.primary").click()
    page.wait_for_selector(SECTION_CARDS)
    last_title = page.locator(SECTION_CARDS).last.locator("input[placeholder='Section title']")
    last_title.fill("Awards")
    page.wait_for_timeout(500)
    page.reload()
    _wait_preview(page)
    values = page.evaluate("() => Array.from(document.querySelectorAll('input[placeholder=\"Section title\"]')).map(el => el.value)")
    assert "Awards" in values


def test_empty_form_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#editor")
    page.reload()
    _wait_preview(page)
    assert page.locator("input[placeholder='Jane Doe']").input_value() == "**Vatsal Gupta**"
    assert page.locator("input[placeholder='you@example.com']").input_value() == "xyz@gmail.com"


def test_special_characters_persist_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#editor")
    page.locator("input[placeholder='Jane Doe']").fill("José García 日本語 🎉")
    page.reload()
    _wait_preview(page)
    assert page.locator("input[placeholder='Jane Doe']").input_value() == "José García 日本語 🎉"


def test_bold_on_empty_selection_inserts_markers(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    area = page.locator("textarea[placeholder='Write a short professional summary…']").first
    area.fill("Hello world")
    area.evaluate("el => { el.setSelectionRange(0, 0); el.focus(); }")
    page.locator(".format-toolbar--global [data-action='bold']").click()
    assert area.input_value() == "****Hello world"


def test_italic_on_empty_selection_inserts_markers(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("#editor")
    area = page.locator("textarea[placeholder='Write a short professional summary…']").first
    area.fill("Hello world")
    area.evaluate("el => { el.setSelectionRange(0, 0); el.focus(); }")
    page.locator(".format-toolbar--global [data-action='italic']").click()
    assert area.input_value() == "**Hello world"


def test_remove_section_and_persist(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector(SECTION_CARDS)
    initial_count = page.locator(SECTION_CARDS).count()
    cards = page.locator(SECTION_CARDS)
    cards.nth(0).locator("button.card-remove").click()
    page.wait_for_timeout(500)
    assert page.locator(SECTION_CARDS).count() == initial_count - 1
    page.reload()
    _wait_preview(page)
    assert page.locator(SECTION_CARDS).count() == initial_count - 1


def test_multiple_sections_persist(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector(SECTION_CARDS)
    for label in ["Projects", "Certifications", "Custom"]:
        page.select_option(".section-add select", label.lower())
        page.locator(".section-add .btn.primary").click()
        page.wait_for_selector(SECTION_CARDS)
    page.reload()
    _wait_preview(page)
    titles = page.evaluate("() => Array.from(document.querySelectorAll('input[placeholder=\"Section title\"]')).map(el => el.value)")
    assert "Projects" in titles
    assert "Certifications" in titles
    assert "Custom Section" in titles


def test_corrupted_localstorage_falls_back_to_defaults(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.setItem('rendercv_state', 'not-json')")
    page.reload()
    _wait_preview(page)
    assert page.locator("input[placeholder='Jane Doe']").input_value() == "**Vatsal Gupta**"


def test_autopreview_toggle_persists(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#autopreview")
    page.uncheck("#autopreview")
    page.wait_for_timeout(500)
    saved = page.evaluate("() => JSON.parse(localStorage.getItem('rendercv_state') || '{}')")
    assert saved.get("ui", {}).get("autopreview") == False
    page.goto(base_url)
    _wait_preview(page)
    assert not page.locator("#autopreview").is_checked()


def test_partial_state_merges_with_defaults(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#theme-select")
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'moderncv', accent: '#ff0000', pageSize: 'a4', showFooter: false }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    assert page.locator("#theme-select").input_value() == "moderncv"
    assert page.locator("input[placeholder='Jane Doe']").input_value() == "**Vatsal Gupta**"
    assert page.locator("input[placeholder='you@example.com']").input_value() == "xyz@gmail.com"


def test_empty_new_section_entries_do_not_break_render(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector(".section-add select")
    page.select_option(".section-add select", "custom")
    page.locator(".section-add .btn.primary").click()
    page.wait_for_selector(SECTION_CARDS)
    page.reload()
    _wait_preview(page)
    titles = page.evaluate("() => Array.from(document.querySelectorAll('input[placeholder=\"Section title\"]')).map(el => el.value)")
    assert "Custom Section" in titles


def test_corrupted_design_state_falls_back_to_defaults(page, base_url):
    page.goto(base_url)
    page.evaluate("""() => {
      localStorage.setItem('rendercv_state', JSON.stringify({
        design: { theme: 'nonexistent-theme' }
      }));
    }""")
    page.goto(base_url)
    _wait_preview(page)
    assert page.locator("#theme-select").input_value() == "engineeringresumes"
    assert page.locator("input[placeholder='Jane Doe']").input_value() == "**Vatsal Gupta**"


def test_long_text_persists_after_refresh(page, base_url):
    page.goto(base_url)
    page.evaluate("() => localStorage.removeItem('rendercv_state')")
    page.wait_for_selector("#editor")
    long_text = "A" * 5000
    page.locator("textarea[placeholder='Write a short professional summary…']").first.fill(long_text)
    page.reload()
    _wait_preview(page)
    assert page.locator("textarea[placeholder='Write a short professional summary…']").first.input_value() == long_text
