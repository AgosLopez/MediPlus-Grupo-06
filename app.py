from dotenv import load_dotenv
import os
import redis
from astrapy import DataAPIClient

load_dotenv()

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