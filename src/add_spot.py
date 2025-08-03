from src.db.queries import add_spot_to_db

if __name__ == "__main__":
    print("--- Adicionando um novo spot ---")

    while True:
        nome = input("Insira o nome do spot (ou 'q' para sair): ")
        if nome.lower() == 'q':
            break

        try:
            latitude = float(input(f"Insira a latitude para '{nome}': "))
            longitude = float(input(f"Insira a longitude para '{nome}': "))
            timezone = input(f"Insira o fuso horário (ex: America/Sao_Paulo) para '{nome}': ")

            new_spot_id = add_spot_to_db(nome, latitude, longitude, timezone)
            if new_spot_id:
                print(f"Spot '{nome}' adicionado com sucesso com ID: {new_spot_id}")
            else:
                print(f"Falha ao adicionar o spot '{nome}' (pode já existir ou houve um erro).")
        except ValueError:
            print("Entrada inválida. Por favor, insira números para latitude e longitude.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")