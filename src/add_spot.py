from dotenv import load_dotenv
from db_utils import get_db_connection

load_dotenv()

def adicionar_praia_ao_db(name, latitude, longitude):
    """
    Add a new beach (spot) to the database.
    If the beach already exists, it will not be added again."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Verifica se a praia já existe
        cur.execute("SELECT spot_id FROM spots WHERE spot_name = %s", (name,))
        if cur.fetchone():
            print(f"Spot '{name}' already exists in the database.")
            return

        cur.execute(
            """
            INSERT INTO spots (spot_name, latitude, longitude)
            VALUES (%s, %s, %s)
            RETURNING spot_id;
            """,
            (name, latitude, longitude)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"Spot '{name}' (ID: {new_id}, Lat: {latitude}, Lng: {longitude}) addition completed!")

    except Exception as e:
        print(f"Error while adding '{name}': {e}")
        if conn:
            conn.rollback()
            print("Transaction rolled back due to error.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("--- Adding a new spot ---")
    
    while True:
        nome = input("Insert spot name (or 'q' to quit): ").strip()
        if nome.lower() == 'q':
            break

        try:
            latitude = float(input(f"Insert latitude to '{nome}': "))
            longitude = float(input(f"Insert longitude to '{nome}': "))
            
            adicionar_praia_ao_db(nome, latitude, longitude)
            print("-" * 30)
        except ValueError:
            print("Invalid input for latitude or longitude. Please enter numeric values.")
        except Exception as e:
            print(f"Error: {e}")

    print("\n--- Spot addition process completed ---")