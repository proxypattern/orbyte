def get_filters():
    def reverse(value: str) -> str:
        return str(value)[::-1]

    return {"reverse": reverse}
