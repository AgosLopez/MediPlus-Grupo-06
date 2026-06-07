import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

LIMIT_TEST = 3

try:
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client["mediplus"]
    
    print("=" * 50)
    print("PRUEBAS - MONGODB")
    print("=" * 50)
    
    un_afiliado = db["afiliados"].find_one()
    if un_afiliado:
        print("\nConexión exitosa. Ejemplo de estructura de un afiliado real:\n")
        pprint(un_afiliado, indent=4)
    else:
        print("\nConectó bien, pero la colección afiliados está vacía.")
        

    print("\n" + "="*60)
except Exception as e:
    print(f"\nError al conectar: {e}")
