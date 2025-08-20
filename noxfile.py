"""
Nox sessions for orbyte.
Usage examples:
  nox -s tests                 # run tests on all configured Python versions
  nox -s tests-3.12 -- -q      # run tests only on 3.12, pass extra args to pytest
  nox -s lint                  # ruff lint
  nox -s types                 # mypy type-check
  nox -s format                # ruff format (apply fixes)
  nox -s build                 # build sdist + wheel
"""

import nox

PYTHONS = ("3.9", "3.10", "3.11", "3.12", "3.13")

nox.options.reuse_existing_virtualenvs = True
nox.options.stop_on_first_error = False

LOCATIONS = ("src", "tests")


@nox.session(python=PYTHONS)
def tests(session: nox.Session) -> None:
    """Run pytest with coverage."""
    session.install("-e", ".[dev]")
    session.run("pytest", "-q", *session.posargs)


@nox.session
def lint(session: nox.Session) -> None:
    """Static analysis with ruff."""
    session.install("ruff>=0.5.0")
    session.run("ruff", "check", *LOCATIONS, *session.posargs)


@nox.session
def format(session: nox.Session) -> None:
    """Auto-format with ruff (safe fixes)."""
    session.install("ruff>=0.5.0")
    session.run("ruff", "format", *LOCATIONS, *session.posargs)
    session.run("ruff", "check", "--fix", *LOCATIONS, *session.posargs)


@nox.session
def types(session: nox.Session) -> None:
    """Type-check with mypy."""
    session.install("-e", ".[dev]")
    session.run("mypy", "src", "tests", *session.posargs)


@nox.session
def build(session: nox.Session) -> None:
    """Build sdist and wheel (validates packaging)."""
    session.install("build>=1.0.0")
    session.run("python", "-m", "build")
