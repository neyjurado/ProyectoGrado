import re
import hashlib
import hmac
import secrets
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
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
    presidente: Optional[str] = None
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
    cedula: Optional[str] = None
    experiencia_anios: Optional[int] = None
    url_foto: Optional[str] = None

class UsuarioLogin(BaseModel):
    correo: str
    password: str

class AdminCredencialesRequest(BaseModel):
    correo: str
    password: str

class GenerarCalendarioRequest(BaseModel):
    fecha_inicio: date
    correo: str
    password: str

class PartidoActualizar(BaseModel):
    fecha: str
    hora: str
    id_arbitro: Optional[int] = None
    id_arbitro_2: Optional[int] = None
    id_arbitro_3: Optional[int] = None

class IncidenciaJugadorRequest(BaseModel):
    id_jugador: int
    goles: int
    amarillas: int
    rojas: int

class FinalizarPartidoRequest(BaseModel):
    goles_local: int
    goles_visitante: int
    novedades: Optional[str] = None
    foto_vocalia_url: Optional[str] = None
    incidencias: List[IncidenciaJugadorRequest]

class TraspasoRequest(BaseModel):
    id_nuevo_equipo: int
    nuevo_numero_camiseta: int

class CategoriaRequest(BaseModel):
    nueva_categoria: str

class SuspensionRequest(BaseModel):
    motivo: Optional[str] = None

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


PBKDF2_ITERACIONES = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_hex = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), PBKDF2_ITERACIONES).hex()
    return f'pbkdf2_sha256${PBKDF2_ITERACIONES}${salt}${hash_hex}'


def es_hash_pbkdf2(valor: str) -> bool:
    return isinstance(valor, str) and valor.startswith('pbkdf2_sha256$') and valor.count('$') == 3


def verificar_password(password: str, stored: str) -> bool:
    if es_hash_pbkdf2(stored):
        try:
            _, iteraciones_str, salt, hash_hex = stored.split('$')
            calculado = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), int(iteraciones_str)).hex()
            return hmac.compare_digest(calculado, hash_hex)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(password, stored or '')


def verificar_credenciales_admin(cursor, correo: str, password: str) -> None:
    cursor.execute("""
        SELECT Id_Usuario, Password_Hash, Rol
        FROM Usuarios
        WHERE Correo COLLATE SQL_Latin1_General_CP1_CS_AS = ?
    """, (correo,))
    u = cursor.fetchone()
    if not u or u.Rol != 'Administrador' or not verificar_password(password, u.Password_Hash):
        raise HTTPException(status_code=401, detail="Credenciales de administrador inválidas.")
    if not es_hash_pbkdf2(u.Password_Hash):
        cursor.execute("UPDATE Usuarios SET Password_Hash = ? WHERE Id_Usuario = ?", (hash_password(password), u.Id_Usuario))
        cursor.connection.commit()


def validar_password_segura(password: str) -> str:
    texto = (password or '').strip()
    if len(texto) < 8:
        return 'La contraseña debe tener al menos 8 caracteres.'
    if not re.search(r'[A-Z]', texto):
        return 'La contraseña debe incluir al menos una mayúscula.'
    if not re.search(r'[a-z]', texto):
        return 'La contraseña debe incluir al menos una minúscula.'
    if not re.search(r'\d', texto):
        return 'La contraseña debe incluir al menos un número.'
    if not re.search(r'[^\w\s]', texto):
        return 'La contraseña debe incluir al menos un carácter especial.'
    return ''


def normalizar_correo(correo: str) -> str:
    return (correo or '').strip().lower()


def validar_fecha_nacimiento_max_100(fecha_nacimiento: date) -> str:
    hoy = date.today()
    if fecha_nacimiento > hoy:
        return 'La fecha de nacimiento no puede ser futura.'
    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    if edad > 100:
        return 'La fecha de nacimiento no puede superar los 100 años.'
    return ''


def validar_fecha_fundacion_equipo(fecha_fundacion: Optional[date]) -> str:
    if fecha_fundacion is None:
        return ''
    hoy = date.today()
    if fecha_fundacion > hoy:
        return 'La fecha de fundación no puede ser futura.'
    if fecha_fundacion > hoy - timedelta(days=30):
        return 'La fecha de fundación debe tener al menos un mes de antigüedad.'
    return ''


