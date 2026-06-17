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
# CONFIGURACIÓN DE CORS (Permisos para la página web)
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
    numero_camiseta: int  # <-- Campo para el dorsal del jugador

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
    return {"mensaje": "¡Bienvenido al servidor de la Liga Conocoto! Ve a /docs para ver la API."}

# RUTA: Obtener todos los equipos (Visitante) - ACTUALIZADA PARA INCLUIR LOGO
@app.get("/equipos")
def obtener_equipos():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    cursor = conn.cursor()
    # AGREGADO: Url_Logo en la consulta SQL
    cursor.execute("SELECT Id_Equipo, Nombre_Equipo, Categoria, Url_Logo FROM Equipos")
    
    equipos = []
    for row in cursor.fetchall():
        equipos.append({
            "id": row.Id_Equipo,
            "nombre": row.Nombre_Equipo,
            "categoria": row.Categoria,
            "url_logo": row.Url_Logo  # <-- Enviamos la URL al Frontend
        })
        
    conn.close()
    return equipos

# RUTA: Registrar un nuevo equipo (Administrador)
@app.post("/equipos")
def crear_equipo(equipo: EquipoCrear):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
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
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
    finally:
        conn.close()

# RUTA: Obtener los goleadores por categoría (Visitante)
@app.get("/goleadores/{categoria}")
def obtener_goleadores(categoria: str):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    cursor = conn.cursor()
    try:
        consulta_sql = """
            SELECT TOP 10 
                j.Nombre, 
                j.Apellido, 
                e.Nombre_Equipo, 
                SUM(est.Goles) as Total_Goles
            FROM Jugadores j
            INNER JOIN Equipos e ON j.Id_Equipo = e.Id_Equipo
            INNER JOIN Estadisticas_Jugadores est ON j.Id_Jugador = est.Id_Jugador
            WHERE e.Categoria = ?
            GROUP BY j.Nombre, j.Apellido, e.Nombre_Equipo
            ORDER BY Total_Goles DESC
        """
        cursor.execute(consulta_sql, (categoria,))
        
        goleadores = []
        for row in cursor.fetchall():
            goleadores.append({
                "jugador": f"{row.Nombre} {row.Apellido}",
                "equipo": row.Nombre_Equipo,
                "goles": row.Total_Goles
            })
            
        return goleadores
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar estadísticas: {str(e)}")
    finally:
        conn.close()

# RUTA: Registrar un nuevo jugador (Administrador)
@app.post("/jugadores")
def crear_jugador(jugador: JugadorCrear):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Jugadores (Cedula, Nombre, Apellido, Fecha_Nacimiento, Id_Equipo, Url_Foto, Numero_Camiseta)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (jugador.cedula, jugador.nombre, jugador.apellido, jugador.fecha_nacimiento, jugador.id_equipo, jugador.url_foto, jugador.numero_camiseta))
        
        conn.commit()
        return {"mensaje": f"Jugador {jugador.nombre} {jugador.apellido} registrado exitosamente."}
        
    except Exception as e:
        conn.rollback()
        if 'Violation of UNIQUE KEY constraint' in str(e):
            raise HTTPException(status_code=400, detail="Esta cédula ya está registrada en la liga.")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
    finally:
        conn.close()

