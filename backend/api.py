from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pymongo import MongoClient
import redis as redis_lib
from astrapy import DataAPIClient
import os
import json
import uuid
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
from datetime import date


load_dotenv()

app = FastAPI(title="MediPlus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Conexiones ────────────────────────────────────────────────────────────────

def get_neo4j():
    try:
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )
        driver.verify_connectivity()
        return driver
    except Exception:
        return None

def get_mongo():
    try:
        client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
        db = client["prepaga"]
        db.list_collection_names()
        return db, client
    except Exception:
        return None, None

def get_redis():
    try:
        r = redis_lib.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            username=os.getenv("REDIS_USER"),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        r.ping()
        return r
    except Exception:
        return None

def get_astra():
    try:
        client = DataAPIClient()
        db = client.get_database(
            os.getenv("ASTRA_DB_API_ENDPOINT"),
            token=os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        )
        return db
    except Exception:
        return None

# ── Esquemas de modelos ───────────────────────────────────────────────────────

_ZONAS   = ["CABA", "GBA Norte", "GBA Sur", "GBA Oeste", "Interior"]
_PLANES  = ["BASICO", "PLATA", "ORO", "FAMILIAR", "PLATINO"]
_GENEROS = ["M", "F", "X"]
_SANGRE  = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]

MODELS = {
    "Afiliado": {
        # Campos para búsqueda / filtro (READ, UPDATE filter, DELETE)
        "fields_filter": [
            {"name": "numero_afiliado", "type": "text", "required": False},
            {"name": "dni",             "type": "text", "required": False},
        ],
        # Campos para inserción / actualización de datos (CREATE, UPDATE data)
        "fields_create": [
            {"name": "nombre",           "type": "text",   "required": True},
            {"name": "apellido",         "type": "text",   "required": True},
            {"name": "dni",              "type": "text",   "required": True},
            {"name": "email",            "type": "email",  "required": True},
            {"name": "telefono",         "type": "text",   "required": True},
            {"name": "plan_salud",       "type": "select", "options": _PLANES,  "required": True},
            {"name": "zona",             "type": "select", "options": _ZONAS,   "required": True},
            {"name": "genero",           "type": "select", "options": _GENEROS, "required": True},
            {"name": "fecha_nacimiento", "type": "date",   "required": True},
            {"name": "grupo_sanguineo",  "type": "select", "options": _SANGRE,  "required": True},
            {"name": "calle",            "type": "text",   "required": True},
            {"name": "numero",           "type": "text",   "required": True},
            {"name": "ciudad",           "type": "text",   "required": True},
            {"name": "provincia",        "type": "text",   "required": True},
            {"name": "codigo_postal",    "type": "text",   "required": True},
        ],
        "neo4j_label":          "Afiliado",
        "neo4j_prop_map":       {},
        "mongo_collection":     "afiliados",
        "cassandra_collection": "prestaciones_por_afiliado",
        "redis_prefix":         "afiliado",
        "redis_id_field":       "numero_afiliado",
    },
    "Medico": {
        "fields_filter": [
            {"name": "medico_id",    "type": "text", "required": False},
            {"name": "dni",          "type": "text", "required": False},
            {"name": "especialidad", "type": "text", "required": False},
        ],
        "fields_create": [
            {"name": "medico_id",    "type": "text", "required": True},
            {"name": "nombre",       "type": "text", "required": True},
            {"name": "apellido",     "type": "text", "required": True},
            {"name": "especialidad", "type": "text", "required": False},
        ],
        "neo4j_label":          "Medico",
        # medico_id:ID is the actual Neo4j property name (CSV import artifact)
        "neo4j_prop_map":       {"medico_id": "`medico_id:ID`"},
        "mongo_collection":     None,
        "cassandra_collection": None,
        "redis_prefix":         "medico",
        "redis_id_field":       "medico_id",
    },
    "Clinica": {
        "fields_filter": [
            {"name": "clinica_id", "type": "text", "required": False},
            {"name": "nombre",     "type": "text", "required": False},
        ],
        "fields_create": [
            {"name": "clinica_id", "type": "text",   "required": True},
            {"name": "nombre",     "type": "text",   "required": True},
            {"name": "zona",       "type": "select", "options": _ZONAS, "required": False},
        ],
        "neo4j_label":          "Clinica",
        "neo4j_prop_map":       {"clinica_id": "`clinica_id:ID`"},
        "mongo_collection":     None,
        "cassandra_collection": None,
        "redis_prefix":         "clinica",
        "redis_id_field":       "clinica_id",
    },
    "Medicamento": {
        "fields_filter": [
            {"name": "medicamento_id",   "type": "text", "required": False},
            {"name": "nombre_comercial", "type": "text", "required": False},
        ],
        "fields_create": [
            {"name": "nombre_comercial", "type": "text", "required": True},
            {"name": "medicamento_id",   "type": "text", "required": True},
        ],
        "neo4j_label":          "Medicamento",
        "neo4j_prop_map":       {"medicamento_id": "`medicamento_id:ID`"},
        "mongo_collection":     None,
        "cassandra_collection": "uso_medicamentos_mes",
        "redis_prefix":         "medicamento",
        "redis_id_field":       "medicamento_id",
    },
}

