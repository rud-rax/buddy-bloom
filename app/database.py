from neo4j import GraphDatabase
import os
from dotenv import load_dotenv


load_dotenv() 

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


from neo4j import GraphDatabase

class UserCRUD:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()
    print("Connection to AuraDB established successfully!")


    def __del__(self) :
        self.driver.close()
        
    def create_user(self, user_id, name, email):
        with self.driver.session() as session:
            result = session.run(
                "CREATE (u:User {id: $id, name: $name, email: $email}) RETURN u",
                id=user_id, name=name, email=email)
            return result.single()[0]
    
    def get_user(self, user_id):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {id: $id}) RETURN u",
                id=user_id)
            record = result.single()
            return record[0] if record else None
        
    def update_user(self, user_id, name=None, email=None):
        with self.driver.session() as session:
            set_clause = []
            params = {"id": user_id}
            if name is not None:
                set_clause.append("u.name = $name")
                params["name"] = name
            if email is not None:
                set_clause.append("u.email = $email")
                params["email"] = email
            set_clause_str = ", ".join(set_clause)
            query = f"MATCH (u:User {{id: $id}}) SET {set_clause_str} RETURN u"
            result = session.run(query, **params)
            return result.single()[0] if result.peek() else None
    
    def delete_user(self, user_id):
        with self.driver.session() as session:
            session.run(
                "MATCH (u:User {id: $id}) DELETE u",
                id=user_id
            )

# Example usage:
if __name__ == "__main__":

    crud = UserCRUD(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
    print("Create:", crud.create_user("1", "Alice", "alice@example.com"))
    print("Read:", crud.get_user("1"))
    # print("Update:", crud.update_user("1", "Alicia"))
    # print("Delete:", crud.delete_user("1"))
