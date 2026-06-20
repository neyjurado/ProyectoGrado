from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from datetime import date
from typing import Optional
from database import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from firebase_service import upload_image_to_firebase

app = FastAPI(
    title="API Liga Conocoto",
    description="Backend para la gestión deportiva de la LDP Conocoto"
)

# ---------------------------------------------------------
# CONFIGURACIÓN DE CORS
# ---------------------------------------------------------
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

class CalificacionArbitro(BaseModel):
    id_arbitro: int
    id_jugador: int
    id_partido: int
    puntaje: int

class UsuarioLogin(BaseModel):
    correo: str
    password: str

# ---------------------------------------------------------
# 2. RUTAS DE LA API (ENDPOINTS)
# ---------------------------------------------------------

@app.get("/")
def ruta_raiz():
    return {"mensaje": "¡Bienvenido al servidor de la Liga Conocoto!"}

# ==========================================
# RUTAS PARA EQUIPOS
# ==========================================
@app.get("/equipos")
def obtener_equipos():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de BD")
    
    cursor = conn.cursor()
    cursor.execute("SELECT Id_Equipo, Nombre_Equipo, Categoria, Url_Logo FROM Equipos")
    
    equipos = []
    for row in cursor.fetchall():
        equipos.append({
            "id": row.Id_Equipo, "nombre": row.Nombre_Equipo,
            "categoria": row.Categoria, "url_logo": row.Url_Logo
        })
    conn.close()
    return equipos

