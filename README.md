# Orbyte

A lightweight Python library and CLI for managing AI prompt templates with Jinja2, i18n fallback, and simple filesystem conventions.

## Features

*   **Template Rendering:** Uses Jinja2 for powerful and flexible templating.
*   **I18n Integration:** Supports locale fallback for internationalization.
*   **Directory Structure:** Follows a simple and organized directory structure for your prompts.
*   **CLI:** Includes a command-line interface for testing and rendering prompts.

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/wilburhimself/orbyte.git
    cd orbyte
    ```

2.  Create a virtual environment and install the dependencies:

    ```bash
    uv venv
    uv pip install -e .
    ```

Alternatively (once published on PyPI):

```bash
pip install orbyte
```

## Usage

### As a Library

To use Orbyte as a library, import `Orbyte` and point it at your prompts folder. You can set the path via constructor, environment variable, or CLI option.

```python
from orbyte import Orbyte

# Option A: pass the prompts path explicitly
ob = Orbyte(prompts_path="/absolute/path/to/prompts")

# Option B: rely on ORBYTE_PROMPTS_PATH (takes effect if constructor arg is omitted)
#   export ORBYTE_PROMPTS_PATH=/absolute/path/to/prompts
#   ob = Orbyte()

prompt = ob.render(
    "user_onboarding/welcome_email",
    locale="es",
    name="María García",
    app_name="ProjectHub",
    user_role="Team Lead",
    features=["Create projects", "Invite team members", "Track progress", "Generate reports"],
    days_since_signup=2
)

print(prompt)
```

### Command-Line Interface

You can also use the command-line interface to render prompts:

```bash
# Option A: pass prompts path explicitly
.venv/bin/orbyte user_onboarding/welcome_email \
  --prompts-path /absolute/path/to/prompts \
  --locale es \
  --vars '{"name": "Wilbur", "app_name": "Orbyte", "user_role": "Admin", "features": ["A", "B"], "days_since_signup": 1}'

# Option B: use environment variable
export ORBYTE_PROMPTS_PATH=/absolute/path/to/prompts
.venv/bin/orbyte user_onboarding/welcome_email --locale es --vars '{"name": "Wilbur"}'
```

## Directory Structure

Orbyte expects your prompts to be organized in the following directory structure:

```
prompts/
├── user_onboarding/
│   ├── welcome_email.en.j2
│   └── welcome_email.es.j2
└── another_prompt.j2
```

When you call `render("user_onboarding/welcome_email")`, Orbyte will look for the following files in order:

1.  `user_onboarding/welcome_email.<locale>.j2` (e.g., `user_onboarding/welcome_email.es.j2`)
2.  `user_onboarding/welcome_email.<default_locale>.j2` (e.g., `user_onboarding/welcome_email.en.j2`)
3.  `user_onboarding/welcome_email.j2`

