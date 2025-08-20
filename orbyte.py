#!/usr/bin/env python

import os
import argparse
import json
from jinja2 import Environment, FileSystemLoader


class Orbyte:
    def __init__(self, prompts_path=None, default_locale="en"):
        # Determine prompts path: explicit arg > env var > default 'prompts'
        env_path = os.getenv("ORBYTE_PROMPTS_PATH")
        self.prompts_path = prompts_path or env_path or "prompts"
        self.default_locale = default_locale
        self.env = Environment(loader=FileSystemLoader(self.prompts_path))

    def render(self, identifier, locale=None, **kwargs):
        template_name = self._find_template(identifier, locale)
        if not template_name:
            raise FileNotFoundError(f"Template not found for identifier: {identifier}")

        template = self.env.get_template(template_name)
        return template.render(**kwargs)

    def _find_template(self, identifier, locale):
        # 1. Requested locale
        if locale:
            template_name = f"{identifier}.{locale}.j2"
            if os.path.exists(os.path.join(self.prompts_path, template_name)):
                return template_name

        # 2. Default locale
        template_name = f"{identifier}.{self.default_locale}.j2"
        if os.path.exists(os.path.join(self.prompts_path, template_name)):
            return template_name

        # 3. Fallback
        template_name = f"{identifier}.j2"
        if os.path.exists(os.path.join(self.prompts_path, template_name)):
            return template_name

        return None


def main():
    parser = argparse.ArgumentParser(description="Render a Jinja2 template.")
    parser.add_argument(
        "identifier", type=str, help="The identifier of the template to render."
    )
    parser.add_argument("--locale", type=str, help="The locale to use for rendering.")
    parser.add_argument(
        "--vars",
        type=str,
        help="A JSON string of key-value pairs to pass to the template.",
    )
    parser.add_argument(
        "--prompts-path",
        type=str,
        help="Path to the prompts directory. Overrides ORBYTE_PROMPTS_PATH env var.",
    )

    args = parser.parse_args()

    ob = Orbyte(prompts_path=args.prompts_path)

    if args.vars:
        try:
            template_vars = json.loads(args.vars)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for --vars.")
            exit(1)
    else:
        template_vars = {}

    prompt = ob.render(args.identifier, locale=args.locale, **template_vars)
    print(prompt)


if __name__ == "__main__":
    main()