def validar_arbitros_distintos(partido: PartidoActualizar) -> str:
    ids = [partido.id_arbitro, partido.id_arbitro_2, partido.id_arbitro_3]
    ids_limpios = [valor for valor in ids if valor is not None]
    if len(ids_limpios) != len(set(ids_limpios)):
        return 'Los tres árbitros del partido deben ser distintos.'
    return ''


def normalizar_nombre_equipo(nombre: str) -> str:
    if not nombre:
        return ""
    return re.sub(r'\s+', ' ', nombre.strip()).upper()


def validar_nombre_equipo(nombre: str) -> str:
    nombre_limpio = normalizar_nombre_equipo(nombre)
    if len(nombre_limpio) < 2:
        return 'El nombre del equipo debe tener al menos 2 caracteres válidos.'
    if len(nombre_limpio) > 50:
        return 'El nombre del equipo no puede exceder los 50 caracteres.'
    return ''


def validar_cedula_ecuatoriana(cedula: str) -> str:
    texto = (cedula or '').strip()
    if not re.fullmatch(r'\d{10}', texto):
        return 'La cédula debe tener exactamente 10 dígitos numéricos.'
    provincia = int(texto[0:2])
    tercer_digito = int(texto[2])
    if not ((1 <= provincia <= 24) or provincia == 30):
        return 'La cédula no pertenece a un código de provincia válido (01-24 o 30).'
    if tercer_digito > 5:
        return 'La cédula no tiene un tercer dígito válido para persona natural.'
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for digito, coeficiente in zip(texto[:9], coeficientes):
        producto = int(digito) * coeficiente
        if producto > 9:
            producto -= 9
        suma += producto
    verificador = (10 - (suma % 10)) % 10
    if verificador != int(texto[9]):
        return 'La cédula ingresada no es válida (dígito verificador incorrecto).'
    return ''


def validar_numero_camiseta(numero: int) -> str:
    if numero < 1 or numero > 99:
        return 'El número de camiseta debe estar entre 1 y 99.'
    return ''


def validar_experiencia_anios(valor: Optional[int]) -> str:
    if valor is None:
        return ''
    if valor < 0 or valor > 60:
        return 'Los años de experiencia deben estar entre 0 y 60.'
    return ''


def validar_incidencias_vocalia(req: FinalizarPartidoRequest) -> str:
    if req.goles_local < 0 or req.goles_local > 99 or req.goles_visitante < 0 or req.goles_visitante > 99:
        return 'Los goles del equipo deben estar entre 0 y 99.'
    for inc in req.incidencias:
        if inc.goles < 0 or inc.goles > 99:
            return 'Los goles por jugador deben estar entre 0 y 99.'
        if inc.amarillas < 0 or inc.amarillas > 2:
            return 'Las tarjetas amarillas por jugador deben estar entre 0 y 2.'
        if inc.rojas < 0 or inc.rojas > 1:
            return 'Las tarjetas rojas por jugador deben estar entre 0 y 1.'
    return ''


def limpiar_fixture(cursor) -> None:
    cursor.execute('DELETE FROM Calificaciones_Arbitros')
    cursor.execute('DELETE FROM Asistencia')
    cursor.execute('DELETE FROM Estadisticas_Jugadores')
    cursor.execute('DELETE FROM Partidos')

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
    cursor.execute("SELECT Id_Equipo, Nombre_Equipo, Categoria, Url_Logo, Fecha_Fundacion, Presidente FROM Equipos")
    equipos = [{
        "id": r.Id_Equipo,
        "nombre": r.Nombre_Equipo,
        "categoria": r.Categoria,
        "url_logo": r.Url_Logo,
        "fecha_fundacion": r.Fecha_Fundacion.strftime("%Y-%m-%d") if r.Fecha_Fundacion else None,
        "presidente": r.Presidente or ""
    } for r in cursor.fetchall()]
    conn.close()
    return equipos

