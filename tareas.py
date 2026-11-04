from db import conectar
from datetime import date, datetime



def imprimir_tareas(tareas):
    """Recibe la lista de las tuplas para transformarla en tablas"""
    if not tareas:
        print("No tiene ninguna tarea")
        return
    print(f"\n{'ID':<4} {'Código':<10} {'Título':<28} {'Asignado':<22} {'Estado':<14} {'Vence':<12} ")
    print("-" * 95)
    for t in tareas:
        print(f"{t[0]:<4} {t[1]:<10} {t[2][:27]:<28} {t[4][:21]:<22} {t[8]:<14} {str(t[10]):<12}")

def Obtener_Estado(conn):
    cur = conn.cursor()
    cur.execute("SELECT id_estado_tarea, nombre_estado from EstadoTarea")
    return cur.fetchall()

def Obtener_Prioridades(conn):
    cur = conn.cursor()
    cur.execute("SELECT id_prioridad, nivel_prioridad FROM prioridad")
    return cur.fetchall()



########################################################################################
# Estas funciones permiten ver filtros de tareas o sus detalles, sin hacer ningún cambio
########################################################################################

def tareas_de_usuario(conn, id_usuario):
    """Todas las tareas asignadas a un usuario"""
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id_tarea, t.codigo_tarea, t.titulo, t.descripcion,
               CONCAT(a.nombres,' ',a.apellidos) AS asignado,
               CONCAT(c.nombres,' ',c.apellidos) AS creador,
               d.nombre_depto, p.nivel_prioridad, et.nombre_estado,
               t.fecha_creacion, t.fecha_vencimiento, t.fecha_completada
        FROM Tarea t
        INNER JOIN Usuario a      ON t.id_usuario_asignado = a.id_usuario
        INNER JOIN Usuario c      ON t.id_usuario_creador  = c.id_usuario
        INNER JOIN Departamento d ON t.id_departamento     = d.id_departamento
        INNER JOIN Prioridad p    ON t.id_prioridad        = p.id_prioridad
        INNER JOIN EstadoTarea et ON t.id_estado_tarea     = et.id_estado_tarea
        WHERE t.id_usuario_asignado = ?
        ORDER BY t.fecha_vencimiento
    """, (id_usuario,))
    return cur.fetchall()


def tareas_usuario_por_estado(conn, id_usuario, id_estado):
    "Tareas de un usuario filtradas por estado"
    try:
        cur = conn.cursor()
        cur.execute(
            """
             SELECT t.id_tarea, t.codigo_tarea, t.titulo, t.descripcion,
                   CONCAT(a.nombres,' ',a.apellidos) AS asignado,
                   CONCAT(c.nombres,' ',c.apellidos) AS creador,
                   d.nombre_depto, p.nivel_prioridad, et.nombre_estado,
                   t.fecha_creacion, t.fecha_vencimiento, t.fecha_completada
            FROM Tarea t
            INNER JOIN Usuario a      ON t.id_usuario_asignado = a.id_usuario
            INNER JOIN Usuario c      ON t.id_usuario_creador  = c.id_usuario
            INNER JOIN Departamento d ON t.id_departamento     = d.id_departamento
            INNER JOIN Prioridad p    ON t.id_prioridad        = p.id_prioridad
            INNER JOIN EstadoTarea et ON t.id_estado_tarea     = et.id_estado_tarea
            WHERE t.id_usuario_asignado = ? AND t.id_estado_tarea = ?
            ORDER BY t.fecha_vencimiento
            """, (id_usuario, id_estado))
        return cur.fetchall()
    except Exception as e:
        print(f"Hubo un error al intentar filtrar las tareas del usuario: {e}")
        return []


def tareas_vencidas(conn, id_usuario):
    """Esta funcion se encarga de filtrar todas las tareas que un usuario tiene vencidas"""
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT t.id_tarea, t.codigo_tarea, t.titulo, t.descripcion,
                   CONCAT(a.nombres,' ',a.apellidos) AS asignado,
                   CONCAT(c.nombres,' ',c.apellidos) AS creador,
                   d.nombre_depto, p.nivel_prioridad, et.nombre_estado,
                   t.fecha_creacion, t.fecha_vencimiento, t.fecha_completada
            FROM Tarea t
            INNER JOIN Usuario a      ON t.id_usuario_asignado = a.id_usuario
            INNER JOIN Usuario c      ON t.id_usuario_creador  = c.id_usuario
            INNER JOIN Departamento d ON t.id_departamento     = d.id_departamento
            INNER JOIN Prioridad p    ON t.id_prioridad        = p.id_prioridad
            INNER JOIN EstadoTarea et ON t.id_estado_tarea     = et.id_estado_tarea
            WHERE t.id_usuario_asignado = ?
              AND t.fecha_vencimiento < CAST(GETDATE() AS DATE)
              AND t.id_estado_tarea <> 3
            ORDER BY t.fecha_vencimiento
            """, (id_usuario,))
        return cur.fetchall()
    except Exception as e:
        print(f"Hubo un error al filtrar las tareas: {e}")
        return []
    

