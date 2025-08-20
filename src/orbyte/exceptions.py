class TemplateLookupError(FileNotFoundError):
    """Raised when a template identifier cannot be resolved in any search path."""


class MissingVariableError(KeyError):
    """Raised when Jinja fails due to a missing variable under StrictUndefined."""
