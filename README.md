# Orbyte

[![CI](https://github.com/proxypattern/orbyte/actions/workflows/ci.yml/badge.svg)](https://github.com/proxypattern/orbyte/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/proxypattern/orbyte/branch/main/graph/badge.svg)](https://codecov.io/gh/proxypattern/orbyte)

Filesystem-first prompt templating with locale fallback, powered by **Jinja2**.

* Simple file layout: `identifier[.locale].j2`
* Locale fallback: `identifier.<locale>.j2 → identifier.<default_locale>.j2 → identifier.j2`
* Strict rendering (fail fast on missing vars via `StrictUndefined`)
* Works as both **CLI** and **library package**


## Installation

**Local dev:**

With uv (recommended):
```bash
uv sync --extra dev --extra i18n --extra cache
```

With pip:
```bash
pip install -e .
```
Then install dev dependencies separately:
```bash
pip install pytest pytest-cov mypy ruff nox types-click types-babel
```

**From GitHub:**

```bash
pip install "git+https://github.com/proxypattern/orbyte@main#egg=orbyte"
# with extras:
pip install "git+https://github.com/proxypattern/orbyte@main#egg=orbyte[i18n,cache]"
```

**From PyPI:**

```bash
pip install "orbyte[i18n,cache]"
```

Extras:

* `i18n` → Babel (gettext)
* `cache` → diskcache (optional, if you add persistent caching)


## Quick start (CLI)

```bash
# render a template
orbyte render greeting --vars '{"name":"Ada"}' --prompts-path examples/prompts
orbyte render greeting --locale es --vars '{"name":"Ada"}' --prompts-path examples/prompts

# list identifiers (base names without locale suffix)
orbyte list --prompts-path examples/prompts

# explain fallback chain
orbyte explain greeting --locale fr --prompts-path examples/prompts
```

You can also run via module:

```bash
python -m orbyte render greeting --vars '{"name":"Ada"}' --prompts-path examples/prompts
# or (shorthand) default to "render" when first arg isn't a subcommand:
python -m orbyte greeting --vars '{"name":"Ada"}' --prompts-path examples/prompts
```

Environment variable:

* `ORBYTE_PROMPTS_PATH="path1:path2"` is used when `--prompts-path` is not provided.


## Quick start (Library)

```python
# app/prompts/greeting.j2:  "Hello {{ name }}!"
from orbyte.core import Orbyte

ob = Orbyte(
    prompts_paths=["app/prompts"],
    default_locale="en",
)

print(ob.render("greeting", {"name": "Ada"}))
# -> "Hello Ada!"
```

Pass variables as kwargs too:

```python
ob.render("greeting", locale="en", name="Ada")
```

## File layout & fallback

```
examples/prompts/
├── greeting.j2
├── greeting.en.j2
└── greeting.es.j2
```

Resolution order:

1. `identifier.<locale>.j2`
2. `identifier.<default_locale>.j2`
3. `identifier.j2`


## Validation & Errors

* **Identifiers**: must be relative names (no absolute paths / `..` / trailing `.j2`).
* **Locales**: basic `en` / `en-US` pattern; underscores normalized to hyphens.
* **Prompts paths**: must exist and be directories.
* **Variables**: must be a mapping; missing variables raise `MissingVariableError`.
* **Template not found**: raises `TemplateLookupError` and shows all candidates tried.
* **`--vars` JSON**: provide a JSON string or `@file.json` path. Bad input triggers a helpful “Invalid JSON” error.

## CLI options (high-level)

* `--prompts-path` (repeatable): one or more directories to search.
* `--default-locale`: fallback default (default: `en`).
* `--locale`: desired locale for this render (`en`, `es`, `en-US`, …).
* `--vars`: JSON string or `@file.json`.
* `--filters`: Python file exporting `FILTERS` dict or `get_filters()` → dict.
* `--gettext-dir`: base directory for gettext `.mo` files (Babel).
* `--sandbox`: render with Jinja’s `SandboxedEnvironment`.
* `--bytecode-cache-dir`: directory for Jinja bytecode cache.

Examples:

```bash
# multiple prompt paths
orbyte list --prompts-path app/prompts --prompts-path team/prompts

# sandbox + bytecode cache
orbyte render email_welcome --vars '{"name":"Ada"}' \
  --prompts-path app/prompts \
  --sandbox \
  --bytecode-cache-dir .cache/jinja

# gettext i18n
orbyte render email_welcome --locale fr \
  --prompts-path app/prompts \
  --gettext-dir locale
```

## Custom Filters

Register filters at runtime via CLI or programmatically.

**CLI (recommended)** — `scripts/filters.py`

```python
def shout(value: str) -> str:
    return str(value).upper() + "!"

def surround(value: str, left: str = "[", right: str = "]") -> str:
    return f"{left}{value}{right}"

FILTERS = {"shout": shout, "surround": surround}
```

Use it:

```bash
orbyte render greeting \
  --vars '{"name":"Ada"}' \
  --prompts-path examples/prompts \
  --filters scripts/filters.py
```

Alternatively export a factory:

```python
# scripts/filters_factory.py
def get_filters():
    def reverse(value: str) -> str:
        return str(value)[::-1]
    return {"reverse": reverse}
```

**Library**

```python
from orbyte.core import Orbyte
ob = Orbyte(["examples/prompts"], extra_filters={"shout": lambda s: str(s).upper()+"!"})
print(ob.render("greeting", {"name": "Ada"}))  # can use {{ name|shout }} in template
```

## Gettext / Babel (optional)

Enable `{% trans %}` in templates by loading translations. Directory layout:

```
locale/
 └─ fr/
    └─ LC_MESSAGES/
       └─ messages.mo
```

**CLI**

```bash
orbyte render email_welcome --locale fr \
  --prompts-path app/prompts \
  --gettext-dir locale
```

**Library**

```python
from babel.support import Translations
from orbyte.core import Orbyte

translations = Translations.load("locale", ["fr"])
ob = Orbyte(["app/prompts"], default_locale="en", translations=translations)
```

## Sandbox & Bytecode Cache (optional)

```python
ob = Orbyte(
    ["app/prompts"],
    sandbox=True,                    # SandboxedEnvironment for untrusted templates
    bytecode_cache_dir=".cache/jinja"  # faster loads in production
)
```

## Using prompts bundled inside your package

Ship prompts inside your wheel and resolve a filesystem path with `importlib.resources`:

```python
from importlib.resources import files, as_file
from orbyte.core import Orbyte

prompts_resource = files("myapp") / "prompts"
with as_file(prompts_resource) as p:
    ob = Orbyte([str(p)], default_locale="en")
    print(ob.render("greeting", {"name": "Ada"}))
```

> Ensure your package includes the files (e.g., via your build backend’s include settings).


## Nox (local dev task runner)

We include a `noxfile.py` so you can run tests, lint, types, and builds in isolated virtualenvs.

Common commands:

```bash
# run tests on all configured Python versions
nox -s tests

# run tests only on Python 3.12 and pass extra args to pytest
nox -s tests-3.12 -- -q -k cli

# ruff lint and format
nox -s lint
nox -s format

# mypy type-checks
nox -s types

# build sdist + wheel
nox -s build
```

> Install nox once with `pipx install nox` (or `pip install nox`).
> If you don’t have all interpreters locally, run a specific session like `nox -s tests-3.12`.


## Development

With uv (recommended):
```bash
# clone
git clone https://github.com/proxypattern/orbyte
cd orbyte

# install
uv sync --extra dev --extra i18n --extra cache

# quality gate
ruff check .
mypy src tests
pytest -q
```

With pip:
```bash
# clone
git clone https://github.com/proxypattern/orbyte
cd orbyte

# install
pip install -e .
pip install pytest pytest-cov mypy ruff nox types-click types-babel

# quality gate
ruff check .
mypy src tests
pytest -q
```

## CI & Release (GitHub Actions)

* **CI**: lint, mypy, pytest across Python 3.9–3.12.
* **Release**: tag `v*` builds wheels and publishes to PyPI via **Trusted Publishing**.

Tagging a release:

```bash
git tag v0.1.0
git push origin v0.1.0
```
