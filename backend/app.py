from dotenv import load_dotenv
from neo4j import GraphDatabase
from pymongo import MongoClient
import os
import redis
from astrapy import DataAPIClient

load_dotenv()

from dotenv import load_dotenv
import os

load_dotenv()

print("URI =", os.getenv("NEO4J_URI"))
print("USER =", os.getenv("NEO4J_USER"))
print("DATABASE =", os.getenv("NEO4J_DATABASE"))

# ==========================================
# NEO4J AURA
# ==========================================

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD")
    )
)

driver.verify_connectivity()

print("Conectado a Neo4j Aura")

with driver.session(database=os.getenv("NEO4J_DATABASE")) as session:

    resultado = session.run("""
        MATCH (n)
        RETURN count(n) AS total
    """)

    for fila in resultado:
        print("Nodos:", fila["total"])


# ==========================================
# MONGODB
# ==========================================

mongo_client = MongoClient(os.getenv("MONGO_URI"))

mongo_db = mongo_client["mediplus"]

print("Conectado a MongoDB")

# ver colecciones
print("Colecciones MongoDB:")

for c in mongo_db.list_collection_names():
    print("-", c)

# ==========================================
# REDIS CLOUD
# ==========================================

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    username=os.getenv("REDIS_USER"),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

print("Conectado a Redis Cloud")

# guardar dato
r.set("prepaga", "MediPlus")

# obtener dato
valor = r.get("prepaga")

print("Valor Redis:", valor)


# ASTRA CON CASSANDRA


client = DataAPIClient()

db = client.get_database(
    os.getenv("ASTRA_DB_API_ENDPOINT"),
    token=os.getenv("ASTRA_DB_APPLICATION_TOKEN")
)

print("Conectado a Cassandra Astra")

# ver collections
collections = db.list_collection_names()

print("Collections:")

for c in collections:
    print("-", c)