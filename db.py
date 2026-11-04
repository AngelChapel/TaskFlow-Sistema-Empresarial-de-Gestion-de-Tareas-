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