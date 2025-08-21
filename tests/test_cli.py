from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner


import pytest

from orbyte.cli import app


@pytest.fixture()
def tmp_prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_cli_render_basic(tmp_prompts_dir: Path, write_template, runner):
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


def test_cli_render_with_locale(tmp_prompts_dir: Path, write_template, runner):
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


def test_cli_render_with_vars_file(
    tmp_prompts_dir: Path, write_template, tmp_path: Path, runner
):
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


def test_cli_render_invalid_json(tmp_prompts_dir: Path, write_template, runner):
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
    assert result.exception is not None
    assert "JSON" in str(result.exception)  # message bubbles from Orbyte.parse_vars()


def test_cli_list_identifiers(tmp_prompts_dir: Path, write_template, runner):
    write_template(tmp_prompts_dir, "greeting", "Hello!")
    write_template(tmp_prompts_dir, "welcome", "Welcome!", locale="en")
    write_template(tmp_prompts_dir, "welcome", "Bienvenido!", locale="es")
    result = runner.invoke(app, ["list", "--prompts-path", str(tmp_prompts_dir)])
    assert result.exit_code == 0
    items = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert "greeting" in items
    assert "welcome" in items


def test_cli_list_non_recursive_only_top_level(
    tmp_prompts_dir: Path, write_template, runner
):
    write_template(tmp_prompts_dir, "root", "Top")
    nested = tmp_prompts_dir / "nested"
    write_template(nested, "child", "Child")
    result = runner.invoke(
        app, ["list", "--prompts-path", str(tmp_prompts_dir), "--non-recursive"]
    )
    assert result.exit_code == 0
    items = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert items == {"root"}


def test_cli_explain_resolution(tmp_prompts_dir: Path, write_template, runner):
    write_template(tmp_prompts_dir, "greeting", "Hello!", locale="en")
    result = runner.invoke(
        app,
        ["explain", "greeting", "--locale", "es", "--prompts-path", str(tmp_prompts_dir)],
    )
    assert result.exit_code == 0
    explanation = json.loads(result.stdout)
    assert explanation["identifier"] == "greeting"
    assert explanation["locale"] == "es"
    assert explanation["chosen"] is not None
    assert "candidates" in explanation


def test_cli_render_missing_template(tmp_prompts_dir: Path, runner):
    result = runner.invoke(
        app, ["render", "nonexistent", "--prompts-path", str(tmp_prompts_dir)]
    )
    assert result.exit_code != 0


def test_cli_render_with_default_locale_fallback(
    tmp_prompts_dir: Path, write_template, runner
):
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
    tmp_prompts_dir: Path, write_template, runner, monkeypatch
):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ name }}!")
    monkeypatch.setenv("ORBYTE_PROMPTS_PATH", str(tmp_prompts_dir))
    result = runner.invoke(app, ["render", "greeting", "--vars", '{"name": "Env"}'])
    assert result.exit_code == 0
    assert "Hello Env!" in result.stdout


def test_cli_render_with_sandbox_mode(tmp_prompts_dir: Path, write_template, runner):
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


def test_cli_render_empty_vars(tmp_prompts_dir: Path, write_template, runner: CliRunner):
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


def test_gettext_translations_success_via_dummy_babel(
    tmp_prompts_dir: Path, write_template, runner, install_dummy_babel, tmp_path: Path
):
    gettext_dir = tmp_path / "locale"
    gettext_dir.mkdir()
    write_template(tmp_prompts_dir, "greeting", "Hello {{ who }}")
    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            json.dumps({"who": "World"}),
            "--prompts-path",
            str(tmp_prompts_dir),
            "--gettext-dir",
            str(gettext_dir),
        ],
    )
    assert result.exit_code == 0
    assert "Hello World" in result.stdout


