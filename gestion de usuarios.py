import hashlib
from datetime import date
import pyodbc

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=TaskFlowDB;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

def conectar():
    try:
        return pyodbc.connect(CONNECTION_STRING)
    except pyodbc.Error as e:
        print(f"\n[ERROR DE CONEXIÓN]: {e}")
        return None

def encriptar(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest().upper()

def login(correo, contrasena):
    conn = conectar()
    if not conn:
        return None
    cursor = conn.cursor()
    query = """
    SELECT 
        u.id_usuario, u.codigo_usuario, u.nombres, u.apellidos, u.correo,
        r.nombre_rol, u.id_empresa, e.nombre_empresa, u.id_departamento, d.nombre_depto
    FROM Usuario u
    INNER JOIN Rol r ON u.id_rol = r.id_rol
    LEFT JOIN Empresa e ON u.id_empresa = e.id_empresa
    LEFT JOIN Departamento d ON u.id_departamento = d.id_departamento
    WHERE u.correo = ? AND u.contrasena = ? AND u.estado = 'Activo'
    """
    cursor.execute(query, (correo, encriptar(contrasena)))
    row = cursor.fetchone()
    conn.close()
    if row:
        columnas = [col[0] for col in cursor.description]
        return dict(zip(columnas, row))
    return None


# MÓDULO: SUPERADMIN


def superadmin_crear_empresa_y_dueno():
    print("\n--- [SUPERADMIN] CREAR EMPRESA Y DECLARAR DUEÑO ---")
    nombre_empresa = input("Nombre de la Empresa: ").strip()
    rnc = input("RNC de la Empresa: ").strip()

    conn = conectar()
    if not conn:
        return
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO Empresa (nombre_empresa, rnc) VALUES (?, ?)", (nombre_empresa, rnc))
        cursor.execute("SELECT @@IDENTITY")
        id_empresa = int(cursor.fetchone()[0])

        print(f"\nEmpresa '{nombre_empresa}' registrada. Proceda a registrar al Dueño:")
        codigo = input("Código del Dueño (ej. D-101): ").strip()
        nombres = input("Nombres: ").strip()
        apellidos = input("Apellidos: ").strip()
        correo = input("Correo institucional del Dueño: ").strip()
        password = input("Contraseña: ").strip()

        # Rol  = Dueño
        cursor.execute("""
            INSERT INTO Usuario (codigo_usuario, nombres, apellidos, correo, contrasena, id_rol, id_empresa, fecha_ingreso, estado)
            VALUES (?, ?, ?, ?, ?, 3, ?, GETDATE(), 'Activo')
        """, (codigo, nombres, apellidos, correo, encriptar(password), id_empresa))

        conn.commit()
        print(f"Dueño asignado exitosamente a {nombre_empresa}.")
    except pyodbc.Error as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

def superadmin_asignar_admin_empresa():
    print("\n--- [SUPERADMIN] ASIGNAR ADMIN DE EMPRESA ---")
    conn = conectar()
    if not conn:
        return
    cursor = conn.cursor()

    cursor.execute("SELECT id_empresa, nombre_empresa, rnc FROM Empresa")
    empresas = cursor.fetchall()
    if not empresas:
        print("No hay empresas registradas.")
        conn.close()
        return

    print("Empresas disponibles:")
    for emp in empresas:
        print(f"[{emp[0]}] {emp[1]} (RNC: {emp[2]})")
    id_empresa = int(input("Seleccione el ID de la empresa: ").strip())

    codigo = input("Código del Admin (ej. ADM-01): ").strip()
    nombres = input("Nombres: ").strip()
    apellidos = input("Apellidos: ").strip()
    correo = input("Correo: ").strip()
    password = input("Contraseña: ").strip()

    try:
        # Rol  = Admin de Empresa
        cursor.execute("""
            INSERT INTO Usuario (codigo_usuario, nombres, apellidos, correo, contrasena, id_rol, id_empresa, fecha_ingreso, estado)
            VALUES (?, ?, ?, ?, ?, 2, ?, GETDATE(), 'Activo')
        """, (codigo, nombres, apellidos, correo, encriptar(password), id_empresa))
        conn.commit()
        print(f"Admin de Empresa '{nombres} {apellidos}' creado exitosamente con acceso total a su empresa.")
    except pyodbc.Error as e:
        print(f"Error al registrar admin: {e}")
    finally:
        conn.close()

def superadmin_listar_empresas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id_empresa, e.nombre_empresa,
               (SELECT CONCAT(u.nombres, ' ', u.apellidos) FROM Usuario u WHERE u.id_empresa = e.id_empresa AND u.id_rol = 3) AS Dueno,
               (SELECT CONCAT(u.nombres, ' ', u.apellidos) FROM Usuario u WHERE u.id_empresa = e.id_empresa AND u.id_rol = 2) AS AdminEmpresa
        FROM Empresa e
    """)
    filas = cursor.fetchall()
    print("\n--- REGISTRO GENERAL DE EMPRESAS ---")
    for f in filas:
        dueno = f[2] if f[2] else "Sin asignar"
        admin = f[3] if f[3] else "Sin asignar"
        print(f"ID: {f[0]} | Empresa: {f[1]} | Dueño: {dueno} | Admin: {admin}")
    conn.close()


# MÓDULO: GESTIÓN DE EMPRESA (ADMIN DE EMPRESA / DUEÑO)


def crear_departamento(user):
    nombre_depto = input("Nombre del departamento: ").strip()
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Departamento (nombre_depto, id_empresa) VALUES (?, ?)", (nombre_depto, user['id_empresa']))
    conn.commit()
    conn.close()
    print(f"Departamento '{nombre_depto}' creado.")

def crear_usuario_empresa(user, es_admin=False):
    print(f"\n--- CREAR USUARIO EN {user['nombre_empresa']} ---")
    print("Roles disponibles:")
    if es_admin:
        print("3. Dueño")
    print("4. Jefe de Departamento")
    print("5. Empleado")
    rol_opc = int(input("Seleccione número de rol: ").strip())

    if not es_admin and rol_opc not in [4, 5]:
        print("El Dueño solo puede crear Jefes de Departamento o Empleados.")
        return

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id_departamento, nombre_depto FROM Departamento WHERE id_empresa = ?", (user['id_empresa'],))
    deptos = cursor.fetchall()
    if not deptos:
        print("Debe crear al menos un departamento primero.")
        conn.close()
        return

    print("\nDepartamentos:")
    for d in deptos:
        print(f"[{d[0]}] {d[1]}")
    id_depto = int(input("ID del Departamento: ").strip())

    codigo = input("Código del empleado: ").strip()
    nombres = input("Nombres: ").strip()
    apellidos = input("Apellidos: ").strip()
    correo = input("Correo: ").strip()
    password = input("Contraseña: ").strip()

    id_jefe = None
    if rol_opc == 5:
        cursor.execute("SELECT id_usuario, nombres, apellidos FROM Usuario WHERE id_departamento = ? AND id_rol = 4", (id_depto,))
        jefes = cursor.fetchall()
        if jefes:
            print("\nJefe directo del departamento:")
            for j in jefes:
                print(f"[{j[0]}] {j[1]} {j[2]}")
            opc_j = int(input("ID del jefe directo (0 para ninguno): ").strip())
            if opc_j > 0: id_jefe = opc_j

    cursor.execute("""
        INSERT INTO Usuario (codigo_usuario, nombres, apellidos, correo, contrasena, id_rol, id_empresa, id_departamento, id_jefe, fecha_ingreso, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), 'Activo')
    """, (codigo, nombres, apellidos, correo, encriptar(password), rol_opc, user['id_empresa'], id_depto, id_jefe))
    conn.commit()
    conn.close()
    print(f"Usuario {nombres} {apellidos} registrado exitosamente.")

def crear_tarea_empresa(user):
    print("\n--- CREAR TAREA EMPRESARIAL ---")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombres, apellidos FROM Usuario WHERE id_empresa = ? AND id_usuario != ?", (user['id_empresa'], user['id_usuario']))
    usuarios = cursor.fetchall()
    if not usuarios:
        print("No hay personal en la empresa para asignar tareas.")
        conn.close()
        return

    for u in usuarios:
        print(f"[{u[0]}] {u[1]} {u[2]}")
    id_asignado = int(input("ID de la persona a asignar: ").strip())

    cursor.execute("SELECT id_departamento FROM Usuario WHERE id_usuario = ?", (id_asignado,))
    fila = cursor.fetchone()
    id_depto = fila[0] if fila and fila[0] else 1

    codigo = input("Código de tarea (ej. T-101): ").strip()
    titulo = input("Título: ").strip()
    desc = input("Descripción: ").strip()
    vence = input("Fecha vencimiento (AAAA-MM-DD): ").strip()

    cursor.execute("""
        INSERT INTO Tarea (codigo_tarea, titulo, descripcion, id_empresa, id_departamento, id_usuario_asignado, id_usuario_creador, id_prioridad, id_estado_tarea, fecha_vencimiento)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?)
    """, (codigo, titulo, desc, user['id_empresa'], id_depto, id_asignado, user['id_usuario'], vence))
    conn.commit()
    conn.close()
    print("Tarea creada y asignada.")

def ver_todas_las_tareas_empresa(user):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.codigo_tarea, t.titulo, CONCAT(u.nombres, ' ', u.apellidos) AS asignado, 
               d.nombre_depto, et.nombre_estado, t.fecha_vencimiento
        FROM Tarea t
        INNER JOIN Usuario u ON t.id_usuario_asignado = u.id_usuario
        INNER JOIN Departamento d ON t.id_departamento = d.id_departamento
        INNER JOIN EstadoTarea et ON t.id_estado_tarea = et.id_estado_tarea
        WHERE t.id_empresa = ?
    """, (user['id_empresa'],))
    tareas = cursor.fetchall()
    print(f"\n--- TODAS LAS TAREAS DE {user['nombre_empresa']} ---")
    for t in tareas:
        print(f"[{t[0]}] {t[1]} | Asignado: {t[2]} | Depto: {t[3]} | Estado: {t[4]} | Vence: {t[5]}")
    conn.close()

