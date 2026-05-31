from dotenv import load_dotenv
from astrapy import DataAPIClient
import os

load_dotenv()

try:
    client = DataAPIClient()

    db = client.get_database(
        os.getenv("ASTRA_DB_API_ENDPOINT"),
        token=os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    )

    print("✅ Cassandra conectada")
    print(db.list_collection_names())

except Exception as e:
    print("❌ Error")
    print(e)