def test_list_non_recursive_only_top_level(
    tmp_prompts_dir: Path, write_template, runner: CliRunner
):
    # top-level
    write_template(tmp_prompts_dir, "root", "Top")
    # nested
    nested = tmp_prompts_dir / "nested"
    nested.mkdir()
    write_template(nested, "child", "Child")

    result = runner.invoke(
        app,
        [
            "list",
            "--prompts-path",
            str(tmp_prompts_dir),
            "--non-recursive",
        ],
    )
    assert result.exit_code == 0, result.stdout
    items = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    # Only the top-level identifier should appear
    assert items == {"root"}


def test_resolve_paths_invalid_directory_errors(tmp_path: Path, runner):
    bad = tmp_path / "does-not-exist"
    result = runner.invoke(app, ["list", "--prompts-path", str(bad)])
    assert result.exit_code != 0
    assert result.exception is not None
    assert "Prompts path does not exist" in str(result.exception)


def test_filters_file_not_found_raises(
    tmp_prompts_dir: Path, write_template, runner: CliRunner
):
    write_template(tmp_prompts_dir, "greeting", "Hello")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--prompts-path",
            str(tmp_prompts_dir),
            "--filters",
            str(tmp_prompts_dir / "missing_filters.py"),
        ],
    )
    assert result.exit_code != 0
    assert result.exception is not None
    assert "Filters file not found" in str(result.exception)


def test_filters_get_filters_wrong_type_raises(
    tmp_prompts_dir: Path, write_template, tmp_path: Path, runner: CliRunner
):
    write_template(tmp_prompts_dir, "greeting", "Hello {{ who }}")
    bad = tmp_path / "filters_bad.py"
    bad.write_text(
        "def get_filters():\n    return 42\n",  # not a dict
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            json.dumps({"who": "x"}),
            "--prompts-path",
            str(tmp_prompts_dir),
            "--filters",
            str(bad),
        ],
    )
    assert result.exit_code != 0
    assert result.exception is not None
    assert "get_filters() in filters module must return a dict" in str(result.exception)


def test_gettext_dir_is_not_directory_raises(
    tmp_prompts_dir: Path, write_template, tmp_path: Path, runner: CliRunner
):
    write_template(tmp_prompts_dir, "greeting", "Hello")
    not_a_dir = tmp_path / "file.txt"
    not_a_dir.write_text("x", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--prompts-path",
            str(tmp_prompts_dir),
            "--gettext-dir",
            str(not_a_dir),
        ],
    )
    assert result.exit_code != 0
    assert result.exception is not None
    assert "--gettext-dir must be a directory" in str(result.exception)


def test_gettext_translations_success_via_monkeypatched_babel(
    tmp_prompts_dir: Path,
    write_template,
    runner: CliRunner,
    install_dummy_babel,  # <-- provided by conftest.py
    tmp_path: Path,
):
    """
    Simulate Babel being installed by using the install_dummy_babel fixture,
    which injects a dummy `babel.support.Translations` into sys.modules.
    This exercises the success branch of `_load_translations`.
    """
    gettext_dir = tmp_path / "locale"
    gettext_dir.mkdir()

    # Template (no trans blocks—just ensure the code path succeeds)
    write_template(tmp_prompts_dir, "greeting", "Hello {{ who }}")

    result = runner.invoke(
        app,
        [
            "render",
            "greeting",
            "--vars",
            json.dumps({"who": "World"}),
            "--prompts-path",
            str(tmp_prompts_dir),
            "--gettext-dir",
            str(gettext_dir),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "Hello World" in result.stdout


def test_env_var_multiple_paths_dedup(tmp_path: Path, runner, monkeypatch):
    p1 = tmp_path / "p1"
    p1.mkdir()
    p2 = tmp_path / "p2"
    p2.mkdir()
    (p1 / "a.j2").write_text("x", encoding="utf-8")
    (p2 / "a.j2").write_text("y", encoding="utf-8")
    monkeypatch.setenv("ORBYTE_PROMPTS_PATH", f"{p1}:{p2}")
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    items = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert items == {"a"}
