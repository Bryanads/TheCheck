import psycopg2
from psycopg2 import pool
import os
from src.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Pool de conexões global
db_pool = None

def init_db_pool(minconn=1, maxconn=10):
    """
    Inicializa o pool de conexões global.
    Chame esta função uma vez no início da aplicação.
    """
    global db_pool
    if db_pool is None:
        try:
            db_pool = pool.SimpleConnectionPool(
                minconn,
                maxconn,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME
            )
            print("Pool de conexões com o banco de dados inicializado com sucesso!")
        except Exception as e:
            print(f"Falha ao inicializar o pool de conexões: {e}")
            db_pool = None


def get_db_connection():
    """
    Obtém uma conexão do pool de conexões.
    """
    global db_pool
    if db_pool is None:
        print("Pool de conexões não inicializado. Chame init_db_pool() antes de usar.")
        return None
    try:
        conn = db_pool.getconn()
        # print("Conexão obtida do pool.")
        return conn
    except Exception as e:
        print(f"Falha ao obter conexão do pool: {e}")
        return None

def close_db_connection(connection, cursor):
    """
    Fecha o cursor e devolve a conexão ao pool.
    """
    global db_pool
    if cursor:
        cursor.close()
    if connection and db_pool:
        db_pool.putconn(connection)
        # print("Conexão devolvida ao pool.")
    # print("Cursor fechado e conexão devolvida ao pool.")