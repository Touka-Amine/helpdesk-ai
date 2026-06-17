"""Authentication middleware scaffold."""


def verify_token(token: str) -> bool:
    return bool(token)