# ============================================================
# MÓDULO: JEFE DE DEPARTAMENTO
# ============================================================

def jefe_asignar_tarea(user):
    print(f"\n--- [JEFE] ASIGNAR TAREA EN DEPARTAMENTO ---")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_usuario, nombres, apellidos FROM Usuario 
        WHERE id_departamento = ? AND id_rol = 5 AND estado = 'Activo'
    """, (user['id_departamento'],))
    empleados = cursor.fetchall()

    if not empleados:
        print("No tienes empleados adscritos a tu departamento.")
        conn.close()
        return

    for emp in empleados:
        print(f"[{emp[0]}] {emp[1]} {emp[2]}")
    id_asignado = int(input("ID del empleado: ").strip())

    codigo = input("Código de tarea: ").strip()
    titulo = input("Título: ").strip()
    desc = input("Descripción: ").strip()
    vence = input("Fecha de vencimiento (AAAA-MM-DD): ").strip()

    cursor.execute("""
        INSERT INTO Tarea (codigo_tarea, titulo, descripcion, id_empresa, id_departamento, id_usuario_asignado, id_usuario_creador, id_prioridad, id_estado_tarea, fecha_vencimiento)
        VALUES (?, ?, ?, ?, ?, ?, ?, 2, 1, ?)
    """, (codigo, titulo, desc, user['id_empresa'], user['id_departamento'], id_asignado, user['id_usuario'], vence))
    conn.commit()
    conn.close()
    print("Tarea asignada.")

def jefe_ver_tareas_departamento(user):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.codigo_tarea, t.titulo, CONCAT(u.nombres, ' ', u.apellidos) AS asignado, et.nombre_estado, t.fecha_vencimiento
        FROM Tarea t
        INNER JOIN Usuario u ON t.id_usuario_asignado = u.id_usuario
        INNER JOIN EstadoTarea et ON t.id_estado_tarea = et.id_estado_tarea
        WHERE t.id_departamento = ?
    """, (user['id_departamento'],))
    tareas = cursor.fetchall()
    print(f"\n--- TAREAS DE MI DEPARTAMENTO ---")
    for t in tareas:
        print(f"[{t[0]}] {t[1]} | Asignado: {t[2]} | Estado: {t[3]} | Vence: {t[4]}")
    conn.close()

