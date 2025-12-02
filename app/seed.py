import csv
import sys

from database import UserCRUD, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def seed_data():
    print(f"Connecting to Aura at {NEO4J_URI}...")
    try:
        crud = UserCRUD(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    # 1. Load Users
    print("\n--- Loading Users ---")
    users = []
    with open('../data/users.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert counts to integers if they exist, else default to 0
            row['followersCount'] = 0
            row['followingCount'] = 0
            users.append(row)

    if users:
        with crud.driver.session() as session:
            query = """
            UNWIND $rows AS row
            MERGE (u:User {username: row.username})
            SET u.userId = row.userId,
                u.name = row.name,
                u.email = row.email,
                u.passwordHash = row.passwordHash,
                u.bio = row.bio,
                u.followersCount = 0,
                u.followingCount = 0
            """
            session.run(query, rows=users)
            print(f"Successfully loaded {len(users)} users.")

    # 2. Load Connections
    print("\n--- Loading Connections ---")
    connections = []
    with open('../data/connections.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            connections.append(row)

    if connections:
        with crud.driver.session() as session:
            # Create relationships and update counts
            batch_size = 1000
            for i in range(0, len(connections), batch_size):
                batch = connections[i : i + batch_size]
                query = """
                UNWIND $rows AS row
                MATCH (follower:User {username: row.follower_username})
                MATCH (followee:User {username: row.followee_username})
                MERGE (follower)-[r:FOLLOWS]->(followee)
                ON CREATE SET 
                    r.since = datetime(),
                    follower.followingCount = coalesce(follower.followingCount, 0) + 1,
                    followee.followersCount = coalesce(followee.followersCount, 0) + 1
                """
                session.run(query, rows=batch)
                print(f"Processed batch {i} to {i + len(batch)}...")
            
            print(f"Successfully loaded {len(connections)} relationships.")
    
    # 3. Validation
    with crud.driver.session() as session:
        result = session.run("MATCH (u:User) RETURN count(u) as users").single()
        u_count = result['users']
        result = session.run("MATCH ()-[r:FOLLOWS]->() RETURN count(r) as rels").single()
        r_count = result['rels']
        print(f"\nFINAL DB STATUS: {u_count} Users, {r_count} Relationships.")
    
    crud.driver.close()

if __name__ == "__main__":
    seed_data()
