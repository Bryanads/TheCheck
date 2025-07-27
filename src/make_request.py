import arrow
import requests
import json
import os
from dotenv import load_dotenv

from db_utils import get_db_connection, close_db_connection

load_dotenv()

API_KEY = os.getenv('API_KEY')

PARAMS = [
    'waveHeight', 'waveDirection', 'wavePeriod', 'swellHeight', 'swellDirection',
    'swellPeriod', 'secondarySwellHeight', 'secondarySwellDirection',
    'secondarySwellPeriod', 'windSpeed', 'windDirection', 'waterTemperature',
    'airTemperature', 'currentSpeed', 'currentDirection'
]

HORARIOS = list(range(5, 18))  # Das 05h às 17h
DIAS = 5  # Previsão para 5 dias

CONFIG_PATH = 'configs/locs.json'

def carregar_coordenadas():
    """Carrega as coordenadas das praias do arquivo de configuração."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo de configuração '{CONFIG_PATH}' não encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"Erro: Arquivo '{CONFIG_PATH}' inválido. Verifique a sintaxe JSON.")
        return None

def selecionar_praia(coordenadas):
    """Permite ao usuário selecionar uma praia da lista carregada."""
    print("\nEscolha uma das praias disponíveis:")
    for i, praia in enumerate(coordenadas):
        print(f"{i + 1}. {praia['nome']}")
    while True:
        try:
            escolha = int(input("Digite o número da praia: ")) - 1
            if 0 <= escolha < len(coordenadas):
                return coordenadas[escolha]['nome'], coordenadas[escolha]
            else:
                print("Escolha inválida. Tente novamente.")
        except ValueError:
            print("Entrada inválida. Por favor, digite um número.")

def get_praia_id(cursor, nome_praia, latitude, longitude):
    """
    Busca o id_praia no banco de dados. Se a praia não existir, insere ela
    na tabela praias e retorna o novo ID.
    """
    cursor.execute("SELECT id_praia FROM praias WHERE nome_praia = %s;", (nome_praia,))
    result = cursor.fetchone()
    if result:
        print(f"Praia '{nome_praia}' encontrada no BD com ID: {result[0]}")
        return result[0]
    else:
        print(f"Praia '{nome_praia}' não encontrada na tabela 'praias'. Inserindo nova praia...")
        try:
            # Inserindo com valores padrão/nulos para os campos que não temos no config/locs.json
            # Ajuste os 'None' se você tiver outros valores padrão ou quiser buscá-los de outro lugar.
            cursor.execute(
                """
                INSERT INTO praias (nome_praia, latitude, longitude, tipo_fundo, orientacao_costa, descricao, caracteristicas_gerais)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id_praia;
                """,
                (nome_praia, latitude, longitude, None, None, None, None)
            )
            new_id = cursor.fetchone()[0]
            print(f"Praia '{nome_praia}' inserida com sucesso com ID: {new_id}")
            return new_id
        except Exception as e:
            print(f"Erro ao inserir praia '{nome_praia}': {e}")
            raise # Re-levanta o erro para que a conexão seja fechada no bloco principal

def make_request(nome_praia, coordenadas_praia, db_connection, cursor):
    lat = coordenadas_praia['lat']
    lon = coordenadas_praia['lng']

    # --- Obter ou criar id_praia ---
    try:
        id_praia = get_praia_id(cursor, nome_praia, lat, lon)
        if id_praia is None:
            print(f"Não foi possível obter um ID válido para a praia '{nome_praia}'. Abortando inserção de previsão.")
            return
    except Exception as e:
        print(f"Erro crítico ao obter/criar ID da praia: {e}")
        return

    start = arrow.utcnow().floor('day')
    end = start.shift(days=DIAS).ceil('day')

    # DUMMY DADOS DE MARÉ - ATENÇÃO: ISTO DEVE VIR DE UMA REQUISIÇÃO REAL À API DA STORMGLASS NO FUTURO
    dados_mares = {
        (start.shift(days=i).format('YYYY-MM-DD')): [
            {"time": (start.shift(days=i).replace(hour=3)).format('YYYY-MM-DDTHH:mm:ssZ'), "type": "low", "height": 0.3},
            {"time": (start.shift(days=i).replace(hour=9)).format('YYYY-MM-DDTHH:mm:ssZ'), "type": "high", "height": 1.5},
            {"time": (start.shift(days=i).replace(hour=15)).format('YYYY-MM-DDTHH:mm:ssZ'), "type": "low", "height": 0.2},
            {"time": (start.shift(days=i).replace(hour=21)).format('YYYY-MM-DDTHH:mm:ssZ'), "type": "high", "height": 1.6}
        ] for i in range(DIAS + 1)
    }

    url = "https://api.stormglass.io/v2/weather/point"
    headers = {'Authorization': API_KEY}
    params = {
        'lat': lat,
        'lng': lon,
        'params': ','.join(PARAMS),
        'start': int(start.timestamp()),
        'end': int(end.timestamp())
    }

    print(f"\nFazendo requisição à StormGlass para {nome_praia}...")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        horas = data.get('hours', [])
        if not horas:
            print("Nenhum dado de previsão encontrado na resposta da API.")
            return

        print("Dados de previsão recebidos. Iniciando inserção/atualização no banco de dados...")

        # --- Inserir/Atualizar em previsoes_horarias ---
        for hora in horas:
            timestamp_utc = arrow.get(hora["time"]).datetime # Objeto datetime para o banco de dados
            
            # Mapeamento e coleta dos valores da API StormGlass
            values_to_insert = (
                id_praia,
                timestamp_utc,
                hora.get('waveHeight', {}).get('sg'),
                hora.get('waveDirection', {}).get('sg'),
                hora.get('wavePeriod', {}).get('sg'),
                hora.get('swellHeight', {}).get('sg'),
                hora.get('swellDirection', {}).get('sg'),
                hora.get('swellPeriod', {}).get('sg'),
                hora.get('secondarySwellHeight', {}).get('sg'),
                hora.get('secondarySwellDirection', {}).get('sg'),
                hora.get('secondarySwellPeriod', {}).get('sg'),
                hora.get('windSpeed', {}).get('sg'),
                hora.get('windDirection', {}).get('sg'),
                hora.get('waterTemperature', {}).get('sg'),
                hora.get('airTemperature', {}).get('sg'),
                hora.get('currentSpeed', {}).get('sg'),
                hora.get('currentDirection', {}).get('sg')
            )

            columns_names = """
                id_praia, timestamp_utc, wave_height_sg, wave_direction_sg, wave_period_sg,
                swell_height_sg, swell_direction_sg, swell_period_sg, secondary_swell_height_sg,
                secondary_swell_direction_sg, secondary_swell_period_sg, wind_speed_sg,
                wind_direction_sg, water_temperature_sg, air_temperature_sg, current_speed_sg,
                current_direction_sg
            """
            
            update_columns = [
                "wave_height_sg", "wave_direction_sg", "wave_period_sg",
                "swell_height_sg", "swell_direction_sg", "swell_period_sg",
                "secondary_swell_height_sg", "secondary_swell_direction_sg",
                "secondary_swell_period_sg", "wind_speed_sg", "wind_direction_sg",
                "water_temperature_sg", "air_temperature_sg", "current_speed_sg",
                "current_direction_sg"
            ]
            update_set_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])


            insert_query_previsoes = f"""
            INSERT INTO previsoes_horarias ({columns_names})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_praia, timestamp_utc) DO UPDATE SET
                {update_set_clause},
                data_coleta = NOW();
            """
            
            try:
                cursor.execute(insert_query_previsoes, values_to_insert)
            except Exception as e:
                print(f"Erro ao inserir/atualizar previsão horária para {timestamp_utc} na praia {nome_praia}: {e}")


        # --- Inserir/Atualizar em mares ---
        for data_str, tides_for_day in dados_mares.items():
            for tide in tides_for_day:
                tide_timestamp_utc = arrow.get(tide["time"]).datetime
                tide_type = tide["type"]
                tide_height = tide["height"]

                tide_insert_query = """
                INSERT INTO mares (id_praia, timestamp_utc, tipo, altura)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id_praia, timestamp_utc) DO UPDATE SET
                    tipo = EXCLUDED.tipo,
                    altura = EXCLUDED.altura,
                    data_coleta = NOW();
                """
                try:
                    cursor.execute(tide_insert_query, (id_praia, tide_timestamp_utc, tide_type, tide_height))
                except Exception as e:
                    print(f"Erro ao inserir/atualizar dado de maré para {tide_timestamp_utc} na praia {nome_praia}: {e}")

        # --- Commit da transação ---
        db_connection.commit()
        print(f"Dados de previsão e maré para {nome_praia} inseridos/atualizados com sucesso no banco de dados!")

    else:
        print(f"Erro na requisição StormGlass: {response.status_code} - {response.text}")


if __name__ == "__main__":
    coordenadas = carregar_coordenadas()
    if not coordenadas:
        print("Erro ao carregar coordenadas. Saindo.")
    else:
        nome_praia_selecionada, coordenadas_selecionadas = selecionar_praia(coordenadas)

        conn = get_db_connection() # Obtém a conexão do db_utils
        if conn:
            cur = None
            try:
                cur = conn.cursor()
                make_request(nome_praia_selecionada, coordenadas_selecionadas, conn, cur)
            except Exception as e:
                print(f"Ocorreu um erro durante a operação principal: {e}")
            finally:
                close_db_connection(conn, cur) # Fecha a conexão e o cursor usando db_utils
        else:
            print("Não foi possível estabelecer a conexão com o banco de dados. Saindo.")