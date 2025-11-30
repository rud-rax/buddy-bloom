import sys
import uuid
import getpass
from typing import Optional

from app.database import UserCRUD, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from app.services.user_service import UserService
from app.repository.user_repository import UserRepository
from app.models import User

def display_profile(user: User):
    """Displays the user's profile information."""
    print("\n--- Your Profile ---")
    print(f"  User ID: {user.userId}")
    print(f"  Username: {user.username}")
    print(f"  Name: {user.name}")
    print(f"  Email: {user.email}")
    # Display computed/relationship counts (initial values from model if not fetched)
    print(f"  Followers: {user.followersCount}")
    print(f"  Following: {user.followingCount}")
    print("----------------------\n")

def edit_profile_flow(service: UserService, current_user: User) -> Optional[User]:
    print("\n--- Edit Profile ---")
    print(f"Current Name: {current_user.name}")
    new_name = input("Enter new Name (or press Enter to keep current): ").strip()
    
    print(f"Current Email: {current_user.email}")
    new_email = input("Enter new Email (or press Enter to keep current): ").strip()

    print("\n--- Change Password ---")
    new_password = getpass.getpass("Enter new Password (or press Enter to keep current): ")
    
    password_to_update = None
    if new_password:
        confirm = getpass.getpass("Confirm new Password: ")
        if new_password != confirm:
            print("Passwords do not match. Password not updated.")
            new_password = None
        else:
            password_to_update = new_password

    name_to_update = new_name if new_name else None
    email_to_update = new_email if new_email else None
    
    if not name_to_update and not email_to_update and not password_to_update:
        print("No changes specified.")
        return current_user

    try:
        updated_user = service.update_profile(
            current_user.userId, 
            name=name_to_update, 
            email=email_to_update, 
            new_password=password_to_update
        )
        
        if updated_user:
            print("Profile updated successfully!")
            return updated_user
        else:
            print("Failed to update profile. User ID may be invalid or no changes were made.")
            return current_user

    except Exception as e:
        print(f"An error occurred during update: {e}")
        return current_user

def logged_in_menu(service: UserService, current_user: User):
    """Menu shown after a user successfully logs in."""
    while True:
        print(f"\n=== Buddy-Bloom Console: Logged in as {current_user.username} ===\n")
        print("1) View Profile")
        print("2) Edit Profile")
        print("3) Logout")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            display_profile(current_user)

        elif choice == "2":
            current_user = edit_profile_flow(service, current_user)
            
        elif choice == "3":
            print("Logged out successfully.")
            return None # Signal to the main function to return to the pre-login menu
        
        else:
            print("Invalid choice. Please select 1, 2 or 3.")
            
        # Ensure the menu uses the potentially updated current_user for the next iteration
        if current_user is None:
            return None

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

    current_user: Optional[User] = None

    print("\n=== Buddy-Bloom Console: Signup / Login ===\n")
    while True:
        if current_user:
            # If logged in, pass control to the logged_in_menu
            current_user = logged_in_menu(service, current_user)
            continue

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
                current_user = user
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
