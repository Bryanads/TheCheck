import arrow
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')

PARAMS = [
    'waveHeight',
    'waveDirection',
    'wavePeriod',
    'swellHeight',
    'swellDirection',
    'swellPeriod',
    'secondarySwellHeight',
    'secondarySwellDirection',
    'secondarySwellPeriod',
    'windSpeed',
    'windDirection',
    'waterTemperature',
    'airTemperature',
    'currentSpeed',
    'currentDirection'
]

HORARIOS = list(range(5, 18))  # Das 05h às 17h
DIAS = 5  # Previsão para 5 dias

CONFIG_PATH = 'configs/locs.json'
OUTPUT_PATH = 'data/previsoes.json'

def carregar_coordenadas():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def selecionar_praia(coordenadas):
    print("Escolha uma das praias disponíveis:")
    for i, praia in enumerate(coordenadas):
        print(f"{i + 1}. {praia['nome']}")
    while True:
        try:
            escolha = int(input("Número da praia: ")) - 1
            if 0 <= escolha < len(coordenadas):
                return coordenadas[escolha]['nome'], coordenadas[escolha]
            else:
                print("Escolha inválida. Tente novamente.")
        except ValueError:
            print("Entrada inválida. Digite um número.")

def get_mares(lat, lng, start, end):
    url = "https://api.stormglass.io/v2/tide/extremes/point"
    headers = {
        'Authorization': API_KEY
    }
    params = {
        'lat': lat,
        'lng': lng,
        'start': int(start.timestamp()),
        'end': int(end.timestamp())
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"[ERRO MARE] {response.status_code}: {response.text}")
        return {}

    dados = response.json().get('data', [])
    resultado_mares = {}

    for item in dados:
        dt = arrow.get(item["time"]).to('local')
        dia = dt.format('YYYY-MM-DD')
        if dia not in resultado_mares:
            resultado_mares[dia] = []
        resultado_mares[dia].append({
            "time": dt.format('HH:mm'),
            "type": item["type"],
            "height": item["height"]
        })

    return resultado_mares

def get_dados_stormglass():
    coordenadas = carregar_coordenadas()
    nome_praia, praia = selecionar_praia(coordenadas)
    LAT = praia['lat']
    LNG = praia['lng']

    start = arrow.now().floor('day').to('UTC')
    end = start.shift(days=DIAS).ceil('day').to('UTC')

    # COLETA DE MARÉS
    dados_mares = get_mares(LAT, LNG, start, end)

    # COLETA DE DADOS METEOROLÓGICOS
    url = "https://api.stormglass.io/v2/weather/point"
    headers = {
        'Authorization': API_KEY
    }
    params = {
        'lat': LAT,
        'lng': LNG,
        'params': ','.join(PARAMS),
        'start': int(start.timestamp()),
        'end': int(end.timestamp())
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        horas = data.get('hours', [])
        if not horas:
            print("Nenhum dado encontrado.")
            return

        resultado = {}
        for hora in horas:
            dt = arrow.get(hora["time"]).to('local')
            hora_num = dt.hour
            if hora_num not in HORARIOS:
                continue
            dia = dt.format('YYYY-MM-DD')
            hora_str = dt.format('HH:mm')
            if dia not in resultado:
                resultado[dia] = {}
            resultado[dia][hora_str] = {}
            for param in PARAMS:
                valor = hora.get(param, {}).get('sg')
                if valor is not None:
                    resultado[dia][hora_str][param] = valor

        # Adiciona as marés
        for dia in resultado:
            resultado[dia]["tides"] = dados_mares.get(dia, [])

        # Salva no arquivo
        if not os.path.exists('data'):
            os.makedirs('data')
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump({nome_praia: resultado}, f, indent=2, ensure_ascii=False)

        print(f"\nDados salvos em: {OUTPUT_PATH}")

    else:
        print(f"Erro {response.status_code}: {response.text}")

if __name__ == "__main__":
    get_dados_stormglass()
