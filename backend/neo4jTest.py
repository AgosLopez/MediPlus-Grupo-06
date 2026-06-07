from neo4j import GraphDatabase

URI = "neo4j+s://2bbf613e.databases.neo4j.io"
AUTH = ("2bbf613e", "7e1GHFkg_ASsS6JxMagKNAJUjCUGozheW1-Z4CLTdgE")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("✅ Conectado a Neo4j Aura")