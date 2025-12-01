import csv
import random
import bcrypt

# Configuration
EDGE_FILE = 'gplus_combined.txt'
USERS_CSV = 'users.csv'
CONNECTIONS_CSV = 'connections.csv'
TARGET_NODE_COUNT = 1500
TARGET_PASSWORD = 'password123'

# Data structures to hold results
unique_ids = set()
processed_edges = []

def hash_password(password: str) -> str:
    """Hash a password and return the hash as a UTF-8 string."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

print(f"Reading edges from {EDGE_FILE}...")

# 1. Collect unique IDs and edges
try:
    with open(EDGE_FILE, 'r') as f:
        # Use a list to maintain the order of IDs collected, ensuring we process the 'first' N nodes
        ordered_ids = [] 
        
        for line in f:
            line = line.strip()
            if not line:
                continue

            # ID_A follows ID_B (directed edge)
            parts = line.split()
            if len(parts) == 2:
                id_a, id_b = parts[0], parts[1]
                
                # Check if this ID is new and if we are still collecting users
                for uid in [id_a, id_b]:
                    if uid not in unique_ids:
                        unique_ids.add(uid)
                        ordered_ids.append(uid)
                        
                # Only process edges where both IDs are in our target set (or haven't been filtered out yet)
                if id_a in unique_ids and id_b in unique_ids:
                    processed_edges.append((id_a, id_b))
                
                # Stop processing after reaching the target node count
                if len(unique_ids) >= TARGET_NODE_COUNT:
                    break

except FileNotFoundError:
    print(f"Error: {EDGE_FILE} not found. Ensure it is in the same directory as the script.")
    exit()

print(f"Collected {len(unique_ids)} unique nodes and {len(processed_edges)} edges.")

# Ensure we meet the minimum requirements
if len(unique_ids) < 1000 or len(processed_edges) < 5000:
    print("Warning: Did not meet minimum node/edge count. You may need a larger subset.")

### Step 2: Generate Functional User Properties (Augmentation)

# Generate a single hashed password to use for all imported users
DEFAULT_HASH = hash_password(TARGET_PASSWORD)

user_data = []
for i, raw_id in enumerate(ordered_ids):
    # Generate unique, synthetic properties
    username = f"user_{raw_id}"
    name = f"Graph User {i+1}"
    email = f"user_{raw_id}@gplus.com"
    
    user_data.append({
        'userId': raw_id,
        'username': username,
        'name': name,
        'email': email,
        'passwordHash': DEFAULT_HASH
    })

# Create a mapping dictionary for relationship creation
id_to_username = {u['userId']: u['username'] for u in user_data}

### Step 3: Create CSV Files

# 1. Write Users CSV
with open(USERS_CSV, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['userId', 'username', 'name', 'email', 'passwordHash']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(user_data)
    
print(f"Successfully created {USERS_CSV} with {len(user_data)} users.")

# 2. Write Connections CSV
connection_rows = []
for follower_id, followee_id in processed_edges:
    # Ensure both IDs were successfully mapped to our filtered set
    if follower_id in id_to_username and followee_id in id_to_username:
        connection_rows.append({
            'follower_username': id_to_username[follower_id],
            'followee_username': id_to_username[followee_id]
        })

with open(CONNECTIONS_CSV, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['follower_username', 'followee_username']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(connection_rows)

print(f"Successfully created {CONNECTIONS_CSV} with {len(connection_rows)} relationships.")
