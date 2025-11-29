from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from typing import Optional

from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class UserCRUD:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()
        print("Connection to AuraDB established successfully!")
        # Ensure uniqueness constraint on username exists (idempotent)
        try:
            with self.driver.session() as session:
                session.run(
                    "CREATE CONSTRAINT user_username_unique IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE"
                )
                print("Ensured unique constraint on :User(username)")
        except Exception as e:
            # Log and continue; constraint creation may require appropriate privileges
            print(f"Warning: failed to create username uniqueness constraint: {e}")

    def __del__(self):
        try:
            self.driver.close()
        except Exception:
            pass

    def create_user(self, user_id: str, username: str, password_hash: str, name: str = None, email: str = None):
        """Create a user idempotently by username.

        If the username already exists the existing node is returned and not duplicated.
        """
        with self.driver.session() as session:
            # Use MERGE on username to make creation idempotent. Only set fields on create.
            result = session.run(
                """
                MERGE (u:User {username: $username})
                ON CREATE SET u.userId = $userId, u.passwordHash = $passwordHash, u.name = $name, u.email = $email
                RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash, u.name AS name, u.email AS email
                """,
                userId=user_id,
                username=username,
                passwordHash=password_hash,
                name=name,
                email=email,
            )
            record = result.single()
            return record.data() if record else None

    def get_user(self, user_id: str):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {userId: $userId}) RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash, u.name AS name, u.email AS email",
                userId=user_id,
            )
            record = result.single()
            return record.data() if record else None

    def get_user_by_username(self, username: str):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {username: $username}) RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash, u.name AS name, u.email AS email",
                username=username,
            )
            record = result.single()
            return record.data() if record else None

    def update_user(self, user_id: str, username: Optional[str] = None, password_hash: Optional[str] = None):
        with self.driver.session() as session:
            set_clauses = []
            params = {"userId": user_id}
            if username is not None:
                set_clauses.append("u.username = $username")
                params["username"] = username
            if password_hash is not None:
                set_clauses.append("u.passwordHash = $password_hash")
                params["password_hash"] = password_hash
            if not set_clauses:
                return None
            set_clause_str = ", ".join(set_clauses)
            query = f"MATCH (u:User {{userId: $userId}}) SET {set_clause_str} RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash"
            result = session.run(query, parameters=params)
            record = result.single()
            return record.data() if record else None

    def delete_user(self, user_id: str):
        with self.driver.session() as session:
            session.run("MATCH (u:User {userId: $userId}) DELETE u", userId=user_id)


if __name__ == "__main__":
    crud = UserCRUD(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print("Create:", crud.create_user("1", "alice", "fakehash"))
    print("Read:", crud.get_user("1"))