# ============================================================
# MÓDULO: EMPLEADO Y MENSAJERÍA
# ============================================================

def empleado_ver_mis_tareas(user):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id_tarea, t.codigo_tarea, t.titulo, et.nombre_estado, t.fecha_vencimiento
        FROM Tarea t
        INNER JOIN EstadoTarea et ON t.id_estado_tarea = et.id_estado_tarea
        WHERE t.id_usuario_asignado = ?
    """, (user['id_usuario'],))
    tareas = cursor.fetchall()
    print("\n--- MIS TAREAS ---")
    if not tareas:
        print("No tienes tareas pendientes.")
    for t in tareas:
        print(f"[{t[0]}] {t[1]} - {t[2]} | Estado: {t[3]} | Vence: {t[4]}")
    
    if tareas:
        opc = input("\n¿Actualizar estado de alguna tarea? (s/n): ").lower()
        if opc == 's':
            id_t = int(input("ID de la tarea: "))
            print("[1] Sin Iniciar | [2] En Proceso | [3] Completada")
            st = int(input("Nuevo estado: "))
            cursor.execute("UPDATE Tarea SET id_estado_tarea = ? WHERE id_tarea = ? AND id_usuario_asignado = ?", (st, id_t, user['id_usuario']))
            conn.commit()
            print("Estado actualizado.")
    conn.close()

def enviar_mensaje(user):
    print("\n--- ENVIAR MENSAJE ---")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombres, apellidos FROM Usuario WHERE id_empresa = ? AND id_usuario != ?", (user['id_empresa'], user['id_usuario']))
    usuarios = cursor.fetchall()
    for u in usuarios:
        print(f"[{u[0]}] {u[1]} {u[2]}")
    destinatario = int(input("ID destinatario: ").strip())
    contenido = input("Mensaje: ").strip()

    cursor.execute("INSERT INTO Mensaje (id_emisor, id_receptor, contenido) VALUES (?, ?, ?)", (user['id_usuario'], destinatario, contenido))
    conn.commit()
    conn.close()
    print("Mensaje enviado.")

def ver_mensajes(user):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.contenido, CONCAT(u.nombres, ' ', u.apellidos), m.fecha_envio
        FROM Mensaje m
        INNER JOIN Usuario u ON m.id_emisor = u.id_usuario
        WHERE m.id_receptor = ?
        ORDER BY m.fecha_envio DESC
    """, (user['id_usuario'],))
    mensajes = cursor.fetchall()
    print("\n--- MENSAJES RECIBIDOS ---")
    if not mensajes:
        print("Bandeja vacía.")
    for m in mensajes:
        print(f"De: {m[1]} ({m[2]}): {m[0]}")
    conn.close()

