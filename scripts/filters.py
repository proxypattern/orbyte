# Provide custom Jinja filters at runtime via --filters scripts/filters.py
def shout(value: str) -> str:
    return str(value).upper() + "!"


def surround(value: str, left: str = "[", right: str = "]") -> str:
    return f"{left}{value}{right}"


# The CLI will look for either FILTERS or get_filters()
FILTERS = {
    "shout": shout,
    "surround": surround,
}
