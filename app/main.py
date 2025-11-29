import sys
import uuid
import getpass

from app.database import UserCRUD, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from app.services.user_service import UserService
from app.repository.user_repository import UserRepository



def main():
    """Main entry point for Buddy-Bloom application"""
    try:
        crud = UserCRUD(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        sys.exit(1)

    # wire repository and service
    repository = UserRepository(crud)
    service = UserService(repository)

    print("\n=== Buddy-Bloom Console: Signup / Login ===\n")
    while True:
        print("1) Signup")
        print("2) Login")
        print("3) Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            # Signup flow using service
            username = input("Choose username: ").strip()
            email = input("Email: ").strip()
            name = input("Full name: ").strip()
            if not username or not email or not name:
                print("username, email and name are required")
                continue
            password = getpass.getpass("Choose password: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match.")
                continue
            created = service.register(username, email, name, password)
            if created:
                print(f"User created: {created.username} (userId={created.userId})")
            else:
                print("Failed to create user (may already exist)")

        elif choice == "2":
            username = input("Username: ").strip()
            if not username:
                print("Username required.")
                continue
            password = getpass.getpass("Password: ")
            user = service.authenticate(username, password)
            if user:
                print(f"Login successful. Welcome, {user.name} (userId={user.userId})")
            else:
                print("Invalid credentials.")

        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please select 1, 2 or 3.")
    try:
        del crud
    except Exception:
        pass

if __name__ == "__main__":
    main()