# ============================================================
# MENÚ CON VALIDACIÓN DE ROLES
# ============================================================

def menu_usuario(user):
    while True:
        rol = user['nombre_rol']
        emp = user['nombre_empresa'] if user['nombre_empresa'] else "Global"
        print(f"\n==========================================")
        print(f" USUARIO: {user['nombres']} {user['apellidos']}")
        print(f" ROL: [{rol}] | EMPRESA: [{emp}]")
        print(f"==========================================")

        if rol == 'SuperAdmin':
            print("1. Crear Empresa y Declarar Dueño")
            print("2. Nombrar Admin de Empresa (Acceso Total a Empresa)")
            print("3. Listar Empresas, Dueños y Admins")
            print("4. Cerrar Sesión")
            opc = input("Opción: ").strip()
            if opc == '1': superadmin_crear_empresa_y_dueno()
            elif opc == '2': superadmin_asignar_admin_empresa()
            elif opc == '3': superadmin_listar_empresas()
            elif opc == '4': break

        elif rol == 'Admin de Empresa':
            # Control total a nivel corporativo
            print("1. Crear Departamento")
            print("2. Crear Usuario (Dueño / Jefe / Empleado)")
            print("3. Crear y Asignar Tarea")
            print("4. Ver Todas las Tareas de la Empresa")
            print("5. Enviar Mensaje")
            print("6. Ver Mensajes")
            print("7. Cerrar Sesión")
            opc = input("Opción: ").strip()
            if opc == '1': crear_departamento(user)
            elif opc == '2': crear_usuario_empresa(user, es_admin=True)
            elif opc == '3': crear_tarea_empresa(user)
            elif opc == '4': ver_todas_las_tareas_empresa(user)
            elif opc == '5': enviar_mensaje(user)
            elif opc == '6': ver_mensajes(user)
            elif opc == '7': break

        elif rol == 'Dueño':
            print("1. Crear Departamento")
            print("2. Crear Usuario (Jefe de Depto / Empleado)")
            print("3. Crear Tarea")
            print("4. Ver Todas las Tareas de la Empresa")
            print("5. Enviar Mensaje")
            print("6. Ver Mensajes")
            print("7. Cerrar Sesión")
            opc = input("Opción: ").strip()
            if opc == '1': crear_departamento(user)
            elif opc == '2': crear_usuario_empresa(user, es_admin=False)
            elif opc == '3': crear_tarea_empresa(user)
            elif opc == '4': ver_todas_las_tareas_empresa(user)
            elif opc == '5': enviar_mensaje(user)
            elif opc == '6': ver_mensajes(user)
            elif opc == '7': break

        elif rol == 'Jefe Departamento':
            print("1. Asignar Tarea a Empleado de mi Área")
            print("2. Ver Tareas de mi Departamento")
            print("3. Enviar Mensaje")
            print("4. Ver Mensajes")
            print("5. Cerrar Sesión")
            opc = input("Opción: ").strip()
            if opc == '1': jefe_asignar_tarea(user)
            elif opc == '2': jefe_ver_tareas_departamento(user)
            elif opc == '3': enviar_mensaje(user)
            elif opc == '4': ver_mensajes(user)
            elif opc == '5': break

        elif rol == 'Empleado':
            print("1. Ver Mis Tareas Asignadas (Actualizar Estado)")
            print("2. Enviar Mensaje")
            print("3. Ver Mensajes")
            print("4. Cerrar Sesión")
            opc = input("Opción: ").strip()
            if opc == '1': empleado_ver_mis_tareas(user)
            elif opc == '2': enviar_mensaje(user)
            elif opc == '3': ver_mensajes(user)
            elif opc == '4': break

def main():
    while True:
        print("\n===================================")
        print("       TASKFLOW ENTERPRISE         ")
        print("===================================")
        print("1. Iniciar Sesión")
        print("2. Salir")
        opc = input("Seleccione: ").strip()
        if opc == '1':
            correo = input("Correo: ").strip()
            clave = input("Contraseña: ").strip()
            user = login(correo, clave)
            if user:
                menu_usuario(user)
            else:
                print("❌ Credenciales inválidas.")
        elif opc == '2':
            break

if __name__ == "__main__":
    main()