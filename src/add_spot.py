from src.db.queries import add_spot_to_db

if __name__ == "__main__":
    print("--- Adding a new spot ---")

    while True:
        nome = input("Insert spot name (or 'q' to quit): ").strip()
        if nome.lower() == 'q':
            break

        try:
            latitude = float(input(f"Insert latitude to '{nome}': "))
            longitude = float(input(f"Insert longitude to '{nome}': "))

            add_spot_to_db(nome, latitude, longitude) # Chama a função do novo módulo
            print("-" * 30)
        except ValueError:
            print("Invalid input for latitude or longitude. Please enter numeric values.")
        except Exception as e:
            print(f"Error: {e}")

    print("\n--- Spot addition process completed ---")