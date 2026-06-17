import firebase_admin
from firebase_admin import credentials, storage
import os
from datetime import datetime
import uuid

# Inicializar Firebase
cred_path = os.path.join(os.path.dirname(__file__), 'firebase-key.json')
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'ligadeportivabarrialconocoto.firebasestorage.app'
    })

bucket = storage.bucket()

def upload_image_to_firebase(file_content, filename: str, folder: str = "images") -> str:
    """
    Sube una imagen a Firebase Storage y retorna su URL pública.
    
    Args:
        file_content: Contenido del archivo (bytes)
        filename: Nombre original del archivo
        folder: Carpeta donde guardar (default: "images")
    
    Returns:
        str: URL pública del archivo en Firebase Storage
    """
    try:
        # Generar nombre único para evitar conflictos
        file_extension = filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"{folder}/{datetime.now().strftime('%Y/%m/%d')}/{unique_filename}"
        
        # Crear referencia al archivo
        blob = bucket.blob(file_path)
        
        # Determinar tipo MIME basado en extensión
        mime_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf'
        }
        mime_type = mime_type_map.get(file_extension.lower(), 'application/octet-stream')
        
        # Subir el archivo
        blob.upload_from_string(file_content, content_type=mime_type)
        
        # Hacer el archivo público (opcional, depende de tu configuración)
        blob.make_public()
        
        # Retornar la URL pública
        return blob.public_url
    
    except Exception as e:
        raise Exception(f"Error al subir imagen a Firebase: {str(e)}")


def delete_image_from_firebase(file_url: str) -> bool:
    """
    Elimina una imagen de Firebase Storage.
    
    Args:
        file_url: URL pública del archivo
    
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        # Extraer el path del archivo de la URL
        # Format: https://storage.googleapis.com/bucket/path/to/file
        file_path = file_url.split(f"{bucket.name}/")[-1]
        blob = bucket.blob(file_path)
        blob.delete()
        return True
    except Exception as e:
        raise Exception(f"Error al eliminar imagen de Firebase: {str(e)}")
