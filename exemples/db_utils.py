import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Credenciais do banco de dados (certifique-se de que estão no seu .env)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    """
    Estabelece e retorna uma conexão com o banco de dados PostgreSQL.
    Retorna None em caso de falha.
    """
    try:
        connection = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME
        )
        print("Conexão com o banco de dados Supabase estabelecida com sucesso!")
        return connection
    except Exception as e:
        print(f"Falha ao conectar ao banco de dados Supabase: {e}")
        return None

def close_db_connection(connection, cursor):
    """
    Fecha o cursor e a conexão com o banco de dados.
    """
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    print("Conexão com o banco de dados fechada.")