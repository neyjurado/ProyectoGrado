from database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM sys.tables WHERE name = 'Suspensiones_Jugadores'")
if cur.fetchone()[0] == 0:
    cur.execute("""
        CREATE TABLE Suspensiones_Jugadores (
            Id_Suspension INT IDENTITY(1,1) PRIMARY KEY,
            Id_Jugador INT NOT NULL,
            Fecha_Inicio DATE NOT NULL,
            Fecha_Fin DATE NOT NULL,
            Motivo NVARCHAR(255) NULL,
            Activa BIT NOT NULL DEFAULT 1
        )
    """)

for table, column, definition in [
    ('Arbitros', 'Cedula', 'NVARCHAR(20) NULL'),
    ('Partidos', 'Id_Arbitro_2', 'INT NULL'),
    ('Partidos', 'Id_Arbitro_3', 'INT NULL'),
    ('Partidos', 'Url_Foto_Vocalia', 'NVARCHAR(500) NULL'),
    ('Equipos', 'Presidente', 'NVARCHAR(150) NULL'),
]:
    cur.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' AND COLUMN_NAME = '{column}'")
    if cur.fetchone()[0] == 0:
        cur.execute(f"ALTER TABLE {table} ADD {column} {definition}")

conn.commit()
conn.close()
print('schema ready')
