"""RenderCV integration: turn structured resume data into a PDF."""

from __future__ import annotations

import pathlib
import shutil
import tempfile

from rendercv.cli.render_command.run_rendercv import (
    build_rendercv_dictionary_and_model,
)
from rendercv.exception import RenderCVUserValidationError
from rendercv.renderer.pdf_png import generate_pdf
from rendercv.renderer.typst import generate_typst

CONF_DIR = pathlib.Path(__file__).resolve().parent / "conf"


class RenderError(Exception):
    """Raised when the resume data cannot be rendered.

    Attributes:
        errors: A list of human readable validation messages.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _read_yaml(path: pathlib.Path) -> dict:
    from rendercv.schema.yaml_reader import read_yaml

    return read_yaml(path.read_text(encoding="utf-8"))


def get_defaults() -> dict:
    """Return the starting cv/design/locale/settings used to seed the form."""
    base = CONF_DIR
    defaults: dict[str, dict] = {}
    for key, filename in (
        ("cv", "resume.yaml"),
        ("design", "design.yaml"),
        ("locale", "locale.yaml"),
        ("settings", "settings.yaml"),
    ):
        data = _read_yaml(base / filename)
        # The YAML files wrap content under a single top-level key.
        defaults[key] = dict(next(iter(data.values())))
    return defaults


def get_themes() -> list[str]:
    from rendercv.schema.models.design.built_in_design import available_themes

    return list(available_themes)


def render_cv(data: dict) -> bytes:
    """Build a RenderCV model and compile it to PDF bytes.

    Args:
        data: A dict with ``cv``, ``design``, ``locale`` and ``settings`` keys.
            Each value is the inner content of the corresponding YAML block.

    Returns:
        The generated PDF as raw bytes.

    Raises:
        RenderError: If the data fails RenderCV schema validation.
    """
    workdir = pathlib.Path(tempfile.mkdtemp(prefix="rendercv-web-"))
    try:
        cv = data.get("cv") or {}
        design = data.get("design") or {}
        locale = data.get("locale") or {}
        settings = data.get("settings") or {}

        # Compose a single YAML document rooting each block under its key.
        merged = {"cv": cv, "design": design, "locale": locale, "settings": settings}

        # Direct all generated artifacts into the temp work directory.
        settings.setdefault("render_command", {})
        overrides = {
            "output_folder": str(workdir / "out"),
            "dont_generate_markdown": True,
            "dont_generate_html": True,
            "dont_generate_png": True,
            "dont_generate_typst": False,
            "dont_generate_pdf": False,
        }
        for key, value in overrides.items():
            settings["render_command"][key] = value

        try:
            _, model = build_rendercv_dictionary_and_model(
                main_yaml_file=_to_yaml(merged),
                input_file_path=workdir / "resume.yaml",
            )
        except RenderCVUserValidationError as exc:
            messages = []
            for e in exc.validation_errors:
                loc = getattr(e, "schema_location", "") or ""
                if isinstance(loc, (list, tuple)):
                    loc = ".".join(str(p) for p in loc)
                messages.append(f"{loc}: {getattr(e, 'message', '') or ''}")
            raise RenderError(messages or [str(exc)])

        typst_path = generate_typst(model)
        pdf_path = generate_pdf(model, typst_path)
        if pdf_path is None or not pdf_path.exists():
            raise RenderError(["PDF generation failed unexpectedly."])
        return pdf_path.read_bytes()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _to_yaml(data: dict) -> str:
    import ruamel.yaml

    yaml = ruamel.yaml.YAML()
    yaml.default_flow_style = False
    stream = ruamel.yaml.compat.StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()
