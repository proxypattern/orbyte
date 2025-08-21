from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from orbyte.cli import app


def test_cli_render_with_filters_dict(
    tmp_prompts_dir: Path, write_template, runner: CliRunner, tmp_path: Path
):
    write_template(tmp_prompts_dir, "custom", "Hello {{ name|shout }}", locale="en")
    filters_py = tmp_path / "filters.py"
    filters_py.write_text(
        "def shout(v):\n    return str(v).upper() + '!'\nFILTERS = {'shout': shout}\n",
        encoding="utf-8",
    )
    r = runner.invoke(
        app,
        [
            "render",
            "custom",
            "--vars",
            '{"name":"Ada"}',
            "--prompts-path",
            str(tmp_prompts_dir),
            "--filters",
            str(filters_py),
        ],
    )
    assert r.exit_code == 0, r.output
    assert "Hello ADA!" in r.stdout


def test_cli_render_with_filters_factory(
    tmp_prompts_dir: Path, write_template, runner: CliRunner, tmp_path: Path
):
    write_template(tmp_prompts_dir, "custom", "{{ word|reverse }}")
    filters_py = tmp_path / "filters_factory.py"
    filters_py.write_text(
        "def get_filters():\n"
        "    def reverse(v):\n"
        "        return str(v)[::-1]\n"
        "    return {'reverse': reverse}\n",
        encoding="utf-8",
    )
    r = runner.invoke(
        app,
        [
            "render",
            "custom",
            "--vars",
            '{"word":"orbyte"}',
            "--prompts-path",
            str(tmp_prompts_dir),
            "--filters",
            str(filters_py),
        ],
    )
    assert r.exit_code == 0, r.output
    assert "etybro" in r.stdout  # reversed 'orbyte'
