from dotenv import load_dotenv
from neo4j import GraphDatabase
from pymongo import MongoClient
import os
import socket
import redis
from astrapy import DataAPIClient

load_dotenv()

uri      = os.getenv("NEO4J_URI")
user     = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE")

# ── NEO4J ─────────────────────────────────────────────────────────────────────
print("=" * 55)
print("NEO4J")
print("=" * 55)

# Intenta varias combinaciones de usuario
candidatos = [
    (user,        password),
    ("neo4j",     password),
    ("2bbf613e",  password),
    ("admin",     password),
]

for u, p in candidatos:
    try:
        drv = GraphDatabase.driver(uri, auth=(u, p))
        drv.verify_connectivity()
        print(f"  CONECTADO  user='{u}'")
        with drv.session(database="neo4j") as s:
            r = s.run("MATCH (n) RETURN count(n) AS total")
            for row in r:
                print(f"  Nodos: {row['total']}")
        drv.close()
        break
    except Exception as e:
        short = str(e).split("{message:")[1].split("}")[0].strip() if "{message:" in str(e) else str(e)[:80]
        print(f"  FALLO      user='{u}' -> {short}")

# ── MONGODB ───────────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("MONGODB")
print("=" * 55)
try:
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client["mediplus"]
    cols = db.list_collection_names()
    print(f"  CONECTADO  — colecciones: {cols if cols else '(vacío)'}")
except Exception as e:
    print(f"  FALLO → {e}")

# ── REDIS ─────────────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("REDIS")
print("=" * 55)
try:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        username=os.getenv("REDIS_USER"),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
        socket_timeout=5,
    )
    r.ping()
    r.set("debug_test", "ok")
    val = r.get("debug_test")
    print(f"  CONECTADO  — ping OK, get='{val}'")
except Exception as e:
    print(f"  FALLO → {e}")

# ── ASTRA / CASSANDRA ─────────────────────────────────────────────────────────
print()
print("=" * 55)
print("ASTRA (Cassandra)")
print("=" * 55)
try:
    astra_client = DataAPIClient()
    astra_db = astra_client.get_database(
        os.getenv("ASTRA_DB_API_ENDPOINT"),
        token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
    )
    cols = astra_db.list_collection_names()
    print(f"  CONECTADO  — collections: {cols if cols else '(vacío)'}")
except Exception as e:
    print(f"  FALLO → {e}")

print()
print("=" * 55)
