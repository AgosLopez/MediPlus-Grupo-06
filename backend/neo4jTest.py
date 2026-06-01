from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

print("URI =", os.getenv("NEO4J_URI"))
print("USER =", os.getenv("NEO4J_USER"))

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD")
    )
)

with driver.session(database=os.getenv("NEO4J_DATABASE")) as session:
    result = session.run("RETURN 1 AS x")
    print(result.single()["x"])

print("CONECTADO")