@app.post("/equipos")
def crear_equipo(equipo: EquipoCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        nombre_normalizado = normalizar_nombre_equipo(equipo.nombre_equipo)
        err_nombre = validar_nombre_equipo(nombre_normalizado)
        if err_nombre:
            raise HTTPException(status_code=400, detail=err_nombre)
        if equipo.categoria not in ('Primera', 'Máxima'):
            raise HTTPException(status_code=400, detail="Por favor selecciona una categoría válida ('Primera' o 'Máxima').")
        validacion_fecha = validar_fecha_fundacion_equipo(equipo.fecha_fundacion)
        if validacion_fecha:
            raise HTTPException(status_code=400, detail=validacion_fecha)
        cursor.execute("SELECT Id_Equipo, Nombre_Equipo FROM Equipos")
        equipos_existentes = cursor.fetchall()
        if any(normalizar_nombre_equipo(r.Nombre_Equipo) == nombre_normalizado for r in equipos_existentes):
            raise HTTPException(status_code=400, detail="¡Atención! Ya existe un equipo registrado con ese nombre.")
        pres_val = equipo.presidente.strip() if equipo.presidente and equipo.presidente.strip() else None
        cursor.execute("INSERT INTO Equipos (Nombre_Equipo, Fecha_Fundacion, Categoria, Url_Logo, Presidente) VALUES (?, ?, ?, ?, ?)", (nombre_normalizado, equipo.fecha_fundacion, equipo.categoria, equipo.url_logo, pres_val))
        conn.commit()
        return {"mensaje": f"Equipo '{nombre_normalizado}' creado exitosamente."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/equipos/{id_equipo}")
def actualizar_equipo(id_equipo: int, equipo: EquipoCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        nombre_normalizado = normalizar_nombre_equipo(equipo.nombre_equipo)
        err_nombre = validar_nombre_equipo(nombre_normalizado)
        if err_nombre:
            raise HTTPException(status_code=400, detail=err_nombre)
        if equipo.categoria not in ('Primera', 'Máxima'):
            raise HTTPException(status_code=400, detail="Por favor selecciona una categoría válida ('Primera' o 'Máxima').")
        validacion_fecha = validar_fecha_fundacion_equipo(equipo.fecha_fundacion)
        if validacion_fecha:
            raise HTTPException(status_code=400, detail=validacion_fecha)
        cursor.execute("SELECT Id_Equipo, Nombre_Equipo FROM Equipos WHERE Id_Equipo <> ?", (id_equipo,))
        equipos_existentes = cursor.fetchall()
        if any(normalizar_nombre_equipo(r.Nombre_Equipo) == nombre_normalizado for r in equipos_existentes):
            raise HTTPException(status_code=400, detail="¡Atención! Ya existe otro equipo registrado con ese nombre.")
        pres_val = equipo.presidente.strip() if equipo.presidente and equipo.presidente.strip() else None
        cursor.execute("UPDATE Equipos SET Nombre_Equipo = ?, Categoria = ?, Fecha_Fundacion = ?, Url_Logo = ?, Presidente = ? WHERE Id_Equipo = ?", (nombre_normalizado, equipo.categoria, equipo.fecha_fundacion, equipo.url_logo, pres_val, id_equipo))
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
                   j.Id_Equipo, e.Nombre_Equipo, j.Url_Documento, e.Categoria, s.Fecha_Fin, s.Motivo
            FROM Jugadores j
            LEFT JOIN Equipos e ON j.Id_Equipo = e.Id_Equipo
            LEFT JOIN Suspensiones_Jugadores s ON j.Id_Jugador = s.Id_Jugador AND s.Activa = 1 AND s.Fecha_Fin >= CAST(GETDATE() AS DATE)
            ORDER BY j.Id_Jugador DESC
        """)
        lista_jugadores = []
        for row in cursor.fetchall():
            lista_jugadores.append({
                "id_jugador": row.Id_Jugador, "cedula": row.Cedula, "nombre": row.Nombre, "apellido": row.Apellido,
                "fecha_nacimiento": row.Fecha_Nacimiento, "numero_camiseta": row.Numero_Camiseta,
                "url_foto": row.Url_Foto, "id_equipo": row.Id_Equipo, "nombre_equipo": row.Nombre_Equipo,
                "categoria_equipo": row.Categoria, "url_documento": row.Url_Documento if hasattr(row, 'Url_Documento') else '',
                "suspendido_hasta": row.Fecha_Fin if hasattr(row, 'Fecha_Fin') else None, "motivo_suspension": row.Motivo if hasattr(row, 'Motivo') else ''
            })
        return lista_jugadores
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/jugadores")
def crear_jugador(jugador: JugadorCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        validacion_fecha = validar_fecha_nacimiento_max_100(jugador.fecha_nacimiento)
        if validacion_fecha:
            raise HTTPException(status_code=400, detail=validacion_fecha)
        validacion_cedula = validar_cedula_ecuatoriana(jugador.cedula)
        if validacion_cedula:
            raise HTTPException(status_code=400, detail=validacion_cedula)
        validacion_camiseta = validar_numero_camiseta(jugador.numero_camiseta)
        if validacion_camiseta:
            raise HTTPException(status_code=400, detail=validacion_camiseta)
        cursor.execute("SELECT 1 FROM Arbitros WHERE Cedula = ?", (jugador.cedula,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="No se puede registrar un jugador con una cédula que ya pertenece a un árbitro.")
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
        if 'UNIQUE KEY constraint' in str(e): raise HTTPException(status_code=400, detail="La cédula ya está registrada en otro jugador.")
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/jugadores/{id_jugador}")
def actualizar_jugador(id_jugador: int, jugador: JugadorCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        validacion_cedula = validar_cedula_ecuatoriana(jugador.cedula)
        if validacion_cedula:
            raise HTTPException(status_code=400, detail=validacion_cedula)
        validacion_camiseta = validar_numero_camiseta(jugador.numero_camiseta)
        if validacion_camiseta:
            raise HTTPException(status_code=400, detail=validacion_camiseta)
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
        cursor.execute("""
            SELECT
              (SELECT COUNT(*) FROM Estadisticas_Jugadores WHERE Id_Jugador = ?) +
              (SELECT COUNT(*) FROM Asistencia WHERE Id_Jugador = ?) +
              (SELECT COUNT(*) FROM Suspensiones_Jugadores WHERE Id_Jugador = ?) +
              (SELECT COUNT(*) FROM Calificaciones_Arbitros WHERE Id_Jugador = ?) +
              (SELECT COUNT(*) FROM Usuarios WHERE Id_Jugador = ?) AS total
        """, (id_jugador, id_jugador, id_jugador, id_jugador, id_jugador))
        if cursor.fetchone().total > 0:
            raise HTTPException(status_code=400, detail="No se puede dar de baja al jugador porque tiene historial asociado (estadísticas, asistencias, suspensiones, calificaciones o una cuenta de usuario vinculada).")
        cursor.execute("DELETE FROM Jugadores WHERE Id_Jugador = ?", (id_jugador,))
        conn.commit()
        return {"mensaje": "El jugador ha sido dado de baja exitosamente."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/arbitros")
def obtener_arbitros():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Arbitro, Nombre, Apellido, Cedula, Experiencia_Anios, Url_Foto FROM Arbitros ORDER BY Id_Arbitro DESC")
        return [{"id_arbitro": r.Id_Arbitro, "nombre": r.Nombre, "apellido": r.Apellido, "cedula": r.Cedula, "experiencia_anios": r.Experiencia_Anios, "url_foto": r.Url_Foto} for r in cursor.fetchall()]
    finally: conn.close()

@app.post("/arbitros")
def crear_arbitro(arbitro: ArbitroCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        validacion_experiencia = validar_experiencia_anios(arbitro.experiencia_anios)
        if validacion_experiencia:
            raise HTTPException(status_code=400, detail=validacion_experiencia)
        cedula = arbitro.cedula.strip() if arbitro.cedula else None
        if cedula:
            validacion_cedula = validar_cedula_ecuatoriana(cedula)
            if validacion_cedula:
                raise HTTPException(status_code=400, detail=validacion_cedula)
            cursor.execute("SELECT Id_Jugador FROM Jugadores WHERE Cedula = ?", (cedula,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="No se puede registrar un árbitro con una cédula que ya pertenece a un jugador.")
            cursor.execute("SELECT Id_Arbitro FROM Arbitros WHERE Cedula = ?", (cedula,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Ya existe un árbitro registrado con esa cédula.")
        cursor.execute("INSERT INTO Arbitros (Nombre, Apellido, Cedula, Experiencia_Anios, Url_Foto) VALUES (?, ?, ?, ?, ?)", (arbitro.nombre, arbitro.apellido, cedula, arbitro.experiencia_anios, arbitro.url_foto))
        conn.commit()
        return {"mensaje": f"Árbitro {arbitro.nombre} registrado exitosamente."}
    except HTTPException: raise
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/partidos/fixture")
def borrar_fixture(req: AdminCredencialesRequest = Body(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        verificar_credenciales_admin(cursor, req.correo, req.password)
        limpiar_fixture(cursor)
        conn.commit()
        return {"mensaje": "Fixture eliminado correctamente."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/partidos")
def obtener_partidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
                 SELECT p.Id_Partido, p.Fecha_Hora, p.Estado, p.Goles_Local, p.Goles_Visitante, p.Id_Arbitro, p.Id_Arbitro_2, p.Id_Arbitro_3,
                     el.Nombre_Equipo AS Local, el.Categoria AS Categoria_Local,
                     ev.Nombre_Equipo AS Visitante, ev.Categoria AS Categoria_Visitante,
                   a1.Nombre AS Arbitro1_Nombre, a1.Apellido AS Arbitro1_Apellido,
                   a2.Nombre AS Arbitro2_Nombre, a2.Apellido AS Arbitro2_Apellido,
                   a3.Nombre AS Arbitro3_Nombre, a3.Apellido AS Arbitro3_Apellido
            FROM Partidos p
            INNER JOIN Equipos el ON p.Id_Equipo_Local = el.Id_Equipo
            INNER JOIN Equipos ev ON p.Id_Equipo_Visitante = ev.Id_Equipo
            LEFT JOIN Arbitros a1 ON p.Id_Arbitro = a1.Id_Arbitro
            LEFT JOIN Arbitros a2 ON p.Id_Arbitro_2 = a2.Id_Arbitro
            LEFT JOIN Arbitros a3 ON p.Id_Arbitro_3 = a3.Id_Arbitro
            ORDER BY p.Fecha_Hora ASC
        """)
        partidos = []
        for r in cursor.fetchall():
            arbitros_partido = [f"{r.Arbitro1_Nombre} {r.Arbitro1_Apellido}" if r.Arbitro1_Nombre else None,
                                f"{r.Arbitro2_Nombre} {r.Arbitro2_Apellido}" if r.Arbitro2_Nombre else None,
                                f"{r.Arbitro3_Nombre} {r.Arbitro3_Apellido}" if r.Arbitro3_Nombre else None]
            arbitro_str = " / ".join([a for a in arbitros_partido if a]) or "Sin asignar"
            partidos.append({
                "id_partido": r.Id_Partido, "local": r.Local, "visitante": r.Visitante,
                "categoria_local": r.Categoria_Local, "categoria_visitante": r.Categoria_Visitante,
                "fecha": r.Fecha_Hora.strftime("%Y-%m-%d") if r.Fecha_Hora else "",
                "hora": r.Fecha_Hora.strftime("%H:%M") if r.Fecha_Hora else "",
                "goles_local": r.Goles_Local if r.Goles_Local is not None else 0,
                "goles_visitante": r.Goles_Visitante if r.Goles_Visitante is not None else 0,
                "estado": r.Estado, "arbitro": arbitro_str, "id_arbitro": r.Id_Arbitro,
                "id_arbitro_2": r.Id_Arbitro_2, "id_arbitro_3": r.Id_Arbitro_3
            })
        return partidos
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/partidos/{id_partido}")
def actualizar_partido(id_partido: int, partido: PartidoActualizar):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        validacion_arbitros = validar_arbitros_distintos(partido)
        if validacion_arbitros:
            raise HTTPException(status_code=400, detail=validacion_arbitros)
        fecha_hora_str = f"{partido.fecha} {partido.hora}"
        fecha_hora_dt = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M")
        cursor.execute("SELECT COUNT(*) as total FROM Partidos WHERE Fecha_Hora = ? AND Id_Partido <> ?", (fecha_hora_dt, id_partido))
        if cursor.fetchone().total > 0: raise HTTPException(status_code=400, detail="¡Conflicto de Horario! Ya existe otro partido programado en esa misma fecha y hora.")
        cursor.execute("UPDATE Partidos SET Fecha_Hora = ?, Id_Arbitro = ?, Id_Arbitro_2 = ?, Id_Arbitro_3 = ? WHERE Id_Partido = ?", (fecha_hora_dt, partido.id_arbitro, partido.id_arbitro_2, partido.id_arbitro_3, id_partido))
        conn.commit()
        return {"mensaje": "El partido ha sido reprogramado con éxito."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

def calcular_si_esta_suspendido(cursor, id_jugador: int, id_equipo: int) -> bool:
    cursor.execute("SELECT TOP 1 1 FROM Suspensiones_Jugadores WHERE Id_Jugador = ? AND Activa = 1 AND Fecha_Fin >= CAST(GETDATE() AS DATE)", (id_jugador,))
    if cursor.fetchone():
        return True
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
        validacion = validar_incidencias_vocalia(req)
        if validacion:
            raise HTTPException(status_code=400, detail=validacion)
        cursor.execute("UPDATE Partidos SET Goles_Local = ?, Goles_Visitante = ?, Estado = 'Finalizado', Novedades = ?, Url_Foto_Vocalia = ? WHERE Id_Partido = ?", (req.goles_local, req.goles_visitante, req.novedades, req.foto_vocalia_url, id_partido))
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
        cursor.execute("SELECT Novedades, Id_Equipo_Local, Id_Equipo_Visitante, Url_Foto_Vocalia FROM Partidos WHERE Id_Partido = ?", (id_partido,))
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
            "foto_vocalia_url": partido.Url_Foto_Vocalia if hasattr(partido, 'Url_Foto_Vocalia') and partido.Url_Foto_Vocalia else None,
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
        validacion_camiseta = validar_numero_camiseta(req.nuevo_numero_camiseta)
        if validacion_camiseta:
            raise HTTPException(status_code=400, detail=validacion_camiseta)
        cursor.execute("SELECT COUNT(*) as total FROM Partidos WHERE Estado <> 'Finalizado'")
        if cursor.fetchone().total > 0:
            raise HTTPException(status_code=400, detail="Los traspasos quedan bloqueados hasta que se jueguen todos los partidos del torneo.")
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
        cursor.execute("SELECT COUNT(*) as total FROM Partidos WHERE Estado <> 'Finalizado'")
        if cursor.fetchone().total > 0:
            raise HTTPException(status_code=400, detail="Los cambios de categoría quedan bloqueados hasta que se completen todos los partidos.")
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
        verificar_credenciales_admin(cursor, req.correo, req.password)
        limpiar_fixture(cursor)
        p_primera = generar_round_robin_por_categoria(cursor, "Primera", req.fecha_inicio)
        p_maxima = generar_round_robin_por_categoria(cursor, "Máxima", req.fecha_inicio + timedelta(days=1))
        todos = p_primera + p_maxima
        if not todos: raise HTTPException(status_code=400, detail="No hay suficientes equipos.")
        cursor.executemany("INSERT INTO Partidos (Id_Equipo_Local, Id_Equipo_Visitante, Fecha_Hora, Estado) VALUES (?, ?, ?, ?)", todos)
        conn.commit()
        return {"mensaje": f"¡Torneo unificado generado! {len(todos)} partidos cargados."}
    finally: conn.close()

@app.get("/jugadores/suspendidos")
def obtener_jugadores_suspendidos():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT j.Id_Jugador, j.Nombre, j.Apellido, j.Cedula, e.Nombre_Equipo, s.Fecha_Inicio, s.Fecha_Fin, s.Motivo
            FROM Suspensiones_Jugadores s
            INNER JOIN Jugadores j ON s.Id_Jugador = j.Id_Jugador
            LEFT JOIN Equipos e ON j.Id_Equipo = e.Id_Equipo
            WHERE s.Activa = 1 AND s.Fecha_Fin >= CAST(GETDATE() AS DATE)
            ORDER BY s.Fecha_Fin DESC
        """)
        return [{"id_jugador": r.Id_Jugador, "nombre": r.Nombre, "apellido": r.Apellido, "cedula": r.Cedula, "equipo": r.Nombre_Equipo, "fecha_inicio": r.Fecha_Inicio, "fecha_fin": r.Fecha_Fin, "motivo": r.Motivo} for r in cursor.fetchall()]
    finally: conn.close()

@app.post("/jugadores/{id_jugador}/suspender")
def suspender_jugador(id_jugador: int, req: SuspensionRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=365)
        cursor.execute("UPDATE Suspensiones_Jugadores SET Activa = 0 WHERE Id_Jugador = ?", (id_jugador,))
        cursor.execute("INSERT INTO Suspensiones_Jugadores (Id_Jugador, Fecha_Inicio, Fecha_Fin, Motivo, Activa) VALUES (?, ?, ?, ?, 1)", (id_jugador, fecha_inicio, fecha_fin, req.motivo))
        conn.commit()
        return {"mensaje": "Jugador suspendido por un año correctamente."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/jugadores/{id_jugador}/suspender")
def quitar_suspension_jugador(id_jugador: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Suspensiones_Jugadores SET Activa = 0 WHERE Id_Jugador = ?", (id_jugador,))
        conn.commit()
        return {"mensaje": "Suspensión removida correctamente."}
    except Exception as e: conn.rollback(); raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/login")
def iniciar_sesion(credenciales: UsuarioLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Usamos COLLATE SQL_Latin1_General_CP1_CS_AS para forzar la validación exacta 
        # de mayúsculas y minúsculas (Case Sensitive) directamente en la base de datos.
        cursor.execute("""
            SELECT Id_Usuario, Correo, Password_Hash, Rol, Id_Jugador 
            FROM Usuarios 
            WHERE Correo COLLATE SQL_Latin1_General_CP1_CS_AS = ?
        """, (credenciales.correo,))
        
        u = cursor.fetchone()

        if not u or not verificar_password(credenciales.password, u.Password_Hash):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        if not es_hash_pbkdf2(u.Password_Hash):
            cursor.execute("UPDATE Usuarios SET Password_Hash = ? WHERE Id_Usuario = ?", (hash_password(credenciales.password), u.Id_Usuario))
            conn.commit()

        return {"usuario": {"id": u.Id_Usuario, "correo": u.Correo, "rol": u.Rol, "id_jugador": u.Id_Jugador if hasattr(u, 'Id_Jugador') else None}}
    finally:
        conn.close()

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
        validacion_cedula = validar_cedula_ecuatoriana(req.cedula)
        if validacion_cedula:
            raise HTTPException(status_code=400, detail=validacion_cedula)

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
        correo_normalizado = normalizar_correo(req.correo)
        cursor.execute("SELECT Id_Usuario FROM Usuarios WHERE LOWER(Correo) = ?", (correo_normalizado,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Este correo electrónico ya está en uso, sin importar mayúsculas o minúsculas.")

        validacion_password = validar_password_segura(req.password)
        if validacion_password:
            raise HTTPException(status_code=400, detail=validacion_password)
            
        # 4. Insertar en la tabla Usuarios vinculándolo con su Id_Jugador
        cursor.execute("""
            INSERT INTO Usuarios (Correo, Password_Hash, Rol, Id_Jugador)
            VALUES (?, ?, 'Jugador', ?)
        """, (correo_normalizado, hash_password(req.password), id_jugador))
        conn.commit()
        
        return {"mensaje": f"¡Bienvenido {jugador.Nombre}! Tu cuenta ha sido creada exitosamente. Ya puedes iniciar sesión."}
        
    except HTTPException: raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()