import bcrypt

# Hashing
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Checking
def check_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

if __name__ == "__main__":
    # pw = "mysecret123"
    # hashed_pw = hash_password(pw)
    # print("Hashed password:", hashed_pw)
    
    # # Check correct password
    # print("Password correct?", check_password("mysecret123", hashed_pw))  # True
    
    # # Check incorrect password
    # print("Password correct?", check_password("anotherpassword", hashed_pw))  # False
    pass