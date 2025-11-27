# from app.database import db_service
from utils.string import hash_password , check_password


def main():
    """Main entry point for Buddy-Bloom application"""
    
    try:
        print("\n=== Buddy-Bloom: User Registration & Fetch Test ===\n")

        pw = "mysecret123"
        hashed_pw = hash_password(pw)
        print("Hashed password:", hashed_pw)
        
        # Check correct password
        print("Password correct?", check_password("mysecret123", hashed_pw))  # True
        
        # Check incorrect password
        print("Password correct?", check_password("anotherpassword", hashed_pw))  # False)

        
    except Exception as e:
        print(f"\n✗ Error: {e}\n")
    finally:
        # Disconnect from Neo4j
        pass


if __name__ == "__main__":
    main()