# RUTA: Calificar a un árbitro (Jugador)
@app.post("/calificar-arbitro")
def registrar_calificacion(calificacion: CalificacionArbitro):
    if calificacion.puntaje < 0 or calificacion.puntaje > 5:
        raise HTTPException(status_code=400, detail="El puntaje debe ser entre 0 y 5 estrellas.")

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Calificaciones_Arbitros (Id_Arbitro, Id_Jugador, Id_Partido, Puntaje)
            VALUES (?, ?, ?, ?)
        """, (calificacion.id_arbitro, calificacion.id_jugador, calificacion.id_partido, calificacion.puntaje))
        
        conn.commit()
        return {"mensaje": "¡Calificación registrada exitosamente!"}
        
    except Exception as e:
        conn.rollback()
        if 'UQ_Calificacion_Por_Partido' in str(e):
            raise HTTPException(status_code=400, detail="Ya has calificado a este árbitro en este partido.")
        
        if 'The INSERT statement conflicted with the FOREIGN KEY constraint' in str(e):
            raise HTTPException(status_code=400, detail="Los datos de partido, jugador o árbitro no existen en la base de datos.")
            
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
    finally:
        conn.close()

# RUTA: Autenticación de Usuarios (Login)
@app.post("/login")
def iniciar_sesion(credenciales: UsuarioLogin):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT Id_Usuario, Correo, Password_Hash, Rol 
            FROM Usuarios 
            WHERE Correo = ?
        """, (credenciales.correo,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
            
        if credenciales.password != usuario.Password_Hash:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
            
        return {
            "mensaje": "Login exitoso",
            "usuario": {
                "id": usuario.Id_Usuario,
                "correo": usuario.Correo,
                "rol": usuario.Rol
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        conn.close()

# ---------------------------------------------------------
# 3. RUTAS PARA FIREBASE STORAGE (Subida de imágenes)
# ---------------------------------------------------------

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), folder: Optional[str] = Form("images")):
    """
    Endpoint para subir imágenes a Firebase Storage.
    
    Parámetros:
        - file: Archivo de imagen (JPG, PNG, GIF, WebP)
        - folder: Carpeta donde guardar (default: "images")
    
    Retorna:
        - URL pública del archivo en Firebase
    """
    try:
        # Validar que sea una imagen
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de archivo no permitido. Usa: {', '.join(allowed_extensions)}"
            )
        
        # Leer el contenido del archivo
        file_content = await file.read()
        
        # Validar tamaño (máximo 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400, 
                detail="El archivo es demasiado grande. Máximo: 5MB"
            )
        
        # Subir a Firebase
        image_url = upload_image_to_firebase(
            file_content, 
            file.filename, 
            folder
        )
        
        return {
            "mensaje": "Imagen subida exitosamente",
            "url": image_url,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al subir imagen: {str(e)}"
        )

@app.post("/upload-player-photo")
async def upload_player_photo(
    file: UploadFile = File(...),
    player_id: Optional[int] = Form(None)
):
    """
    Endpoint especializado para subir fotos de jugadores.
    Automáticamente actualiza la URL en la base de datos.
    """
    try:
        # Validar imagen
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
        
        # Leer archivo
        file_content = await file.read()
        max_size = 5 * 1024 * 1024
        
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="Archivo demasiado grande (máximo 5MB)")
        
        # Subir a Firebase
        image_url = upload_image_to_firebase(
            file_content,
            file.filename,
            "jugadores"
        )
        
        # Actualizar URL en la base de datos si se proporciona player_id
        if player_id:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "UPDATE Jugadores SET Url_Foto = ? WHERE Id_Jugador = ?",
                        (image_url, player_id)
                    )
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise HTTPException(status_code=500, detail=f"Error al actualizar BD: {str(e)}")
                finally:
                    conn.close()
        
        return {
            "mensaje": "Foto de jugador subida exitosamente",
            "url": image_url,
            "player_id": player_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/upload-team-logo")
async def upload_team_logo(
    file: UploadFile = File(...),
    team_id: Optional[int] = Form(None)
):
    """
    Endpoint especializado para subir logos de equipos.
    Automáticamente actualiza la URL en la base de datos.
    """
    try:
        # Validar imagen
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
        
        # Leer archivo
        file_content = await file.read()
        max_size = 5 * 1024 * 1024
        
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="Archivo demasiado grande (máximo 5MB)")
        
        # Subir a Firebase
        image_url = upload_image_to_firebase(
            file_content,
            file.filename,
            "equipos"
        )
        
        # Actualizar URL en la base de datos si se proporciona team_id
        if team_id:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "UPDATE Equipos SET Url_Logo = ? WHERE Id_Equipo = ?",
                        (image_url, team_id)
                    )
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise HTTPException(status_code=500, detail=f"Error al actualizar BD: {str(e)}")
                finally:
                    conn.close()
        
        return {
            "mensaje": "Logo de equipo subido exitosamente",
            "url": image_url,
            "team_id": team_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")