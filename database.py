import pyodbc

# Reemplaza 'DESKTOP-A9DPDLM\SQLNEY' con el nombre de tu servidor que vimos en SSMS
SERVER = 'DESKTOP-A9DPDLM\SQLNEY' 
DATABASE = 'LigaConocotoDB'

# Cadena de conexión usando Windows Authentication (Trusted_Connection=yes)
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"

def get_db_connection():
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None