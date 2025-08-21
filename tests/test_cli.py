import json
from pathlib import Path
from typer.testing import CliRunner

import pytest

from orbyte.cli import app


runner = CliRunner()


def write_template(
    base: Path, identifier: str, content: str, locale: str | None = None
):
    name = f"{identifier}.{locale}.j2" if locale else f"{identifier}.j2"
    (base / name).write_text(content, encoding="utf-8")


@pytest.fixture()
def tmp_prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_cli_render_basic(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ name }}!")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            '{"name": "World"}',
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Hello World!" in result.stdout


def test_cli_render_with_locale(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ name }}!", locale="en")
    write_template(tmp_prompts_dir, "greeting", "Hola {{ name }}!", locale="es")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--locale",
            "es",
            "--vars",
            '{"name": "Mundo"}',
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Hola Mundo!" in result.stdout


def test_cli_render_with_vars_file(tmp_prompts_dir: Path, tmp_path: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ name }}!")

    vars_file = tmp_path / "vars.json"
    vars_file.write_text('{"name": "File"}', encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            f"@{vars_file}",
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Hello File!" in result.stdout


def test_cli_render_invalid_json(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello World!")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            "{invalid json}",
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code != 0
    # The error is raised as an exception, check the exception message
    assert result.exception is not None
    assert "JSON" in str(result.exception)


def test_cli_list_identifiers(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello!")
    write_template(tmp_prompts_dir, "welcome", "Welcome!", locale="en")
    write_template(tmp_prompts_dir, "welcome", "Bienvenido!", locale="es")

    result = runner.invoke(
        app,
        [
            "list",
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code == 0
    identifiers = result.stdout.strip().split("\n")
    assert "greeting" in identifiers
    assert "welcome" in identifiers


def test_cli_explain_resolution(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello!", locale="en")

    result = runner.invoke(
        app,
        [
            "explain",
            "greeting",
            "--locale",
            "es",
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code == 0
    explanation = json.loads(result.stdout)
    assert explanation["identifier"] == "greeting"
    assert explanation["locale"] == "es"
    assert explanation["chosen"] is not None
    assert "candidates" in explanation


def test_cli_render_missing_template(tmp_prompts_dir: Path):
    result = runner.invoke(
        app,
        [
            "render",
            "nonexistent",
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code != 0


def test_cli_render_with_default_locale_fallback(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ name }}!", locale="en")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--locale",
            "fr",
            "--vars",
            '{"name": "World"}',
            "--prompts-path",
            str(tmp_prompts_dir),
            "--default-locale",
            "en",
        ],
    )

    assert result.exit_code == 0
    assert "Hello World!" in result.stdout


def test_cli_render_with_env_prompts_path(
    tmp_prompts_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ name }}!")

    monkeypatch.setenv("ORBYTE_PROMPTS_PATH", str(tmp_prompts_dir))

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            '{"name": "Env"}',
        ],
    )

    assert result.exit_code == 0
    assert "Hello Env!" in result.stdout


def test_cli_render_with_sandbox_mode(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ name }}!")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            '{"name": "Safe"}',
            "--prompts-path",
            str(tmp_prompts_dir),
            "--sandbox",
        ],
    )

    assert result.exit_code == 0
    assert "Hello Safe!" in result.stdout


def test_cli_render_empty_vars(tmp_prompts_dir: Path):
    write_template(tmp_prompts_dir, "greeting", "Hello World!")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--prompts-path",
            str(tmp_prompts_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Hello World!" in result.stdout
