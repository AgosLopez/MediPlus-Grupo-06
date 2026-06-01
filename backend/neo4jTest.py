from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt+s://2bbf613e.databases.neo4j.io:7687",
    auth=("neo4j", "7e1GHFkg_ASsS6JxMagKNAJUjCUGozheW1-Z4CLTdgE")
)

driver.verify_connectivity()

print("Conectado")