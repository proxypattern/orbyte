from pathlib import Path
from typer.testing import CliRunner

from orbyte.cli import app

runner = CliRunner()


def test_cli_render_with_filters_dict(tmp_path: Path):
    # Arrange: prompts and filters file
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "custom.en.j2").write_text("Hello {{ name|shout }}", encoding="utf-8")

    filters_py = tmp_path / "filters.py"
    filters_py.write_text(
        "def shout(v):\n    return str(v).upper() + '!'\nFILTERS = {'shout': shout}\n",
        encoding="utf-8",
    )

    # Act
    r = runner.invoke(
        app,
        [
            "render",
            "custom",
            "--vars",
            '{"name":"Ada"}',
            "--prompts-path",
            str(prompts),
            "--filters",
            str(filters_py),
        ],
    )

    # Assert
    assert r.exit_code == 0, r.output
    assert "Hello ADA!" in r.stdout


def test_cli_render_with_filters_factory(tmp_path: Path):
    # Arrange
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "custom.j2").write_text("{{ word|reverse }}", encoding="utf-8")

    filters_py = tmp_path / "filters_factory.py"
    filters_py.write_text(
        "def get_filters():\n"
        "    def reverse(v):\n"
        "        return str(v)[::-1]\n"
        "    return {'reverse': reverse}\n",
        encoding="utf-8",
    )

    # Act
    r = runner.invoke(
        app,
        [
            "render",
            "custom",
            "--vars",
            '{"word":"orbyte"}',
            "--prompts-path",
            str(prompts),
            "--filters",
            str(filters_py),
        ],
    )

    # Assert
    assert r.exit_code == 0, r.output
    assert "etybro" in r.stdout
