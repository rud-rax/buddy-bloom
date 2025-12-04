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

    def create_user(self, user_id: str, username: str, password_hash: str, name: str = None, email: str = None, bio: str = None):
        """Create a user idempotently by username.

        If the username already exists the existing node is returned and not duplicated.
        """
        with self.driver.session() as session:
            # Use MERGE on username to make creation idempotent. Only set fields on create.
            result = session.run(
                """
                MERGE (u:User {username: $username})
                ON CREATE SET u.userId = $userId, u.passwordHash = $passwordHash, u.name = $name, u.email = $email, u.bio = $bio
                RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash, u.name AS name, u.email AS email, u.bio = $bio
                """,
                userId=user_id,
                username=username,
                passwordHash=password_hash,
                name=name,
                email=email,
                bio=bio,
            )
            record = result.single()
            return record.data() if record else None

    def get_user(self, user_id: str):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {userId: $userId}) RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash, u.name AS name, u.email AS email, u.followersCount AS followersCount, u.followingCount AS followingCount, u.bio AS bio",
                userId=user_id,
            )
            record = result.single()
            return record.data() if record else None

    def get_user_by_username(self, username: str):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {username: $username}) RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash, u.name AS name, u.email AS email, u.followersCount AS followersCount, u.followingCount AS followingCount, u.bio AS bio",
                username=username,
            )
            record = result.single()
            return record.data() if record else None

    def update_user(self, user_id: str, username: Optional[str] = None, password_hash: Optional[str] = None, name: Optional[str] = None, email: Optional[str] = None, bio=None):
        """
        Updates fields on a user node based on provided, non-None values.
        Returns the updated user's basic data.
        """
        with self.driver.session() as session:
            set_clauses = []
            params = {"userId": user_id}
            
            if username is not None:
                set_clauses.append("u.username = $username")
                params["username"] = username
            if password_hash is not None:
                set_clauses.append("u.passwordHash = $password_hash")
                params["password_hash"] = password_hash
            if name is not None:
                set_clauses.append("u.name = $name")
                params["name"] = name
            if email is not None:
                set_clauses.append("u.email = $email")
                params["email"] = email
            if bio is not None:
                set_clauses.append("u.bio = $bio")
                params["bio"] = bio
                
            if not set_clauses:
                return None
            
            set_clause_str = ", ".join(set_clauses)
            query = f"""
            MATCH (u:User {{userId: $userId}}) 
            SET {set_clause_str} 
            RETURN u.userId AS userId, u.username AS username, u.passwordHash AS passwordHash, 
                   u.name AS name, u.email AS email, u.bio AS bio, 
                   u.followersCount AS followersCount, u.followingCount AS followingCount
            """
            result = session.run(query, parameters=params)
            record = result.single()
            return record.data() if record else None

    def delete_user(self, user_id: str):
        with self.driver.session() as session:
            session.run("MATCH (u:User {userId: $userId}) DELETE u", userId=user_id)

    def follow_user(self, follower_username: str, followee_username: str) -> bool:
        """
        Create a FOLLOWS relationship and increment the denormalized counts.
        Returns True if the relationship was created/updated, False otherwise.
        """
        if follower_username == followee_username:
            return False

        with self.driver.session() as session:
            # Cypher query to:
            # 1. Match the follower and followee nodes by their unique username.
            # 2. MERGE the FOLLOWS relationship (creates it if it doesn't exist).
            # 3. Use an ON CREATE clause to increment the counts ONLY if the relationship is new.
            # 4. Return the relationship to confirm success.
            query = """
            MATCH (follower:User {username: $follower_username})
            MATCH (followee:User {username: $followee_username})
            MERGE (follower)-[f:FOLLOWS]->(followee)
            ON CREATE SET f.since = datetime()
            ON CREATE SET 
                follower.followingCount = coalesce(follower.followingCount, 0) + 1,
                followee.followersCount = coalesce(followee.followersCount, 0) + 1
            RETURN f
            """
            result = session.run(
                query,
                follower_username=follower_username,
                followee_username=followee_username
            )
            # If a row is returned, the MERGE was successful (either created or matched)
            # However, the counter only increments on CREATE, which is what we want.
            return bool(result.single())

    def unfollow_user(self, follower_username: str, followee_username: str) -> bool:
        """
        Remove a FOLLOWS relationship and decrement the denormalized counts.
        Returns True if the relationship was deleted, False otherwise.
        """
        if follower_username == followee_username:
            return False

        with self.driver.session() as session:
            # Cypher query to:
            # 1. Match the relationship and the two nodes.
            # 2. DELETE the relationship.
            # 3. Conditional decrement: decrement the counters ONLY IF the relationship existed and was deleted.
            query = """
            MATCH (follower:User {username: $follower_username})-[f:FOLLOWS]->(followee:User {username: $followee_username})
            WITH follower, followee, f
            DELETE f
            SET 
                follower.followingCount = coalesce(follower.followingCount, 1) - 1,
                followee.followersCount = coalesce(followee.followersCount, 1) - 1
            RETURN follower, followee
            """
            result = session.run(
                query,
                follower_username=follower_username,
                followee_username=followee_username
            )
            # The result will be empty if the relationship didn't exist/wasn't deleted.
            return bool(result.single())

    def get_followers_for_user(self, username: str, skip: int = 0, limit: int = 100) -> list:
        """Return list of follower user dicts for `username`, with pagination."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (f:User)-[:FOLLOWS]->(u:User {username: $username})
                RETURN f.userId AS userId, f.username AS username, f.name AS name, f.email AS email,
                       f.followersCount AS followersCount, f.followingCount AS followingCount
                ORDER BY f.username SKIP $skip LIMIT $limit
                """,
                username=username,
                skip=skip,
                limit=limit,
            )
            return [r.data() for r in result]

    def get_following_for_user(self, username: str, skip: int = 0, limit: int = 100) -> list:
        """Return list of users that `username` follows, with pagination."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {username: $username})-[:FOLLOWS]->(followee:User)
                RETURN followee.userId AS userId, followee.username AS username, followee.name AS name, followee.email AS email,
                       followee.followersCount AS followersCount, followee.followingCount AS followingCount
                ORDER BY followee.username SKIP $skip LIMIT $limit
                """,
                username=username,
                skip=skip,
                limit=limit,
            )
            return [r.data() for r in result]
        
    def get_mutual_connections(self, username1: str, username2: str):
        """Find users followed by BOTH username1 and username2."""
        with self.driver.session() as session:
            query = """
            MATCH (u1:User {username: $u1})-[:FOLLOWS]->(mutual:User)<-[:FOLLOWS]-(u2:User {username: $u2})
            RETURN mutual.userId AS userId, mutual.username AS username, mutual.name AS name, 
                   mutual.email AS email, mutual.bio AS bio,
                   mutual.followersCount AS followersCount, mutual.followingCount AS followingCount
            """
            result = session.run(query, u1=username1, u2=username2)
            return [r.data() for r in result]
        
    def get_friend_recommendations(self, username: str):
        """Recommend users that 'username's friends follow."""
        with self.driver.session() as session:
            # Logic:
            # 1. Start at 'u' (Me)
            # 2. Hop to 'friend' (People I follow)
            # 3. Hop to 'fof' (People they follow)
            # 4. WHERE clause: Ensure I don't already follow 'fof' AND 'fof' isn't me.
            # 5. RETURN 'fof' and count how many 'friend' nodes connect us (strength).
            query = """
            MATCH (u:User {username: $username})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(fof:User)
            WHERE NOT (u)-[:FOLLOWS]->(fof) AND u <> fof
            RETURN fof.userId AS userId, fof.username AS username, fof.name AS name, 
                   fof.email AS email, fof.bio AS bio,
                   fof.followersCount AS followersCount, fof.followingCount AS followingCount,
                   count(friend) as strength
            ORDER BY strength DESC
            LIMIT 5
            """
            result = session.run(query, username=username)
            return [r.data() for r in result]


if __name__ == "__main__":
    crud = UserCRUD(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print("Create:", crud.create_user("1", "alice", "fakehash"))
    print("Read:", crud.get_user("1"))
