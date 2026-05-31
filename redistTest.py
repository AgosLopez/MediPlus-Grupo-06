from dotenv import load_dotenv
import os
import redis

load_dotenv()

try:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        username=os.getenv("REDIS_USER"),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )

    r.set("test", "hola")

    print("✅ Redis conectado")
    print(r.get("test"))

except Exception as e:
    print("❌ Error")
    print(e)