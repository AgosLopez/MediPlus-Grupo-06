import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

# Variable global para configurar el límite de registros en las pruebas
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
        
    print("\n" + "=" * 50)
    
    # TESTEO DE QUERIES
    afiliados_col = db["afiliados"]

    print("\n" + "="*60)
    print("TESTEO DE QUERIES - ORDEN INSTITUCIONAL PREPAGA")
    print("="*60)

    # 1. Buscar un afiliado específico por su número único
    print("\n1. Buscar afiliado por número de credencial:")
    q1 = afiliados_col.find_one({"numero_afiliado": "AF-2024-0000001"})
    if q1: print(f"   --> {q1.get('apellido')}, {q1.get('nombre')} | Estado: {q1.get('activo')}")

    # 2. Contador de afiliados inactivos o de baja
    print("\n2. Conteo de cuentas de afiliados inactivas:")
    inactivos = afiliados_col.count_documents({"activo": False})
    print(f"   --> Cantidad de cuentas inactivas: {inactivos}")

    # 3. Filtro por rango de fechas (Afiliados de alta desde 2023)
    print("\n3. Buscar nuevos afiliados dados de alta desde 2023:")
    q3 = afiliados_col.find({"fecha_alta": {"$gte": "2023-01-01"}}).limit(LIMIT_TEST)
    for af in q3: print(f"   --> {af['apellido']} | Alta: {af['fecha_alta']}")

    # 4. Filtrar por código de plan)
    print("\n4. Buscar afiliados adheridos al plan básico:")
    q4 = afiliados_col.find({"plan_salud.codigo_plan": "BASICO"}).limit(LIMIT_TEST)
    for af in q4: print(f"   --> {af['apellido']} - Plan: {af['plan_salud']['nombre']}")

    # 5. Filtro por rango numérico en campos embebidos (Cobertura mayor al 50%)
    print("\n5. Buscar planes con cobertura de estudios superior al 50%:")
    q5 = afiliados_col.find({"plan_salud.cobertura_estudios": {"$gt": 50}}).limit(LIMIT_TEST)
    for af in q5: print(f"   --> {af['apellido']} - Cobertura: {af['plan_salud']['cobertura_estudios']}%")

    # 6. Traer solo apellido, teléfono y ocultar el ID de sistema
    print("\n6. Listado optimizado para contacto telefónico (Proyección):")
    q6 = afiliados_col.find({}, {"apellido": 1, "telefono": 1, "_id": 0}).limit(LIMIT_TEST)
    for af in q6: print(f"   --> Datos: {af}")

    # 7. Filtrar por un objeto embebido (Dirección - Zona específica)
    print("\n7. Buscar afiliados que residen en la zona GBA Oeste:")
    q7 = afiliados_col.find({"direccion.zona": "GBA Oeste"}).limit(LIMIT_TEST)
    for af in q7: print(f"   --> {af['apellido']} ({af['direccion']['ciudad']})")

    # 8. Búsqueda por grupo familiar
    print("\n8. Buscar integrantes asociados al grupo familiar 'FAM-0052':")
    q8 = afiliados_col.find({"grupo_familiar_id": "FAM-0052"}).limit(LIMIT_TEST)
    for af in q8: print(f"   --> {af['apellido']}, {af['nombre']} | Rol: {af['rol_familiar']}")

    # 9. Gente que tiene cargado un médico de cabecera
    print("\n9. Buscar afiliados con médico de cabecera asignado:")
    q9 = afiliados_col.find({"medico_cabecera_id": {"$exists": True, "$ne": None}}).limit(LIMIT_TEST)
    for af in q9: print(f"   --> {af['apellido']} -> Médico ID: {af['medico_cabecera_id']}")

    # 10. Ordenar por fecha de nacimiento (mayor a menor)
    print("\n10. Listar afiliados de mayor edad registrados (Orden por nacimiento):")
    q10 = afiliados_col.find().sort("fecha_nacimiento", 1).limit(LIMIT_TEST)
    for af in q10: print(f"   --> {af['apellido']}, Nacimiento: {af['fecha_nacimiento']}")

    # 11. Buscar por grupo sanguíneo
    print("\n11. Buscar donantes potenciales con grupo sanguíneo O- o A+:")
    q11 = afiliados_col.find({"$or": [{"grupo_sanguineo": "O-"}, {"grupo_sanguineo": "A+"}]}).limit(LIMIT_TEST)
    for af in q11: print(f"   --> {af['apellido']} | Grupo: {af['grupo_sanguineo']}")

    # 12. Buscar afiliados con alergias
    print("\n12. Buscar afiliados con antecedentes de alergia en su historial:")
    q12 = afiliados_col.find({"enfermedades.tipo": "alergia"}).limit(LIMIT_TEST)
    for af in q12: print(f"   --> {af['apellido']} tiene alergias registradas.")

    # 13. Consulta compleja dentro de Array de Objetos (Enfermedad Severa y Crónica)
    print("\n13. Buscar pacientes con cuadros clínicos crónicos severos:")
    q13 = afiliados_col.find({"enfermedades": {"$elemMatch": {"tipo": "cronica", "severidad": "severa"}}}).limit(LIMIT_TEST)
    for af in q13: print(f"   --> {af['apellido']} presenta cuadro crónico severo.")

    # 14. Buscar por medicamento específico
    print("\n14. Buscar pacientes bajo tratamiento activo con la droga 'Enalapril':")
    q14 = afiliados_col.find({"enfermedades.medicacion_actual.droga": "Enalapril"}).limit(LIMIT_TEST)
    for af in q14: print(f"   --> {af['apellido']} consume Enalapril.")

    # 15. Buscar por código médico internacional (CIE10) en el historial
    print("\n15. Buscar pacientes diagnosticados bajo el código internacional CIE10 'I50':")
    q15 = afiliados_col.find({"enfermedades.cie10": "I50"}).limit(LIMIT_TEST)
    for af in q15: print(f"   --> {af['apellido']} tiene código I50 en su historial.")

    print("\n" + "="*60)
except Exception as e:
    print(f"\nError al conectar: {e}")