@app.post("/equipos")
def crear_equipo(equipo: EquipoCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Equipos (Nombre_Equipo, Fecha_Fundacion, Categoria, Url_Logo)
            VALUES (?, ?, ?, ?)
        """, (equipo.nombre_equipo, equipo.fecha_fundacion, equipo.categoria, equipo.url_logo))
        conn.commit()
        return {"mensaje": f"Equipo '{equipo.nombre_equipo}' creado exitosamente."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# NUEVA RUTA: EDITAR EQUIPO
@app.put("/equipos/{id_equipo}")
def actualizar_equipo(id_equipo: int, equipo: EquipoCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Equipos 
            SET Nombre_Equipo = ?, Categoria = ?, Fecha_Fundacion = ?, Url_Logo = ?
            WHERE Id_Equipo = ?
        """, (equipo.nombre_equipo, equipo.categoria, equipo.fecha_fundacion, equipo.url_logo, id_equipo))
        conn.commit()
        return {"mensaje": "Equipo actualizado correctamente."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# NUEVA RUTA: ELIMINAR EQUIPO (Administrador)
@app.delete("/equipos/{id_equipo}")
def eliminar_equipo(id_equipo: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
        
    cursor = conn.cursor()
    try:
        # VALIDACIÓN VITAL: Impedir eliminar si hay jugadores huérfanos
        cursor.execute("SELECT COUNT(*) as total FROM Jugadores WHERE Id_Equipo = ?", (id_equipo,))
        total_jugadores = cursor.fetchone().total
        if total_jugadores > 0:
            raise HTTPException(
                status_code=400, 
                detail="No se puede eliminar el equipo porque tiene jugadores inscritos. Retíralos primero."
            )
            
        cursor.execute("DELETE FROM Equipos WHERE Id_Equipo = ?", (id_equipo,))
        conn.commit()
        return {"mensaje": "El equipo ha sido dado de baja exitosamente."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==========================================
# RUTAS PARA JUGADORES
# ==========================================
@app.get("/jugadores")
def obtener_jugadores():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                j.Id_Jugador, j.Cedula, j.Nombre, j.Apellido, 
                j.Fecha_Nacimiento, j.Numero_Camiseta, j.Url_Foto, 
                j.Id_Equipo, e.Nombre_Equipo, j.Url_Documento
            FROM Jugadores j
            LEFT JOIN Equipos e ON j.Id_Equipo = e.Id_Equipo
            ORDER BY j.Id_Jugador DESC
        """)
        lista_jugadores = []
        for row in cursor.fetchall():
            lista_jugadores.append({
                "id_jugador": row.Id_Jugador, "cedula": row.Cedula,
                "nombre": row.Nombre, "apellido": row.Apellido,
                "fecha_nacimiento": row.Fecha_Nacimiento, "numero_camiseta": row.Numero_Camiseta,
                "url_foto": row.Url_Foto, "id_equipo": row.Id_Equipo,
                "nombre_equipo": row.Nombre_Equipo, "url_documento": getattr(row, 'Url_Documento', '')
            })
        return lista_jugadores
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/jugadores")
def crear_jugador(jugador: JugadorCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Jugador FROM Jugadores WHERE Id_Equipo = ? AND Numero_Camiseta = ?", 
                       (jugador.id_equipo, jugador.numero_camiseta))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"¡Error! La camiseta #{jugador.numero_camiseta} ya está asignada a otro jugador.")

        cursor.execute("""
            INSERT INTO Jugadores (Cedula, Nombre, Apellido, Fecha_Nacimiento, Id_Equipo, Url_Foto, Numero_Camiseta, Url_Documento, Acepta_Terminos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (jugador.cedula, jugador.nombre, jugador.apellido, jugador.fecha_nacimiento, 
              jugador.id_equipo, jugador.url_foto, jugador.numero_camiseta, 
              jugador.url_documento, jugador.acepta_terminos))
        conn.commit()
        return {"mensaje": f"Jugador {jugador.nombre} {jugador.apellido} registrado exitosamente."}
    except HTTPException:
        raise 
    except Exception as e:
        conn.rollback()
        if 'UNIQUE KEY constraint' in str(e):
            raise HTTPException(status_code=400, detail="Este documento ya está registrado.")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# NUEVA RUTA: EDITAR JUGADOR
@app.put("/jugadores/{id_jugador}")
def actualizar_jugador(id_jugador: int, jugador: JugadorCrear):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Validamos que la camiseta no la tenga OTRO jugador del mismo equipo
        cursor.execute("SELECT Id_Jugador FROM Jugadores WHERE Id_Equipo = ? AND Numero_Camiseta = ? AND Id_Jugador <> ?", 
                       (jugador.id_equipo, jugador.numero_camiseta, id_jugador))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"¡Error! La camiseta #{jugador.numero_camiseta} ya está ocupada.")

        cursor.execute("""
            UPDATE Jugadores 
            SET Cedula = ?, Nombre = ?, Apellido = ?, Fecha_Nacimiento = ?, Id_Equipo = ?, Url_Foto = ?, Numero_Camiseta = ?, Url_Documento = ?, Acepta_Terminos = ?
            WHERE Id_Jugador = ?
        """, (jugador.cedula, jugador.nombre, jugador.apellido, jugador.fecha_nacimiento, 
              jugador.id_equipo, jugador.url_foto, jugador.numero_camiseta, 
              jugador.url_documento, jugador.acepta_terminos, id_jugador))
        conn.commit()
        return {"mensaje": "Jugador actualizado con éxito."}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# NUEVA RUTA: ELIMINAR (DAR DE BAJA) JUGADOR
@app.delete("/jugadores/{id_jugador}")
def eliminar_jugador(id_jugador: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Jugadores WHERE Id_Jugador = ?", (id_jugador,))
        conn.commit()
        return {"mensaje": "El jugador ha sido dado de baja exitosamente."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==========================================
# RUTAS DE PARTIDOS Y ESTADÍSTICAS
# ==========================================
@app.get("/goleadores/{categoria}")
def obtener_goleadores(categoria: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TOP 10 j.Nombre, j.Apellido, e.Nombre_Equipo, SUM(est.Goles) as Total_Goles
            FROM Jugadores j INNER JOIN Equipos e ON j.Id_Equipo = e.Id_Equipo
            INNER JOIN Estadisticas_Jugadores est ON j.Id_Jugador = est.Id_Jugador
            WHERE e.Categoria = ? GROUP BY j.Nombre, j.Apellido, e.Nombre_Equipo ORDER BY Total_Goles DESC
        """, (categoria,))
        goleadores = [{"jugador": f"{r.Nombre} {r.Apellido}", "equipo": r.Nombre_Equipo, "goles": r.Total_Goles} for r in cursor.fetchall()]
        return goleadores
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/calificar-arbitro")
def registrar_calificacion(calificacion: CalificacionArbitro):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Calificaciones_Arbitros (Id_Arbitro, Id_Jugador, Id_Partido, Puntaje) VALUES (?, ?, ?, ?)", 
                       (calificacion.id_arbitro, calificacion.id_jugador, calificacion.id_partido, calificacion.puntaje))
        conn.commit()
        return {"mensaje": "¡Calificación registrada exitosamente!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==========================================
# AUTENTICACIÓN Y ARCHIVOS
# ==========================================
@app.post("/login")
def iniciar_sesion(credenciales: UsuarioLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id_Usuario, Correo, Password_Hash, Rol FROM Usuarios WHERE Correo = ?", (credenciales.correo,))
        usuario = cursor.fetchone()
        if not usuario or credenciales.password != usuario.Password_Hash:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        return {"mensaje": "Login exitoso", "usuario": {"id": usuario.Id_Usuario, "correo": usuario.Correo, "rol": usuario.Rol}}
    except HTTPException:
        raise
    finally:
        conn.close()

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), folder: Optional[str] = Form("images")):
    try:
        file_content = await file.read()
        image_url = upload_image_to_firebase(file_content, file.filename, folder)
        return {"mensaje": "Imagen subida", "url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))