from dotenv import load_dotenv
import os
import redis

load_dotenv()

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

print("Valor:", valor)