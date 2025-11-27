import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # Application Settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"


config = Config()