def buscar_tareas(conn, id_usuario, texto):
    """Se filtran tareas, mostrando aquellas cuyos titulos coinciden con el texto ingresado"""
    try:
        cur = conn.cursor()
        patron = f"%{texto}%"
        cur.execute("""
        SELECT t.id_tarea, t.codigo_tarea, t.titulo, t.descripcion,
                   CONCAT(a.nombres,' ',a.apellidos) AS asignado,
                   CONCAT(c.nombres,' ',c.apellidos) AS creador,
                   d.nombre_depto, p.nivel_prioridad, et.nombre_estado,
                   t.fecha_creacion, t.fecha_vencimiento, t.fecha_completada
            FROM Tarea t
            INNER JOIN Usuario a      ON t.id_usuario_asignado = a.id_usuario
            INNER JOIN Usuario c      ON t.id_usuario_creador  = c.id_usuario
            INNER JOIN Departamento d ON t.id_departamento     = d.id_departamento
            INNER JOIN Prioridad p    ON t.id_prioridad        = p.id_prioridad
            INNER JOIN EstadoTarea et ON t.id_estado_tarea     = et.id_estado_tarea
            WHERE t.id_usuario_asignado = ?
              AND t.titulo LIKE ?
            ORDER BY t.fecha_vencimiento""", (id_usuario, patron))
        return cur.fetchall()
    except Exception as e:
        print (f"Ocurrió un error al buscar tareas coincidentes {e}")
        return []


def ver_detalles_tarea(conn, id_tarea, user):
    """Muestra todos los detalles de una tarea, como la descripción, titulo, prioridad, etc"""
    try:
        cur = conn.cursor()
        cur.execute(
        """SELECT t.codigo_tarea, t.titulo, t.descripcion,
                   CONCAT(a.nombres,' ',a.apellidos),
                   CONCAT(c.nombres,' ',c.apellidos),
                   d.nombre_depto, p.nivel_prioridad, et.nombre_estado,
                   t.fecha_creacion, t.fecha_vencimiento, t.fecha_completada
            FROM Tarea t
            INNER JOIN Usuario a      ON t.id_usuario_asignado = a.id_usuario
            INNER JOIN Usuario c      ON t.id_usuario_creador  = c.id_usuario
            INNER JOIN Departamento d ON t.id_departamento     = d.id_departamento
            INNER JOIN Prioridad p    ON t.id_prioridad        = p.id_prioridad
            INNER JOIN EstadoTarea et ON t.id_estado_tarea     = et.id_estado_tarea
            WHERE t.id_tarea = ?""", (id_tarea,)
        )
        t = cur.fetchone()
        if not t:
            print("Tarea no encontrada.")
            return

        if user["nombre_rol"] == "Empleado":
            cur.execute("SELECT id_usuario_asignado FROM Tarea WHERE id_tarea = ?", (id_tarea,))
            if cur.fetchone()[0] != user["id_usuario"]:
                print("No tienes permitido ver esta tarea")
                return
            
        print(f"\n=== TAREA {t[0]} ===")
        print(f"Título:      {t[1]}")
        print(f"Descripción: {t[2] or '—'}")
        print(f"Asignado a:  {t[3]}")
        print(f"Creada por:  {t[4]}")
        print(f"Depto:       {t[5]}")
        print(f"Prioridad:   {t[6]}")
        print(f"Estado:      {t[7]}")
        print(f"Creada:      {t[8]}  | Vence: {t[9]}  | Completada: {t[10] or '—'}")
    except Exception as e:
        print(f"Error al intentar abrir la tarea {e}")





    ##################################################################################
    #Las funciones de aquí en más editan e interactúan con las tareas de forma directa
    ##################################################################################
