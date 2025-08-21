import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

from orbyte import Orbyte
from orbyte.exceptions import TemplateLookupError


def write_template(
    base: Path, identifier: str, content: str, locale: Optional[str] = None
):
    name = f"{identifier}.{locale}.j2" if locale else f"{identifier}.j2"
    (base / name).write_text(content, encoding="utf-8")


@pytest.fixture()
def tmp_prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_render_with_specific_locale(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "welcome_email", "Hola {{ name }}", locale="es")
    write_template(tmp_prompts_dir, "welcome_email", "Hello {{ name }}", locale="en")

    ob = Orbyte([str(tmp_prompts_dir)], default_locale="en")

    es = ob.render("welcome_email", variables={"name": "Wilbur"}, locale="es")
    en = ob.render("welcome_email", variables={"name": "Wilbur"}, locale="en")

    assert es == "Hola Wilbur"
    assert en == "Hello Wilbur"


def test_render_falls_back_to_default_locale_when_requested_missing(
    tmp_prompts_dir: Path,
):
    write_template(tmp_prompts_dir, "welcome_email", "Hello {{ name }}", locale="en")

    ob = Orbyte([str(tmp_prompts_dir)], default_locale="en")

    result = ob.render("welcome_email", variables={"name": "Wilbur"}, locale="fr")
    assert result == "Hello Wilbur"


def test_render_falls_back_to_plain_identifier_when_no_locale_found(
    tmp_prompts_dir: Path,
):
    write_template(tmp_prompts_dir, "welcome_email", "Howdy {{ name }}")

    ob = Orbyte([str(tmp_prompts_dir)], default_locale="en")

    result = ob.render("welcome_email", variables={"name": "Wilbur"}, locale="fr")
    assert result == "Howdy Wilbur"


def test_render_raises_when_no_matching_template(tmp_prompts_dir: Path):
    ob = Orbyte([str(tmp_prompts_dir)], default_locale="en")
    with pytest.raises(TemplateLookupError):
        ob.render("missing_identifier", locale="en")


def run_cli(cwd: str, args: list[str], env: Optional[dict] = None):
    cmd = [sys.executable, "-m", "orbyte", *args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env or os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_renders_with_vars_and_locale(tmp_path: Path, tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "welcome_email", "Hola {{ name }}", locale="es")
    out = run_cli(
        cwd=str(Path(__file__).resolve().parents[1]),
        args=[
            "welcome_email",
            "--locale",
            "es",
            "--vars",
            json.dumps({"name": "Wilbur"}),
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert out.returncode == 0, out.stderr or out.stdout
    assert out.stdout.strip() == "Hola Wilbur"


def test_cli_errors_on_invalid_json(tmp_path: Path, tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "welcome_email", "Hello", locale="en")
    out = run_cli(
        cwd=str(Path(__file__).resolve().parents[1]),
        args=[
            "welcome_email",
            "--vars",
            "{not-json}",
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert out.returncode == 1
    assert "Invalid JSON" in (out.stdout + out.stderr)


def test_cli_uses_env_prompts_path_when_flag_not_provided(
    tmp_path: Path, tmp_prompts_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    write_template(tmp_prompts_dir, "welcome_email", "Hello {{ name }}", locale="en")

    env = os.environ.copy()
    env["ORBYTE_PROMPTS_PATH"] = str(tmp_prompts_dir)

    out = run_cli(
        cwd=str(Path(__file__).resolve().parents[1]),
        args=[
            "welcome_email",
            "--vars",
            json.dumps({"name": "Wilbur"}),
        ],
        env=env,
    )

    assert out.returncode == 0
    assert out.stdout.strip() == "Hello Wilbur"