# Queries de grafo para Neo4j READ — retornan nodos + relaciones
GRAPH_QUERIES = {
    "Afiliado": {
        "alias":    "a",
        "template": (
            "MATCH (a:Afiliado) {where} "
            "OPTIONAL MATCH (a)-[r1:PERTENECE_A]->(g:GrupoFamiliar) "
            "OPTIONAL MATCH (a)-[r2:RECURRE_A]->(m:Medico) "
            "RETURN a, g, m, r1, r2 LIMIT 5"
        ),
        "nodes": ["a", "g", "m"],
        "rels":  ["r1", "r2"],
    },
    "Medico": {
        "alias":    "m",
        "template": (
            "MATCH (m:Medico) {where} "
            "OPTIONAL MATCH (a:Afiliado)-[r1:RECURRE_A]->(m) "
            "RETURN m, a, r1 LIMIT 10"
        ),
        "nodes": ["m", "a"],
        "rels":  ["r1"],
    },
    "Clinica": {
        "alias":    "c",
        "template": (
            "MATCH (c:Clinica) {where} "
            "OPTIONAL MATCH (doc:Medico)-[r1:PRESTA_EN]->(c) "
            "RETURN c, doc, r1 LIMIT 10"
        ),
        "nodes": ["c", "doc"],
        "rels":  ["r1"],
    },
    "Medicamento": {
        "alias":    "med",
        "template": (
            "MATCH (med:Medicamento) {where} "
            "OPTIONAL MATCH (doc:Medico)-[r1:RECETO]->(med) "
            "RETURN med, doc, r1 LIMIT 10"
        ),
        "nodes": ["med", "doc"],
        "rels":  ["r1"],
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def ok(data, query):
    return {"status": "ok", "data": data, "query": query, "error": None}

def unavailable():
    return {"status": "unavailable", "data": None, "query": None, "error": "Servicio no disponible"}

def not_applicable(msg):
    return {"status": "not_applicable", "data": {"msg": msg}, "query": None, "error": None}

def err(e):
    return {"status": "error", "data": None, "query": None, "error": str(e)}

def neo4j_value(v):
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v

def _node_eid(node):
    if hasattr(node, "element_id"):
        return node.element_id
    return str(node.id)

def neo4j_node_to_dict(node):
    return {k: neo4j_value(v) for k, v in dict(node).items()}

def neo4j_to_graph(records, node_keys, rel_keys):
    nodes_map = {}
    rels = []
    for record in records:
        for k in node_keys:
            node = record.get(k)
            if node is None:
                continue
            nid = _node_eid(node)
            if nid not in nodes_map:
                label = list(node.labels)[0] if node.labels else "Node"
                nodes_map[nid] = {
                    "id":         nid,
                    "label":      label,
                    "properties": {key: neo4j_value(val) for key, val in dict(node).items()},
                }
        for k in rel_keys:
            rel = record.get(k)
            if rel is None:
                continue
            try:
                src = _node_eid(rel.start_node)
                tgt = _node_eid(rel.end_node)
            except Exception:
                continue
            rels.append({"source": src, "target": tgt, "type": rel.type})
    return {"nodes": list(nodes_map.values()), "relationships": rels}

def _next_afiliado_id(db):
    """Genera el proximo afiliado_id usando un contador atomico en MongoDB.

    Usa find_one_and_update + $inc, que MongoDB ejecuta atomicamente,
    eliminando la race condition del count_documents() + 1 anterior.
    $setOnInsert inicializa el contador al conteo actual solo en la primera
    llamada (upsert), preservando los IDs ya existentes.
    """
    db["counters"].update_one(
        {"_id": "afiliado_seq"},
        {"$setOnInsert": {"seq": db["afiliados"].count_documents({})}},
        upsert=True,
    )
    result = db["counters"].find_one_and_update(
        {"_id": "afiliado_seq"},
        {"$inc": {"seq": 1}},
        return_document=True,
    )
    num = result["seq"]
    return f"AF-{num:06d}", f"AF-2024-{num:07d}"

def _mongo_afiliado_filter(flt):
    """Mapea campos planos del formulario a las rutas reales de MongoDB."""
    if "afiliado_id"     in flt: return {"_id":            flt["afiliado_id"]}
    if "numero_afiliado" in flt: return {"numero_afiliado": flt["numero_afiliado"]}
    if "dni"             in flt: return {"dni":             flt["dni"]}
    mongo_flt = {}
    for k, v in flt.items():
        if k == "plan_salud":
            mongo_flt["plan_salud.codigo_plan"] = v
        elif k == "zona":
            mongo_flt["direccion.zona"] = v
        elif k in ("nombre", "apellido"):
            mongo_flt[k] = {"$regex": v, "$options": "i"}
        else:
            mongo_flt[k] = v
    return mongo_flt

def _mongo_afiliado_set(data):
    """Mapea campos planos a rutas correctas para $set."""
    _addr = {"calle", "numero", "ciudad", "provincia", "codigo_postal", "zona"}
    set_doc = {}
    for k, v in data.items():
        if k == "plan_salud":
            set_doc["plan_salud.codigo_plan"] = v
        elif k in _addr:
            set_doc[f"direccion.{k}"] = v
        else:
            set_doc[k] = v
    return set_doc

def _build_afiliado_mongo_doc(afiliado_id, numero_afiliado, data):
    """Convierte los campos planos del formulario al documento MongoDB real."""
    hoy = str(date.today())
    plan_cod = data.get("plan_salud", "BASICO")
    planes = {
        "BASICO":   {"cuota": 25000,  "medicamentos": 40,  "estudios": 60,  "copago": 3500},
        "PLATA":    {"cuota": 50000,  "medicamentos": 50,  "estudios": 75,  "copago": 2000},
        "ORO":      {"cuota": 90000,  "medicamentos": 70,  "estudios": 90,  "copago": 1000},
        "FAMILIAR": {"cuota": 110000, "medicamentos": 80,  "estudios": 95,  "copago": 500},
        "PLATINO":  {"cuota": 150000, "medicamentos": 100, "estudios": 100, "copago": 0},
    }
    plan = planes.get(plan_cod, planes["BASICO"])
    return {
        "_id":               afiliado_id,
        "numero_afiliado":   numero_afiliado,
        "dni":               data.get("dni", ""),
        "nombre":            data.get("nombre", ""),
        "apellido":          data.get("apellido", ""),
        "genero":            data.get("genero", ""),
        "fecha_nacimiento":  data.get("fecha_nacimiento", ""),
        "email":             data.get("email", ""),
        "telefono":          data.get("telefono", ""),
        "grupo_sanguineo":   data.get("grupo_sanguineo", ""),
        "direccion": {
            "calle":         data.get("calle", ""),
            "numero":        data.get("numero", ""),
            "ciudad":        data.get("ciudad", ""),
            "provincia":     data.get("provincia", ""),
            "codigo_postal": data.get("codigo_postal", ""),
            "zona":          data.get("zona", ""),
        },
        "plan_salud": {
            "codigo_plan":            plan_cod,
            "nombre":                 plan_cod.capitalize(),
            "cuota_mensual":          plan["cuota"],
            "cobertura_medicamentos": plan["medicamentos"],
            "cobertura_estudios":     plan["estudios"],
            "copago_consulta":        plan["copago"],
            "fecha_alta":             hoy,
            "estado":                 "activo",
        },
        "enfermedades": [],
        "fecha_alta":    hoy,
        "activo":        True,
    }

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    import asyncio

    def check_neo4j():
        try:
            d = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
                connection_timeout=3,
            )
            d.verify_connectivity()
            d.close()
            return "ok"
        except Exception:
            return "error"

    def check_mongo():
        try:
            c = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=2000)
            c["prepaga"].list_collection_names()
            c.close()
            return "ok"
        except Exception:
            return "error"

    def check_redis():
        try:
            r = redis_lib.Redis(
                host=os.getenv("REDIS_HOST"),
                port=int(os.getenv("REDIS_PORT")),
                username=os.getenv("REDIS_USER"),
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            r.ping()
            return "ok"
        except Exception:
            return "error"

    def check_astra():
        try:
            c = DataAPIClient()
            db = c.get_database(
                os.getenv("ASTRA_DB_API_ENDPOINT"),
                token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
            )
            db.list_collection_names()
            return "ok"
        except Exception:
            return "error"

    loop = asyncio.get_running_loop()
    results = await asyncio.gather(
        loop.run_in_executor(None, check_neo4j),
        loop.run_in_executor(None, check_mongo),
        loop.run_in_executor(None, check_redis),
        loop.run_in_executor(None, check_astra),
    )

    return {
        "neo4j":     results[0],
        "mongodb":   results[1],
        "redis":     results[2],
        "cassandra": results[3],
    }

@app.get("/api/models")
def get_models_endpoint():
    return {
        name: {
            "fields_filter": schema["fields_filter"],
            "fields_create": schema["fields_create"],
        }
        for name, schema in MODELS.items()
    }

@app.get("/api/cassandra")
def ver_colecciones():

    db = get_astra()

    return db.list_collection_names()

@app.get("/api/dashboard/gastos")
def dashboard_gastos():

    db = get_astra()

    col = db.get_collection("gasto_mensual_por_afiliado")

    datos = list(
        col.find({}, limit=1000)
    )

    for d in datos:
        d.pop("_id", None)

    return datos

@app.get("/api/dashboard/medicamentos")
def dashboard_medicamentos():

    db = get_astra()

    col = db.get_collection("uso_medicamentos_mes")

    datos = list(col.find({}, limit=1000))

    for d in datos:
        d.pop("_id", None)

    return datos

@app.get("/api/dashboard/especialidades")
def dashboard_especialidades():

    db = get_astra()

    col = db.get_collection("gasto_por_especialidad_mes")

    datos = list(col.find({}, limit=1000))

    for d in datos:
        d.pop("_id", None)

    return datos

@app.get("/api/dashboard/clinicas")
def dashboard_clinicas():

    db = get_astra()

    col = db.get_collection("eventos_por_clinica_mes")

    datos = list(col.find({}, limit=1000))

    for d in datos:
        d.pop("_id", None)

    return datos

@app.get("/api/dashboard/diagnosticos")
def dashboard_diagnosticos():

    db = get_astra()

    col = db.get_collection("eventos_por_zona_diagnostico_mes")

    datos = list(col.find({}, limit=1000))

    for d in datos:
        d.pop("_id", None)

    return datos

@app.get("/api/dashboard/credenciales")
def dashboard_credenciales():

    db = get_astra()

    col = db.get_collection("eventos_uso_credencial")

    datos = list(col.find({}, limit=1000))

    for d in datos:
        d.pop("_id", None)

    return datos

@app.get("/api/dashboard/prestaciones")
def dashboard_prestaciones():

    db = get_astra()

    col = db.get_collection("prestaciones_por_afiliado")

    datos = list(col.find({}, limit=1000))

    for d in datos:
        d.pop("_id", None)

    return datos


class OperationRequest(BaseModel):
    operation: str
    model: str
    data: Optional[dict] = None
    filter: Optional[dict] = None

@app.post("/api/operation")
def execute_operation(req: OperationRequest):
    try:
        return _execute_operation_inner(req)
    except Exception as e:
        return {
            "neo4j":     err(e),
            "mongodb":   err(e),
            "redis":     err(e),
            "cassandra": err(e),
        }

def _execute_operation_inner(req: OperationRequest):
    if req.model not in MODELS:
        raise HTTPException(status_code=400, detail=f"Modelo {req.model} no existe")

    schema  = MODELS[req.model]
    # Strip empty strings and None values so they don't pollute WHERE clauses or $set
    data    = {k: v for k, v in (req.data   or {}).items() if v is not None and v != ""}
    flt     = {k: v for k, v in (req.filter or {}).items() if v is not None and v != ""}
    op      = req.operation
    results = {}

    if op == "delete" and not flt:
        e = err(ValueError("Se requiere al menos un filtro para eliminar"))
        return {"neo4j": e, "mongodb": e, "redis": e, "cassandra": e}

    if op == "update" and not data:
        e = err(ValueError("Se requieren datos nuevos para actualizar"))
        return {"neo4j": e, "mongodb": e, "redis": e, "cassandra": e}

    # ── Generar IDs para Afiliado en CREATE ───────────────────────────────────
    # Se resuelve antes de tocar cualquier DB para que todos los motores
    # reciban el mismo afiliado_id y numero_afiliado.
    afiliado_id     = None
    numero_afiliado = None
    if req.model == "Afiliado" and op == "create":
        mongo_db_tmp, mongo_client_tmp = get_mongo()
        if mongo_db_tmp is not None:
            afiliado_id, numero_afiliado = _next_afiliado_id(mongo_db_tmp)
            mongo_client_tmp.close()
        else:
            # Fallback si Mongo no está disponible
            import random
            n = random.randint(10000, 99999)
            afiliado_id     = f"AF-{n:06d}"
            numero_afiliado = f"AF-2024-{n:07d}"

    # ── Enriquecimiento DNI → numero_afiliado para Neo4j ─────────────────────
    # Neo4j no almacena DNI; si el filtro es solo DNI se consulta MongoDB
    # primero para obtener el numero_afiliado y usarlo en el grafo.
    neo4j_flt = flt
    if req.model == "Afiliado" and op == "read" and "dni" in flt and "numero_afiliado" not in flt:
        _mdb, _mcli = get_mongo()
        if _mdb is not None:
            try:
                _doc = _mdb["afiliados"].find_one(
                    {"dni": flt["dni"]}, {"numero_afiliado": 1, "_id": 0}
                )
                if _doc and _doc.get("numero_afiliado"):
                    neo4j_flt = {"numero_afiliado": _doc["numero_afiliado"]}
            finally:
                _mcli.close()

    # ── Neo4j ────────────────────────────────────────────────────────────────
    driver = get_neo4j()
    if driver:
        try:
            label = schema["neo4j_label"]
            with driver.session(database=os.getenv("NEO4J_DATABASE")) as s:
                if op == "read":
                    gq       = GRAPH_QUERIES.get(req.model)
                    alias    = gq["alias"] if gq else "n"
                    prop_map = schema.get("neo4j_prop_map", {})
                    if neo4j_flt:
                        parts = []
                        for k in neo4j_flt:
                            if k in prop_map:
                                # Match both imported (:ID) and created (plain) property names
                                parts.append(f"({alias}.{prop_map[k]} = ${k} OR {alias}.{k} = ${k})")
                            else:
                                parts.append(f"{alias}.{k} = ${k}")
                        where = "WHERE " + " AND ".join(parts)
                    else:
                        where = ""
                    if gq:
                        query = gq["template"].replace("{where}", where)
                        rows  = list(s.run(query, **neo4j_flt))
                        result_data = neo4j_to_graph(rows, gq["nodes"], gq["rels"])
                    else:
                        query = f"MATCH (n:{label}) {where} RETURN n LIMIT 10"
                        rows  = list(s.run(query, **neo4j_flt))
                        result_data = [neo4j_node_to_dict(r["n"]) for r in rows]

                elif op == "create":
                    neo4j_data = {**data}
                    if req.model == "Afiliado":
                        neo4j_data["afiliado_id"]     = afiliado_id
                        neo4j_data["numero_afiliado"] = numero_afiliado
                        neo4j_data["zona"]            = data.get("zona", "")
                        neo4j_data["plan_salud"]      = data.get("plan_salud", "BASICO")
                    props_str = ", ".join([f"{k}: ${k}" for k in neo4j_data])
                    query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
                    rows  = list(s.run(query, **neo4j_data))
                    result_data = [neo4j_node_to_dict(r["n"]) for r in rows]

                elif op == "update":
                    prop_map = schema.get("neo4j_prop_map", {})
                    sets   = ", ".join([f"n.{k} = ${k}" for k in data])
                    if flt:
                        parts = []
                        for k in flt:
                            if k in prop_map:
                                parts.append(f"(n.{prop_map[k]} = $f_{k} OR n.{k} = $f_{k})")
                            else:
                                parts.append(f"n.{k} = $f_{k}")
                        where = "WHERE " + " AND ".join(parts)
                    else:
                        where = ""
                    params = {**data, **{f"f_{k}": v for k, v in flt.items()}}
                    query  = f"MATCH (n:{label}) {where} SET {sets} RETURN n"
                    rows   = list(s.run(query, **params))
                    result_data = [neo4j_node_to_dict(r["n"]) for r in rows]

                elif op == "delete":
                    prop_map = schema.get("neo4j_prop_map", {})
                    if flt:
                        parts = []
                        for k in flt:
                            if k in prop_map:
                                parts.append(f"(n.{prop_map[k]} = ${k} OR n.{k} = ${k})")
                            else:
                                parts.append(f"n.{k} = ${k}")
                        where = "WHERE " + " AND ".join(parts)
                    else:
                        where = ""
                    if req.model == "Afiliado":
                        query = f"MATCH (n:{label}) {where} SET n.activo = false RETURN count(n) AS updated"
                        rows  = list(s.run(query, **flt))
                        result_data = {"desactivados": rows[0]["updated"] if rows else 0}
                    else:
                        query = f"MATCH (n:{label}) {where} DETACH DELETE n RETURN count(n) AS deleted"
                        rows  = list(s.run(query, **flt))
                        result_data = {"deleted": rows[0]["deleted"] if rows else 0}

                else:
                    raise ValueError(f"Operacion desconocida: {op}")

            results["neo4j"] = ok(result_data, query)
        except Exception as e:
            results["neo4j"] = err(e)
        finally:
            driver.close()
    else:
        results["neo4j"] = unavailable()

    # ── MongoDB ───────────────────────────────────────────────────────────────
    col_name = schema.get("mongo_collection")
    if col_name:
        mongo_db, mongo_client = get_mongo()
        if mongo_db is not None:
            try:
                col = mongo_db[col_name]
                if op == "read":
                    mongo_flt = _mongo_afiliado_filter(flt)
                    docs  = list(col.find(mongo_flt, {"_id": 0}).limit(10))
                    query = f'db.{col_name}.find({json.dumps(mongo_flt)})'
                    results["mongodb"] = ok(docs, query)

                elif op == "create":
                    doc = _build_afiliado_mongo_doc(afiliado_id, numero_afiliado, data)
                    col.insert_one(doc)
                    doc.pop("_id", None)   # _id no es JSON-serializable directo
                    doc["_id"] = afiliado_id
                    query = f'db.{col_name}.insertOne({{ _id: "{afiliado_id}", numero_afiliado: "{numero_afiliado}", ... }})'
                    results["mongodb"] = ok(doc, query)

                elif op == "update":
                    mongo_flt = _mongo_afiliado_filter(flt)
                    set_doc   = _mongo_afiliado_set(data)
                    res   = col.update_many(mongo_flt, {"$set": set_doc})
                    query = f'db.{col_name}.updateMany({json.dumps(mongo_flt)}, {{$set: {json.dumps(set_doc)}}})'
                    results["mongodb"] = ok({"matched": res.matched_count, "modified": res.modified_count}, query)

                elif op == "delete":
                    mongo_flt = _mongo_afiliado_filter(flt)
                    res   = col.update_many(mongo_flt, {"$set": {"activo": False, "plan_salud.estado": "inactivo"}})
                    query = f'db.{col_name}.updateMany({json.dumps(mongo_flt)}, {{$set: {{activo: false, "plan_salud.estado": "inactivo"}}}})'
                    results["mongodb"] = ok({"desactivados": res.modified_count}, query)

            except Exception as e:
                results["mongodb"] = err(e)
            finally:
                mongo_client.close()
        else:
            results["mongodb"] = unavailable()
    else:
        results["mongodb"] = not_applicable(f"{req.model} no tiene coleccion en MongoDB")

    # ── Redis ─────────────────────────────────────────────────────────────────
    r = get_redis()
    if r:
        try:
            prefix   = schema["redis_prefix"]
            id_field = schema["redis_id_field"]

            if op == "read":
                if req.model == "Afiliado":
                    # Buscar sesiones activas del afiliado + rate limiting
                    id_val       = flt.get("numero_afiliado") or flt.get("dni") or "*"
                    result_data  = {}
                    # Cache propio del afiliado
                    cache_keys   = r.keys(f"mediplus:afiliado:{id_val}")
                    for k in cache_keys[:5]:
                        result_data[k] = r.hgetall(k)
                    # Rate limiting de credencial
                    rate_key     = f"rate:credencial:{id_val}"
                    rate_val     = r.get(rate_key)
                    if rate_val:
                        result_data[rate_key] = rate_val
                    query = (
                        f"KEYS mediplus:afiliado:{id_val}\n"
                        f"GET  rate:credencial:{id_val}"
                    )
                    results["redis"] = ok(result_data, query)

                elif req.model == "Medico":
                    # Mostrar ranking real de medicos mas demandados
                    top   = r.zrevrange("top:medicos_demandados", 0, 9, withscores=True)
                    query = "ZREVRANGE top:medicos_demandados 0 9 WITHSCORES"
                    results["redis"] = ok(
                        [{"medico_id": mid, "consultas": int(score)} for mid, score in top],
                        query
                    )

                elif req.model == "Clinica":
                    id_val = flt.get("clinica_id") or flt.get("nombre") or "*"
                    keys   = r.keys(f"consultorio:*")[:10]
                    result_data = {k: r.get(k) for k in keys}
                    query  = "KEYS consultorio:*"
                    results["redis"] = ok(result_data, query)

                elif req.model == "Medicamento":
                    med_id = flt.get("medicamento_id", "*")
                    keys   = r.keys(f"mediplus:medicamento:{med_id}")
                    result_data = {k: r.hgetall(k) for k in keys[:10]}
                    query  = f"HGETALL mediplus:medicamento:{med_id}"
                    results["redis"] = ok(result_data, query)

                else:
                    id_val = flt.get(id_field, "*")
                    keys   = r.keys(f"mediplus:{prefix}:{id_val}")
                    result_data = {k: r.hgetall(k) for k in keys[:10]}
                    query  = f"HGETALL mediplus:{prefix}:{id_val}"
                    results["redis"] = ok(result_data, query)

            elif op == "create":
                if req.model == "Afiliado":
                    key  = f"mediplus:afiliado:{numero_afiliado}"
                    flat = {
                        "afiliado_id":     afiliado_id,
                        "numero_afiliado": numero_afiliado,
                        "nombre":          data.get("nombre", ""),
                        "apellido":        data.get("apellido", ""),
                        "dni":             data.get("dni", ""),
                        "plan_salud":      data.get("plan_salud", ""),
                        "zona":            data.get("zona", ""),
                    }
                elif req.model == "Medico":
                    med_id = data.get("medico_id", f"MED-NEW-{data.get('nombre','')[:8].upper()}")
                    key    = f"mediplus:medico:{med_id}"
                    flat   = {k: str(v) for k, v in data.items()}
                    r.zadd("top:medicos_demandados", {med_id: 0}, nx=True)
                else:
                    id_val = data.get(id_field, str(uuid.uuid4())[:8])
                    key    = f"mediplus:{prefix}:{id_val}"
                    flat   = {k: str(v) for k, v in data.items()}

                if req.model == "Afiliado":
                    r.hset(key, mapping=flat)
                    r.expire(key, 86400)
                    query = f"HSET {key} ...\nEXPIRE {key} 86400"
                elif req.model == "Medico":
                    r.hset(key, mapping=flat)
                    query = f"HSET {key} ...\nZADD top:medicos_demandados NX 0 {med_id}"

                else:
                    r.hset(key, mapping=flat)
                    r.expire(key, 86400)
                    query = f"HSET {key} ...\nEXPIRE {key} 86400"

                results["redis"] = ok(flat, query)

            elif op == "update":
                if req.model == "Afiliado":
                    id_val = flt.get("numero_afiliado") or flt.get("dni") or "*"
                else:
                    id_val = flt.get(id_field, "*")
                key  = f"mediplus:{prefix}:{id_val}"
                flat = {k: str(v) for k, v in data.items()}
                r.hset(key, mapping=flat)
                query = f"HSET {key} {flat}"
                results["redis"] = ok(flat, query)

            elif op == "delete":
                if req.model == "Afiliado":
                    id_val = flt.get("numero_afiliado") or flt.get("dni") or "*"
                else:
                    id_val = flt.get(id_field, "*")
                deleted_keys = r.keys(f"mediplus:{prefix}:{id_val}")
                count = r.delete(*deleted_keys) if deleted_keys else 0
                query = f"DEL mediplus:{prefix}:{id_val}"
                results["redis"] = ok({"deleted": count}, query)

        except Exception as e:
            results["redis"] = err(e)
    else:
        results["redis"] = unavailable()

    # ── Cassandra (via AstraDB) ───────────────────────────────────────────────
    cass_col = schema.get("cassandra_collection")
    if cass_col:
        adb = get_astra()
        if adb:
            try:
                col = adb.get_collection(cass_col)

                if op == "read":
                    # Construir filtro real para las partition keys de Cassandra
                    cass_flt = {}
                    if req.model == "Afiliado":
                        if "afiliado_id" in flt:
                            cass_flt["afiliado_id"] = flt["afiliado_id"]
                        elif "numero_afiliado" in flt:
                            # numero_afiliado="AF-2024-0000006" → afiliado_id="AF-000006"
                            parts = flt["numero_afiliado"].split("-")
                            if len(parts) == 3 and parts[0] == "AF":
                                cass_flt["afiliado_id"] = f"AF-{int(parts[2]):06d}"
                            else:
                                cass_flt["numero_afiliado"] = flt["numero_afiliado"]
                        # tabla: eventos_por_afiliado PK=(afiliado_id, fecha_evento, evento_id)
                        where_clause = " AND ".join(f"{k} = '{v}'" for k, v in cass_flt.items())
                        cql = (
                            f"SELECT * FROM prepaga.prestaciones_por_afiliado"
                            + (f" WHERE {where_clause}" if cass_flt else "")
                            + " LIMIT 10;"
                        )
                    elif req.model == "Medicamento":
                        if "medicamento_id" in flt:
                            cass_flt["medicamento_id"] = flt["medicamento_id"]
                        # tabla: uso_medicamento_mes PK=((medicamento_id, anio_mes), fecha_evento, evento_id)
                        cql = (
                            f"SELECT * FROM prepaga.uso_medicamentos_mes"
                            + (f" WHERE medicamento_id = '{cass_flt.get('medicamento_id', '?')}'" if cass_flt else "")
                            + " LIMIT 10;"
                        )
                    else:
                        cass_flt = flt
                        cql = f"SELECT * FROM prepaga.{cass_col} LIMIT 10;"

                    docs = list(col.find(cass_flt, limit=10))
                    for d in docs:
                        d.pop("_id", None)
                    results["cassandra"] = ok(docs, cql)

                elif op == "create":
                    if req.model == "Afiliado":
                        doc = {
                            "afiliado_id":    afiliado_id,
                            "numero_afiliado": numero_afiliado,
                            "evento_id":      f"EVT-{uuid.uuid4().hex[:8].upper()}",
                            "fecha_evento":   str(date.today()) + "T00:00:00",
                            "tipo_prestacion": "alta",
                            "especialidad":   "",
                            "zona":           data.get("zona", ""),
                            "cie10_diagnostico": "",
                            "monto_facturado": 0,
                            "monto_cubierto":  0,
                            "copago":          0,
                        }
                        cql = (
                            f"INSERT INTO prepaga.prestaciones_por_afiliado "
                            f"(afiliado_id, fecha_evento, evento_id, tipo_prestacion, zona) "
                            f"VALUES ('{afiliado_id}', '{doc['fecha_evento']}', '{doc['evento_id']}', 'alta', '{doc['zona']}');"
                        )
                    elif req.model == "Medicamento":
                        med_id  = data.get("medicamento_id", "")
                        anio_mes = str(date.today())[:7]
                        doc = {
                            "medicamento_id": med_id,
                            "anio_mes":       anio_mes,
                            "evento_id":      f"EVT-{uuid.uuid4().hex[:8].upper()}",
                            "fecha_evento":   str(date.today()) + "T00:00:00",
                            "afiliado_id":    "",
                            "monto_facturado": 0,
                        }
                        cql = (
                            f"INSERT INTO prepaga.uso_medicamentos_mes "
                            f"(medicamento_id, anio_mes, fecha_evento, evento_id) "
                            f"VALUES ('{med_id}', '{anio_mes}', '{doc['fecha_evento']}', '{doc['evento_id']}');"
                        )
                    else:
                        doc = data
                        cql = f"INSERT INTO prepaga.{cass_col} (...) VALUES (...);"

                    col.insert_one(doc)
                    results["cassandra"] = ok(doc, cql)

                elif op == "update":
                    if req.model == "Afiliado":
                        cass_flt_op = {}
                        if "afiliado_id" in flt:
                            cass_flt_op["afiliado_id"] = flt["afiliado_id"]
                        elif "numero_afiliado" in flt:
                            parts = flt["numero_afiliado"].split("-")
                            if len(parts) == 3 and parts[0] == "AF":
                                cass_flt_op["afiliado_id"] = f"AF-{int(parts[2]):06d}"
                            else:
                                cass_flt_op["numero_afiliado"] = flt["numero_afiliado"]
                    elif req.model == "Medicamento":
                        cass_flt_op = {k: v for k, v in flt.items() if k == "medicamento_id"}
                    else:
                        cass_flt_op = flt
                    col.update_many(cass_flt_op, {"$set": data})
                    sets  = ", ".join([f"{k} = '{v}'" for k, v in data.items()])
                    where_parts = [f"{k} = '{v}'" for k, v in cass_flt_op.items()]
                    where = " AND ".join(where_parts) if where_parts else "1=1"
                    cql = f"UPDATE prepaga.{cass_col} SET {sets} WHERE {where};"
                    results["cassandra"] = ok({"updated": True}, cql)

                elif op == "delete":
                    if req.model == "Afiliado":
                        cass_flt_op = {}
                        if "afiliado_id" in flt:
                            cass_flt_op["afiliado_id"] = flt["afiliado_id"]
                        elif "numero_afiliado" in flt:
                            parts = flt["numero_afiliado"].split("-")
                            if len(parts) == 3 and parts[0] == "AF":
                                cass_flt_op["afiliado_id"] = f"AF-{int(parts[2]):06d}"
                            else:
                                cass_flt_op["numero_afiliado"] = flt["numero_afiliado"]
                    elif req.model == "Medicamento":
                        cass_flt_op = {k: v for k, v in flt.items() if k == "medicamento_id"}
                    else:
                        cass_flt_op = flt
                    col.delete_many(cass_flt_op)
                    where_parts = [f"{k} = '{v}'" for k, v in cass_flt_op.items()]
                    where = " AND ".join(where_parts) if where_parts else "1=1"
                    cql = f"DELETE FROM prepaga.{cass_col} WHERE {where};"
                    results["cassandra"] = ok({"deleted": True}, cql)

            except Exception as e:
                results["cassandra"] = err(e)
        else:
            results["cassandra"] = unavailable()
    else:
        results["cassandra"] = not_applicable(f"{req.model} no tiene tabla en Cassandra")

    return results
