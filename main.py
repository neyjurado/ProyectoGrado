from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import Optional, List
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from firebase_service import upload_image_to_firebase

app = FastAPI(
    title="API Liga Conocoto",
    description="Backend definitivo para la gestión deportiva de la LDP Conocoto"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 1. MODELOS DE DATOS (PYDANTIC)
# ---------------------------------------------------------
class JugadorCrear(BaseModel):
    cedula: str
    nombre: str
    apellido: str
    fecha_nacimiento: date
    id_equipo: int
    url_foto: Optional[str] = None
    numero_camiseta: int
    url_documento: Optional[str] = None  
    acepta_terminos: bool                

class EquipoCrear(BaseModel):
    nombre_equipo: str
    fecha_fundacion: Optional[date] = None
    categoria: str
    url_logo: Optional[str] = None

class UsuarioRegistro(BaseModel):
    cedula: str
    correo: str
    password: str

class ArbitroCrear(BaseModel):
    nombre: str
    apellido: str
    experiencia_anios: Optional[int] = None
    url_foto: Optional[str] = None

class UsuarioLogin(BaseModel):
    correo: str
    password: str

class GenerarCalendarioRequest(BaseModel):
    fecha_inicio: date

class PartidoActualizar(BaseModel):
    fecha: str
    hora: str
    id_arbitro: Optional[int] = None

class IncidenciaJugadorRequest(BaseModel):
    id_jugador: int
    goles: int
    amarillas: int
    rojas: int

class FinalizarPartidoRequest(BaseModel):
    goles_local: int
    goles_visitante: int
    novedades: Optional[str] = None
    incidencias: List[IncidenciaJugadorRequest]

class TraspasoRequest(BaseModel):
    id_nuevo_equipo: int
    nuevo_numero_camiseta: int

class CategoriaRequest(BaseModel):
    nueva_categoria: str

# NUEVOS MODELOS PARA EL DASHBOARD DEL JUGADOR
class AsistenciaRequest(BaseModel):
    id_partido: int
    id_jugador: int
    estado: str # 'Asistiré', 'No asistiré'

class CalificacionArbitro(BaseModel):
    id_arbitro: int
    id_jugador: int
    id_partido: int
    puntaje: int

# ---------------------------------------------------------
# 2. RUTAS DE LA API - PANEL ADMINISTRADOR (INTACTAS)
# ---------------------------------------------------------

@app.get("/")
def ruta_raiz():
    return {"mensaje": "¡API Liga Conocoto Operativa al 100%!"}

@app.get("/equipos")
def obtener_equipos():
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Error de BD")
    cursor = conn.cursor()
    cursor.execute("SELECT Id_Equipo, Nombre_Equipo, Categoria, Url_Logo FROM Equipos")
    equipos = [{"id": r.Id_Equipo, "nombre": r.Nombre_Equipo, "categoria": r.Categoria, "url_logo": r.Url_Logo} for r in cursor.fetchall()]
    conn.close()
    return equipos

@app.post("/equipos")
def crear_equipo(equipo: EquipoCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Equipo FROM Equipos WHERE Nombre_Equipo = ?", (equipo.nombre_equipo,))
        if cursor.fetchone(): raise HTTPException(status_code=400, detail="¡Atención! Ya existe un equipo registrado con ese nombre exacto.")
        cursor.execute("INSERT INTO Equipos (Nombre_Equipo, Fecha_Fundacion, Categoria, Url_Logo) VALUES (?, ?, ?, ?)", (equipo.nombre_equipo, equipo.fecha_fundacion, equipo.categoria, equipo.url_logo))
        conn.commit()
        return {"mensaje": f"Equipo '{equipo.nombre_equipo}' creado exitosamente."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/equipos/{id_equipo}")
def actualizar_equipo(id_equipo: int, equipo: EquipoCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Equipo FROM Equipos WHERE Nombre_Equipo = ? AND Id_Equipo <> ?", (equipo.nombre_equipo, id_equipo))
        if cursor.fetchone(): raise HTTPException(status_code=400, detail="¡Atención! Ya existe otro equipo registrado con ese nombre.")
        cursor.execute("UPDATE Equipos SET Nombre_Equipo = ?, Categoria = ?, Fecha_Fundacion = ?, Url_Logo = ? WHERE Id_Equipo = ?", (equipo.nombre_equipo, equipo.categoria, equipo.fecha_fundacion, equipo.url_logo, id_equipo))
        conn.commit()
        return {"mensaje": "Equipo actualizado correctamente."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/equipos/{id_equipo}")
def eliminar_equipo(id_equipo: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) as total FROM Jugadores WHERE Id_Equipo = ?", (id_equipo,))
        if cursor.fetchone().total > 0: raise HTTPException(status_code=400, detail="No se puede eliminar el equipo porque tiene jugadores inscritos.")
        cursor.execute("DELETE FROM Equipos WHERE Id_Equipo = ?", (id_equipo,))
        conn.commit()
        return {"mensaje": "El equipo ha sido dado de baja exitosamente."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/jugadores")
def obtener_jugadores():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT j.Id_Jugador, j.Cedula, j.Nombre, j.Apellido, j.Fecha_Nacimiento, j.Numero_Camiseta, j.Url_Foto, 
                   j.Id_Equipo, e.Nombre_Equipo, j.Url_Documento, e.Categoria
            FROM Jugadores j LEFT JOIN Equipos e ON j.Id_Equipo = e.Id_Equipo ORDER BY j.Id_Jugador DESC
        """)
        lista_jugadores = []
        for row in cursor.fetchall():
            lista_jugadores.append({
                "id_jugador": row.Id_Jugador, "cedula": row.Cedula, "nombre": row.Nombre, "apellido": row.Apellido,
                "fecha_nacimiento": row.Fecha_Nacimiento, "numero_camiseta": row.Numero_Camiseta,
                "url_foto": row.Url_Foto, "id_equipo": row.Id_Equipo, "nombre_equipo": row.Nombre_Equipo,
                "categoria_equipo": row.Categoria, "url_documento": row.Url_Documento if hasattr(row, 'Url_Documento') else ''
            })
        return lista_jugadores
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/jugadores")
def crear_jugador(jugador: JugadorCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Jugador FROM Jugadores WHERE Id_Equipo = ? AND Numero_Camiseta = ?", (jugador.id_equipo, jugador.numero_camiseta))
        if cursor.fetchone(): raise HTTPException(status_code=400, detail=f"¡Error! La camiseta #{jugador.numero_camiseta} ya está asignada.")
        cursor.execute("""
            INSERT INTO Jugadores (Cedula, Nombre, Apellido, Fecha_Nacimiento, Id_Equipo, Url_Foto, Numero_Camiseta, Url_Documento, Acepta_Terminos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (jugador.cedula, jugador.nombre, jugador.apellido, jugador.fecha_nacimiento, jugador.id_equipo, jugador.url_foto, jugador.numero_camiseta, jugador.url_documento, jugador.acepta_terminos))
        conn.commit()
        return {"mensaje": f"Jugador {jugador.nombre} {jugador.apellido} registrado exitosamente."}
    except HTTPException: raise 
    except Exception as e:
        conn.rollback()
        if 'UNIQUE KEY constraint' in str(e): raise HTTPException(status_code=400, detail="Este documento de identidad ya está registrado.")
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/jugadores/{id_jugador}")
def actualizar_jugador(id_jugador: int, jugador: JugadorCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Jugador FROM Jugadores WHERE Id_Equipo = ? AND Numero_Camiseta = ? AND Id_Jugador <> ?", (jugador.id_equipo, jugador.numero_camiseta, id_jugador))
        if cursor.fetchone(): raise HTTPException(status_code=400, detail=f"¡Error! La camiseta #{jugador.numero_camiseta} ya está ocupada.")
        cursor.execute("""
            UPDATE Jugadores SET Cedula = ?, Nombre = ?, Apellido = ?, Fecha_Nacimiento = ?, Id_Equipo = ?, Url_Foto = ?, Numero_Camiseta = ?, Url_Documento = ?, Acepta_Terminos = ?
            WHERE Id_Jugador = ?
        """, (jugador.cedula, jugador.nombre, jugador.apellido, jugador.fecha_nacimiento, jugador.id_equipo, jugador.url_foto, jugador.numero_camiseta, jugador.url_documento, jugador.acepta_terminos, id_jugador))
        conn.commit()
        return {"mensaje": "Jugador actualizado con éxito."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/jugadores/{id_jugador}")
def eliminar_jugador(id_jugador: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Jugadores WHERE Id_Jugador = ?", (id_jugador,))
        conn.commit()
        return {"mensaje": "El jugador ha sido dado de baja exitosamente."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/arbitros")
def obtener_arbitros():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Arbitro, Nombre, Apellido, Experiencia_Anios, Url_Foto FROM Arbitros ORDER BY Id_Arbitro DESC")
        return [{"id_arbitro": r.Id_Arbitro, "nombre": r.Nombre, "apellido": r.Apellido, "experiencia_anios": r.Experiencia_Anios, "url_foto": r.Url_Foto} for r in cursor.fetchall()]
    finally: conn.close()

@app.post("/arbitros")
def crear_arbitro(arbitro: ArbitroCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Arbitros (Nombre, Apellido, Experiencia_Anios, Url_Foto) VALUES (?, ?, ?, ?)", (arbitro.nombre, arbitro.apellido, arbitro.experiencia_anios, arbitro.url_foto))
        conn.commit()
        return {"mensaje": f"Árbitro {arbitro.nombre} registrado exitosamente."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/partidos")
def obtener_partidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.Id_Partido, p.Fecha_Hora, p.Estado, p.Goles_Local, p.Goles_Visitante, p.Id_Arbitro,
                   el.Nombre_Equipo AS Local, ev.Nombre_Equipo AS Visitante,
                   a.Nombre AS Arbitro_Nombre, a.Apellido AS Arbitro_Apellido
            FROM Partidos p
            INNER JOIN Equipos el ON p.Id_Equipo_Local = el.Id_Equipo
            INNER JOIN Equipos ev ON p.Id_Equipo_Visitante = ev.Id_Equipo
            LEFT JOIN Arbitros a ON p.Id_Arbitro = a.Id_Arbitro
            ORDER BY p.Fecha_Hora ASC
        """)
        partidos = []
        for r in cursor.fetchall():
            arbitro_str = f"{r.Arbitro_Nombre} {r.Arbitro_Apellido}" if r.Arbitro_Nombre else "Sin asignar"
            partidos.append({
                "id_partido": r.Id_Partido, "local": r.Local, "visitante": r.Visitante,
                "fecha": r.Fecha_Hora.strftime("%Y-%m-%d") if r.Fecha_Hora else "",
                "hora": r.Fecha_Hora.strftime("%H:%M") if r.Fecha_Hora else "",
                "goles_local": r.Goles_Local if r.Goles_Local is not None else 0,
                "goles_visitante": r.Goles_Visitante if r.Goles_Visitante is not None else 0,
                "estado": r.Estado, "arbitro": arbitro_str, "id_arbitro": r.Id_Arbitro
            })
        return partidos
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/partidos/{id_partido}")
def actualizar_partido(id_partido: int, partido: PartidoActualizar):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        fecha_hora_str = f"{partido.fecha} {partido.hora}"
        fecha_hora_dt = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M")
        cursor.execute("SELECT COUNT(*) as total FROM Partidos WHERE Fecha_Hora = ? AND Id_Partido <> ?", (fecha_hora_dt, id_partido))
        if cursor.fetchone().total > 0: raise HTTPException(status_code=400, detail="¡Conflicto de Horario! Ya existe otro partido programado en esa misma fecha y hora.")
        cursor.execute("UPDATE Partidos SET Fecha_Hora = ?, Id_Arbitro = ? WHERE Id_Partido = ?", (fecha_hora_dt, partido.id_arbitro, id_partido))
        conn.commit()
        return {"mensaje": "El partido ha sido reprogramado con éxito."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

def calcular_si_esta_suspendido(cursor, id_jugador: int, id_equipo: int) -> bool:
    cursor.execute("""
        SELECT p.Id_Partido, ISNULL(ej.Tarjetas_Amarillas, 0) as A, ISNULL(ej.Tarjetas_Rojas, 0) as R
        FROM Partidos p LEFT JOIN Estadisticas_Jugadores ej ON p.Id_Partido = ej.Id_Partido AND ej.Id_Jugador = ?
        WHERE (p.Id_Equipo_Local = ? OR p.Id_Equipo_Visitante = ?) AND p.Estado = 'Finalizado' ORDER BY p.Fecha_Hora ASC
    """, (id_jugador, id_equipo, id_equipo))
    historial = cursor.fetchall()
    suspensiones = 0; amarillas = 0
    for row in historial:
        if suspensiones > 0: suspensiones -= 1; continue
        if row.R > 0: suspensiones += 2
        elif row.A == 2: suspensiones += 1
        elif row.A == 1:
            amarillas += 1
            if amarillas == 5: suspensiones += 1; amarillas = 0
    return suspensiones > 0

@app.get("/partidos/{id_partido}/vocalia")
def obtener_datos_vocalia(id_partido: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Equipo_Local, Id_Equipo_Visitante FROM Partidos WHERE Id_Partido = ?", (id_partido,))
        partido = cursor.fetchone()
        if not partido: raise HTTPException(status_code=404, detail="Partido no encontrado")
        id_local, id_visitante = partido.Id_Equipo_Local, partido.Id_Equipo_Visitante
        
        cursor.execute("SELECT Id_Jugador, Nombre, Apellido, Numero_Camiseta, Url_Foto FROM Jugadores WHERE Id_Equipo = ?", (id_local,))
        j_local = [{"id_jugador": r.Id_Jugador, "nombre": r.Nombre, "apellido": r.Apellido, "numero_camiseta": r.Numero_Camiseta, "url_foto": r.Url_Foto, "suspendido": calcular_si_esta_suspendido(cursor, r.Id_Jugador, id_local)} for r in cursor.fetchall()]
        
        cursor.execute("SELECT Id_Jugador, Nombre, Apellido, Numero_Camiseta, Url_Foto FROM Jugadores WHERE Id_Equipo = ?", (id_visitante,))
        j_visitante = [{"id_jugador": r.Id_Jugador, "nombre": r.Nombre, "apellido": r.Apellido, "numero_camiseta": r.Numero_Camiseta, "url_foto": r.Url_Foto, "suspendido": calcular_si_esta_suspendido(cursor, r.Id_Jugador, id_visitante)} for r in cursor.fetchall()]
        
        return {"jugadores_local": j_local, "jugadores_visitante": j_visitante}
    finally: conn.close()

@app.post("/partidos/{id_partido}/finalizar")
def finalizar_partido(id_partido: int, req: FinalizarPartidoRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Partidos SET Goles_Local = ?, Goles_Visitante = ?, Estado = 'Finalizado', Novedades = ? WHERE Id_Partido = ?", (req.goles_local, req.goles_visitante, req.novedades, id_partido))
        for inc in req.incidencias:
            if inc.goles > 0 or inc.amarillas > 0 or inc.rojas > 0:
                cursor.execute("INSERT INTO Estadisticas_Jugadores (Id_Jugador, Id_Partido, Goles, Tarjetas_Amarillas, Tarjetas_Rojas) VALUES (?, ?, ?, ?, ?)", (inc.id_jugador, id_partido, inc.goles, inc.amarillas, inc.rojas))
        conn.commit()
        return {"mensaje": "Acta cerrada correctamente."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/partidos/{id_partido}/acta_detalles")
def obtener_detalles_acta(id_partido: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Novedades, Id_Equipo_Local, Id_Equipo_Visitante FROM Partidos WHERE Id_Partido = ?", (id_partido,))
        partido = cursor.fetchone()
        cursor.execute("""
            SELECT j.Nombre, j.Apellido, j.Id_Equipo, ej.Goles, ej.Tarjetas_Amarillas, ej.Tarjetas_Rojas
            FROM Estadisticas_Jugadores ej INNER JOIN Jugadores j ON ej.Id_Jugador = j.Id_Jugador WHERE ej.Id_Partido = ?
        """, (id_partido,))
        incidencias_db = cursor.fetchall()

        incidencias_local = []
        incidencias_visitante = []
        for r in incidencias_db:
            inc_dict = {"jugador": f"{r.Nombre} {r.Apellido}", "goles": r.Goles, "amarillas": r.Tarjetas_Amarillas, "rojas": r.Tarjetas_Rojas}
            if r.Id_Equipo == partido.Id_Equipo_Local: incidencias_local.append(inc_dict)
            elif r.Id_Equipo == partido.Id_Equipo_Visitante: incidencias_visitante.append(inc_dict)

        return {
            "novedades": partido.Novedades if hasattr(partido, 'Novedades') and partido.Novedades else "Ninguna novedad registrada durante el encuentro.",
            "incidencias_local": incidencias_local, "incidencias_visitante": incidencias_visitante
        }
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/estadisticas/posiciones/{categoria}")
def obtener_tabla_posiciones(categoria: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Equipo, Nombre_Equipo, Url_Logo FROM Equipos WHERE Categoria = ?", (categoria,))
        tabla = {}
        for r in cursor.fetchall(): tabla[r.Id_Equipo] = {"id_equipo": r.Id_Equipo, "nombre": r.Nombre_Equipo, "url_logo": r.Url_Logo, "pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "gd": 0, "pts": 0}
        
        cursor.execute("""
            SELECT p.Id_Equipo_Local, p.Id_Equipo_Visitante, p.Goles_Local, p.Goles_Visitante 
            FROM Partidos p INNER JOIN Equipos e ON p.Id_Equipo_Local = e.Id_Equipo
            WHERE p.Estado = 'Finalizado' AND e.Categoria = ?
        """, (categoria,))
        
        for p in cursor.fetchall():
            loc, vis, gl, gv = p.Id_Equipo_Local, p.Id_Equipo_Visitante, p.Goles_Local, p.Goles_Visitante
            if loc in tabla and vis in tabla:
                tabla[loc]["pj"] += 1; tabla[vis]["pj"] += 1
                tabla[loc]["gf"] += gl; tabla[loc]["gc"] += gv
                tabla[vis]["gf"] += gv; tabla[vis]["gc"] += gl
                if gl > gv: tabla[loc]["pg"] += 1; tabla[loc]["pts"] += 3; tabla[vis]["pp"] += 1
                elif gl < gv: tabla[vis]["pg"] += 1; tabla[vis]["pts"] += 3; tabla[loc]["pp"] += 1
                else: tabla[loc]["pe"] += 1; tabla[loc]["pts"] += 1; tabla[vis]["pe"] += 1; tabla[vis]["pts"] += 1

        for k in tabla: tabla[k]["gd"] = tabla[k]["gf"] - tabla[k]["gc"]
        lista_ordenada = list(tabla.values()); lista_ordenada.sort(key=lambda x: (x["pts"], x["gd"], x["gf"]), reverse=True)
        return lista_ordenada
    finally: conn.close()

@app.get("/goleadores/{categoria}")
def obtener_goleadores(categoria: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TOP 10 j.Nombre, j.Apellido, e.Nombre_Equipo, SUM(ISNULL(est.Goles, 0)) as Total_Goles
            FROM Estadisticas_Jugadores est INNER JOIN Jugadores j ON est.Id_Jugador = j.Id_Jugador
            INNER JOIN Equipos e ON j.Id_Equipo = e.Id_Equipo WHERE e.Categoria = ? AND est.Goles > 0
            GROUP BY j.Nombre, j.Apellido, e.Nombre_Equipo ORDER BY Total_Goles DESC
        """, (categoria,))
        return [{"jugador": f"{r.Nombre} {r.Apellido}", "equipo": r.Nombre_Equipo, "goles": r.Total_Goles} for r in cursor.fetchall()]
    finally: conn.close()

@app.put("/jugadores/{id_jugador}/traspaso")
def realizar_traspaso_jugador(id_jugador: int, req: TraspasoRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Jugador FROM Jugadores WHERE Id_Equipo = ? AND Numero_Camiseta = ?", (req.id_nuevo_equipo, req.nuevo_numero_camiseta))
        if cursor.fetchone(): raise HTTPException(status_code=400, detail=f"¡Conflicto de dorsal! El número #{req.nuevo_numero_camiseta} ya está ocupado en ese equipo.")
        cursor.execute("UPDATE Jugadores SET Id_Equipo = ?, Numero_Camiseta = ? WHERE Id_Jugador = ?", (req.id_nuevo_equipo, req.nuevo_numero_camiseta, id_jugador))
        conn.commit()
        return {"mensaje": "El traspaso oficial del futbolista se ejecutó exitosamente."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/equipos/{id_equipo}/categoria")
def cambiar_categoria_equipo(id_equipo: int, req: CategoriaRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Equipos SET Categoria = ? WHERE Id_Equipo = ?", (req.nueva_categoria, id_equipo))
        conn.commit()
        return {"mensaje": "Categoría modificada correctamente."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

def generar_round_robin_por_categoria(cursor, categoria: str, fecha_base: date):
    cursor.execute("SELECT Id_Equipo FROM Equipos WHERE Categoria = ?", (categoria,))
    equipos = [row.Id_Equipo for row in cursor.fetchall()]
    if len(equipos) < 2: return []
    if len(equipos) % 2 != 0: equipos.append(None)
    num_equipos = len(equipos); mitad = num_equipos // 2
    horarios_disponibles = ["08:00", "10:00", "12:00", "14:00", "16:00"]
    partidos_generados = []; fecha_actual = fecha_base; todos_enfrentamientos = []
    
    for jornada in range(1, num_equipos):
        for i in range(mitad):
            local = equipos[i]; visitante = equipos[num_equipos - 1 - i]
            if local is not None and visitante is not None:
                if jornada % 2 == 0 and i == 0: todos_enfrentamientos.append((visitante, local))
                else: todos_enfrentamientos.append((local, visitante))
        equipos = [equipos[0]] + [equipos[-1]] + equipos[1:-1]
        
    partidos_diarios = 0
    for (eq_local, eq_visit) in todos_enfrentamientos:
        if partidos_diarios >= len(horarios_disponibles): fecha_actual += timedelta(days=7); partidos_diarios = 0
        f_h_str = f"{fecha_actual.strftime('%Y-%m-%d')} {horarios_disponibles[partidos_diarios]}"
        partidos_generados.append((eq_local, eq_visit, datetime.strptime(f_h_str, "%Y-%m-%d %H:%M"), 'Pendiente'))
        partidos_diarios += 1
    return partidos_generados

@app.post("/generar-calendario")
def generar_calendario(req: GenerarCalendarioRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Partidos")
        p_primera = generar_round_robin_por_categoria(cursor, "Primera", req.fecha_inicio)
        p_maxima = generar_round_robin_por_categoria(cursor, "Máxima", req.fecha_inicio + timedelta(days=1))
        todos = p_primera + p_maxima
        if not todos: raise HTTPException(status_code=400, detail="No hay suficientes equipos.")
        cursor.executemany("INSERT INTO Partidos (Id_Equipo_Local, Id_Equipo_Visitante, Fecha_Hora, Estado) VALUES (?, ?, ?, ?)", todos)
        conn.commit()
        return {"mensaje": f"¡Torneo unificado generado! {len(todos)} partidos cargados."}
    finally: conn.close()

@app.post("/login")
def iniciar_sesion(credenciales: UsuarioLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Usuario, Correo, Password_Hash, Rol, Id_Jugador FROM Usuarios WHERE Correo = ?", (credenciales.correo,))
        u = cursor.fetchone()
        if not u or credenciales.password != u.Password_Hash: raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        return {"usuario": {"id": u.Id_Usuario, "correo": u.Correo, "rol": u.Rol, "id_jugador": u.Id_Jugador if hasattr(u, 'Id_Jugador') else None}}
    finally: conn.close()

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), folder: Optional[str] = Form("images")):
    try: return {"url": upload_image_to_firebase(await file.read(), file.filename, folder)}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# =========================================================
# 3. NUEVAS RUTAS - MÓDULO JUGADOR (CAMERINO VIRTUAL)
# =========================================================

@app.get("/jugador/{id_jugador}/partidos")
def obtener_partidos_jugador(id_jugador: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Identificar el equipo actual del jugador
        cursor.execute("SELECT Id_Equipo FROM Jugadores WHERE Id_Jugador = ?", (id_jugador,))
        jugador = cursor.fetchone()
        if not jugador: raise HTTPException(status_code=404, detail="Jugador no encontrado.")
        id_equipo = jugador.Id_Equipo

        # 2. Traer todos los partidos donde juegue su equipo, y revisar su asistencia individual
        cursor.execute("""
            SELECT p.Id_Partido, p.Fecha_Hora, p.Estado, p.Goles_Local, p.Goles_Visitante, p.Id_Arbitro,
                   el.Nombre_Equipo AS Local, el.Url_Logo AS Logo_Local,
                   ev.Nombre_Equipo AS Visitante, ev.Url_Logo AS Logo_Visitante,
                   arb.Nombre AS Arb_Nombre, arb.Apellido AS Arb_Apellido,
                   ISNULL(a.Estado, 'Pendiente') AS Mi_Asistencia
            FROM Partidos p
            INNER JOIN Equipos el ON p.Id_Equipo_Local = el.Id_Equipo
            INNER JOIN Equipos ev ON p.Id_Equipo_Visitante = ev.Id_Equipo
            LEFT JOIN Arbitros arb ON p.Id_Arbitro = arb.Id_Arbitro
            LEFT JOIN Asistencia a ON p.Id_Partido = a.Id_Partido AND a.Id_Jugador = ?
            WHERE p.Id_Equipo_Local = ? OR p.Id_Equipo_Visitante = ?
            ORDER BY p.Fecha_Hora ASC
        """, (id_jugador, id_equipo, id_equipo))
        
        partidos_jugador = []
        for r in cursor.fetchall():
            # Si el partido está pendiente, verificamos si está suspendido matemáticamente para esa fecha
            suspendido = False
            if r.Estado == 'Pendiente':
                suspendido = calcular_si_esta_suspendido(cursor, id_jugador, id_equipo)

            arbitro_str = f"{r.Arb_Nombre} {r.Arb_Apellido}" if r.Arb_Nombre else "Sin asignar"
            
            partidos_jugador.append({
                "id_partido": r.Id_Partido,
                "fecha": r.Fecha_Hora.strftime("%Y-%m-%d"),
                "hora": r.Fecha_Hora.strftime("%H:%M"),
                "estado": r.Estado,
                "goles_local": r.Goles_Local,
                "goles_visitante": r.Goles_Visitante,
                "local": r.Local,
                "logo_local": r.Logo_Local,
                "visitante": r.Visitante,
                "logo_visitante": r.Logo_Visitante,
                "arbitro": arbitro_str,
                "id_arbitro": r.Id_Arbitro,
                "mi_asistencia": r.Mi_Asistencia,
                "estoy_suspendido": suspendido
            })
        return partidos_jugador
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/jugador/asistencia")
def registrar_asistencia(req: AsistenciaRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verificar si ya había marcado asistencia para actualizar, o si es nueva insertamos
        cursor.execute("SELECT Id_Asistencia FROM Asistencia WHERE Id_Partido = ? AND Id_Jugador = ?", (req.id_partido, req.id_jugador))
        if cursor.fetchone():
            cursor.execute("UPDATE Asistencia SET Estado = ? WHERE Id_Partido = ? AND Id_Jugador = ?", (req.estado, req.id_partido, req.id_jugador))
        else:
            cursor.execute("INSERT INTO Asistencia (Id_Partido, Id_Jugador, Estado) VALUES (?, ?, ?)", (req.id_partido, req.id_jugador, req.estado))
        conn.commit()
        return {"mensaje": "Asistencia registrada exitosamente."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/partido/{id_partido}/equipo/{id_equipo}/asistencias")
def obtener_camerino_virtual(id_partido: int, id_equipo: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Extrae a toda la plantilla del equipo y su respuesta de asistencia para ese partido
        cursor.execute("""
            SELECT j.Id_Jugador, j.Nombre, j.Apellido, j.Url_Foto, j.Numero_Camiseta,
                   ISNULL(a.Estado, 'Pendiente') AS Estado_Asistencia
            FROM Jugadores j
            LEFT JOIN Asistencia a ON j.Id_Jugador = a.Id_Jugador AND a.Id_Partido = ?
            WHERE j.Id_Equipo = ?
            ORDER BY j.Numero_Camiseta ASC
        """, (id_partido, id_equipo))
        
        companeros = []
        for r in cursor.fetchall():
            companeros.append({
                "id_jugador": r.Id_Jugador,
                "nombre": f"{r.Nombre} {r.Apellido}",
                "numero_camiseta": r.Numero_Camiseta,
                "url_foto": r.Url_Foto,
                "estado_asistencia": r.Estado_Asistencia,
                "suspendido": calcular_si_esta_suspendido(cursor, r.Id_Jugador, id_equipo) # Para avisar si el compañero no puede jugar
            })
        return companeros
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/jugador/calificar_arbitro")
def calificar_arbitro(calificacion: CalificacionArbitro):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Un jugador solo puede calificar a un árbitro 1 vez por partido
        cursor.execute("SELECT Id_Calificacion FROM Calificaciones_Arbitros WHERE Id_Partido = ? AND Id_Jugador = ?", (calificacion.id_partido, calificacion.id_jugador))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ya enviaste tu calificación del árbitro para este encuentro.")

        cursor.execute("""
            INSERT INTO Calificaciones_Arbitros (Id_Arbitro, Id_Jugador, Id_Partido, Puntaje, Fecha_Calificacion) 
            VALUES (?, ?, ?, ?, ?)
        """, (calificacion.id_arbitro, calificacion.id_jugador, calificacion.id_partido, calificacion.puntaje, datetime.now()))
        conn.commit()
        return {"mensaje": "¡Tu calificación fue enviada a la liga!"}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

# =========================================================
# RUTAS DE REGISTRO DE USUARIOS (JUGADORES)
# =========================================================
@app.post("/registro")
def registrar_usuario(req: UsuarioRegistro):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Validar que la Cédula exista en la tabla Jugadores (Que el admin ya lo haya inscrito)
        cursor.execute("SELECT Id_Jugador, Nombre, Apellido FROM Jugadores WHERE Cedula = ?", (req.cedula,))
        jugador = cursor.fetchone()
        
        if not jugador:
            raise HTTPException(status_code=404, detail="Cédula no encontrada. Tu dirigente de equipo debe inscribirte en la liga primero.")
            
        id_jugador = jugador.Id_Jugador
        
        # 2. Validar que el jugador no tenga ya una cuenta creada
        cursor.execute("SELECT Id_Usuario FROM Usuarios WHERE Id_Jugador = ?", (id_jugador,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Este jugador ya tiene una cuenta registrada en el sistema.")
            
        # 3. Validar que el correo no esté en uso
        cursor.execute("SELECT Id_Usuario FROM Usuarios WHERE Correo = ?", (req.correo,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Este correo electrónico ya está en uso.")
            
        # 4. Insertar en la tabla Usuarios vinculándolo con su Id_Jugador
        cursor.execute("""
            INSERT INTO Usuarios (Correo, Password_Hash, Rol, Id_Jugador)
            VALUES (?, ?, 'Jugador', ?)
        """, (req.correo, req.password, id_jugador))
        conn.commit()
        
        return {"mensaje": f"¡Bienvenido {jugador.Nombre}! Tu cuenta ha sido creada exitosamente. Ya puedes iniciar sesión."}
        
    except HTTPException: raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()