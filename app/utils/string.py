import bcrypt


def hash_password(password: str) -> str:
    """Hash a password and return the hash as a UTF-8 string."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    """Check a password against a stored UTF-8 hash string."""
    if isinstance(hashed, str):
        hashed_bytes = hashed.encode("utf-8")
    else:
        hashed_bytes = hashed
    return bcrypt.checkpw(password.encode("utf-8"), hashed_bytes)


if __name__ == "__main__":
    # Quick manual test
    pw = "mysecret123"
    hashed_pw = hash_password(pw)
    print("Hashed password (str):", hashed_pw)
    print("Password correct?", check_password("mysecret123", hashed_pw))  # True
    print("Password correct?", check_password("wrong", hashed_pw))  # False