def Crear_Tarea(user, conn, es_admin=False):
    cur = conn.cursor()

    if es_admin:
        cur.execute("""
        SELECT u.id_usuario, u.nombres, u.apellidos
        FROM Usuario u
        WHERE u.id_empresa = ? AND u.id_usuario <> ? AND u.estado = 'Activo'""", (user["id_empresa"], user["id_usuario"]))

    else:
        cur.execute(
            """
        SELECT u.id_usuario, u.nombres, u.apellidos
        FROM Usuario u
        WHERE u.id_jefe = ? AND u.estado = 'Activo'""", (user["id_usuario"]))

    usuarios = cur.fetchall()
    if not usuarios:
        print("No tienes usuarios disponibles para asignar.")
        return

    print("\nUsuarios disponibles:")
    for u in usuarios:
        print(f"[{u[0]}] {u[1]} {u[2]}")  

    try:
        id_asignado = int(input("ID del asignado: ").strip())
    except ValueError:
        print("ID inválido")
        return

    ids_validos = [u[0] for u in usuarios]
    if id_asignado not in ids_validos:
        print("Ese usuario no está permitido en este contexto.")
        return

    #Obtiene el departamento del usuario asignado
    cur.execute("SELECT id_departamento FROM Usuario WHERE id_usuario = ?", (id_asignado,))
    fila = cur.fetchone()
    if not fila or fila[0] is None:
        print("El usuario asignado no tiene departamento. Asígnalo primero.")
        return
    id_depto = fila[0]

    #Pide los datos de la tarea
    codigo = input("Código (ej. T-101): ").strip()
    titulo = input("Título: ").strip()
    desc = input("Descripción: ").strip()
    vence = input("Vencimiento (AAAA-MM-DD): ").strip()

    if not codigo or not titulo or not vence:
        print("Código, título y vencimiento son obligatorios.")
        return

    cur.execute("SELECT 1 FROM Tarea WHERE codigo_tarea = ?", (codigo,))
    if cur.fetchone():
        print("Ya existe una tarea con ese código.")
        return

    try:
        datetime.strptime(vence, "%Y-%m-%d")
    except ValueError:
        print("Formato de fecha inválido. Usa AAAA-MM-DD.")
        return

    prioridades = Obtener_Prioridades(conn)
    print("\nPrioridades:")
    for p in prioridades:
        print(f"[{p[0]}] {p[1]}")

    try:
        id_prioridad = int(input("ID prioridad: ").strip())
    except ValueError:
        print("ID inválido.")
        return

    if id_prioridad not in [p[0] for p in prioridades]:
        print("Prioridad inválida.")
        return

    try:
        cur.execute("""INSERT INTO Tarea (
                codigo_tarea, titulo, descripcion, id_empresa, id_departamento,
                id_usuario_asignado, id_usuario_creador, id_prioridad,
                id_estado_tarea, fecha_vencimiento
            )
            OUTPUT INSERTED.id_tarea
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (codigo, titulo, desc, user["id_empresa"], id_depto,
              id_asignado, user["id_usuario"], id_prioridad, vence))
        id_tarea = cur.fetchone()[0]
        conn.commit()
        print(f"Tarea '{titulo}' creada (ID interno {id_tarea}).")
    except Exception as e:
        print(f"Error al crear tarea: {e}")



def Cambiar_Estado_Tarea(user, conn, id_tarea, nuevo_estado):
    """Cambiar el estado de una tarea, solo a quien se le asigno la tarea, su jefe o un administrador"""
    cur = conn.cursor()
    cur.execute("""
        SELECT id_estado_tarea, id_usuario_asignado, id_usuario_creador
        FROM Tarea WHERE id_tarea = ?
        """, (id_tarea,))
    fila = cur.fetchone()
    if not fila:
        print("Tarea no encontrada")
        return
    estado_actual, asignado, creador = fila

    roles_especiales = ("SuperAdmin", "Admin de Empresa", "Dueño", "Jefe Departamento")
    if user["id_usuario"] not in (asignado, creador) and user["nombre_rol"] not in roles_especiales:
        print("No tienes permiso para editar esta tarea")
        return

    if estado_actual == nuevo_estado:
        print("La tarea ta está en ese estado")
        return

    try:
        if nuevo_estado == 3: #Completa
            cur.execute("""
                UPDATE Tarea
                SET id_estado_tarea = ?, fecha_completada = GETDATE()
                WHERE id_tarea = ?
            """, (nuevo_estado, id_tarea))

        else:
            cur.execute("""
                UPDATE Tarea
                SET id_estado_tarea = ?, fecha_completada = NULL
                WHERE id_tarea = ?
            """, (nuevo_estado, id_tarea))
        conn.commit()
        print("Estado Actualizado")

    except Exception as e:
        print(f"Hubo un error al cambiar el estado de la tarea: {e}")




#A partir de aquí están los menús principales relacionados a tareas

def menu_mis_tareas(user):
    while True:
        print("---Mis tareas---")
        print("1-Ver mis tareas")
        print("2-Filtrar por estado")
        print("3-Ver tareas vencidas")
        print("4-Buscar en mis tareas")
        print("5-Ver detalles de una tarea")
        print("6-Cambiar estado de una tarea")
        print("7-Volver")

        opcion = input("¿Qué desea hacer?").strip(" ")

        conn = conectar()
        if not conn:
            return
        try:
            if opcion == "1":
                imprimir_tareas(tareas_de_usuario(conn, user["id_usuario"]))  

            elif opcion == "2":
                estados = Obtener_Estado(conn)
                for e in estados:
                    print(f"[{e[0]}] {e[1]}")
                try:
                    id_est = int(input("ID estado: ").strip(" "))
                except ValueError:
                    continue
                imprimir_tareas(tareas_usuario_por_estado(conn, user["id_usuario"], id_est))

            elif opcion == "3":
                imprimir_tareas(tareas_vencidas(conn, user["id_usuario"]))

            elif opcion == "4":
                texto = input("Texto a buscar: ").strip(" ")
                if texto:
                    imprimir_tareas(buscar_tareas(conn, user["id_usuario"], texto))

            elif opcion == "5":
                try:
                    id_t = int(input("ID de la trea: ").strip(" "))
                except ValueError:
                    continue
                ver_detalles_tarea(conn, id_t, user)

            elif opcion == "6": 
                try:
                    id_t = int(input("ID de la tarea: ").strip(" "))
                except ValueError:
                    continue
                estados = Obtener_Estado(conn)
                for e in estados:
                    print(f"[{e[0]}] {e[1]}")
                try:
                    nuevo = int(input("Nuevo estado: ").strip(" "))
                except ValueError:
                    continue
                Cambiar_Estado_Tarea(user, conn, id_t, nuevo)

            elif opcion == "7":
                break
        finally:
            conn.close()


def menu_tareas_otros(user):
    es_admin = user["nombre_rol"] in ("Admin de Empresa", "Dueño", "SuperAdmin")
    
    while True:
        print("---Mis tareas---")
        print("1-Ver tareas del usuario")
        print("2-Ver detalles de una tarea")
        print("3-Crear tarea")
        print("4-Volver")

        opciones = input("¿Qué desea hacer?").strip(" ")

        if opciones == "4":
            break

        conn = conectar()
        if not conn:
            return
        try:
            if opciones in ("1", "2"):
                cur = conn.cursor()
                if es_admin:
                    cur.execute("""
                        SELECT id_usuario, nombres, apellidos FROM Usuario
                        WHERE id_empresa = ? AND estado = 'Activo' AND id_usuario <> ?
                    """, (user["id_empresa"], user["id_usuario"]))
                else:
                    cur.execute("""
                        SELECT id_usuario, nombres, apellidos FROM Usuario
                        WHERE id_jefe = ? AND estado = 'Activo'
                    """, (user["id_usuario"],))
                candidatos = cur.fetchall()

                if not candidatos:
                    print("No hay usuarios disponibles")
                    continue

                print("Usuarios Disponibles")
                for u in candidatos:
                    print(f"[{u[0]}] {u[1]} {u[2]}")

                try:
                    id_u = int(input("Escriba el ID del usuario: ").strip(" "))
                except ValueError:
                    continue

                if id_u not in [u[0] for u in candidatos]:
                    print("Este usuario no está permitido")
                    continue


                if opciones == "1":
                    imprimir_tareas(tareas_de_usuario(conn, id_u))

                elif opciones == "2":
                    try:
                        id_t = int(input("Escriba el ID de la tarea").strip(" "))
                    except ValueError:
                        continue
                    ver_detalles_tarea(conn, id_t, user)

            elif opciones == "3":
                Crear_Tarea(user, conn, es_admin=es_admin)
        finally:
            conn.close()
            
        





