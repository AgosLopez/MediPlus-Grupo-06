"""
afiliados_query.py — Consultas MongoDB para el WinForms.
Llamado desde C# con Process.Start(), retorna JSON por stdout.
 
Uso:
    python afiliados_query.py listar
    python afiliados_query.py detalle AF-000001
"""
 
import os
import sys
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime
 
# Cargar .env desde la misma carpeta que este script
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
 
 
def serializar(obj):
    """Convierte tipos MongoDB no serializables a string."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serializar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serializar(i) for i in obj]
    return obj
 
 
def get_db():
    client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
    return client["prepaga"]
 
 
def listar_afiliados():
    """Retorna lista con _id, nombre y apellido."""
    db = get_db()
    cursor = db["afiliados"].find(
        {},
        {"_id": 1, "nombre": 1, "apellido": 1}
    ).sort("apellido", 1)
    resultado = [serializar(doc) for doc in cursor]
    print(json.dumps(resultado, ensure_ascii=False))
 
 
def detalle_afiliado(id_afiliado: str):
    """Retorna todos los datos de un afiliado por su _id."""
    db = get_db()
    doc = db["afiliados"].find_one({"_id": id_afiliado})
    if doc is None:
        print(json.dumps({"error": f"Afiliado {id_afiliado} no encontrado"}))
        return
    print(json.dumps(serializar(doc), ensure_ascii=False))
 
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Uso: python afiliados_query.py [listar|detalle] [id]"}))
        sys.exit(1)
 
    comando = sys.argv[1]
 
    if comando == "listar":
        listar_afiliados()
    elif comando == "detalle" and len(sys.argv) == 3:
        detalle_afiliado(sys.argv[2])
    else:
        print(json.dumps({"error": "Comando inválido"}))
        sys.exit(1)
 