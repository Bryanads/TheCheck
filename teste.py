import arrow
import requests
import json
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Sua chave da API StormGlass
API_KEY = os.getenv('API_KEY_3')

# Parâmetro específico para o nível do mar
# Conforme a documentação da StormGlass, o parâmetro é 'seaLevel'
TIDE_PARAM = ['seaLevel']

# Número de dias para a previsão
DIAS_PREVISAO = 5

# Caminho para o arquivo de configuração das localizações (praias)
CONFIG_PATH = 'configs/locs.json'
# Pasta onde o JSON de saída será salvo
OUTPUT_DIR = 'api_responses'

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
    print("\nEscolha uma das praias disponíveis para testar:")
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

def test_tide_api_request(nome_praia, coordenadas_praia):
    """
    Faz a requisição para o endpoint de nível do mar da StormGlass
    e salva a resposta em um arquivo JSON.
    """
    lat = coordenadas_praia['lat']
    lon = coordenadas_praia['lng']

    # Define o período da requisição (hoje até DIAS_PREVISAO dias no futuro)
    start = arrow.utcnow().floor('day')
    end = start.shift(days=DIAS_PREVISAO).ceil('day')

    # Endpoint da API para nível do mar
    url = "https://api.stormglass.io/v2/tide/sea-level/point"
    headers = {'Authorization': API_KEY}
    params = {
        'lat': lat,
        'lng': lon,
        'params': ','.join(TIDE_PARAM), # Usando 'seaLevel'
        'start': int(start.timestamp()),
        'end': int(end.timestamp())
    }

    print(f"\nFazendo requisição à StormGlass para o nível do mar em {nome_praia}...")
    print(f"URL da Requisição: {url}")
    print(f"Parâmetros: {params}")

    response = requests.get(url, headers=headers, params=params)

    # Garante que a pasta de saída existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = os.path.join(OUTPUT_DIR, f'stormglass_tide_sea_level_{nome_praia.replace(" ", "_").lower()}.json')

    if response.status_code == 200:
        data = response.json()
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Resposta da API salva com sucesso em '{output_filename}'")
        print("\nConteúdo da resposta (primeiras 5 entradas, se houver):")
        if data and 'hours' in data and data['hours']:
            for i, hour_data in enumerate(data['hours'][:5]):
                print(f"  {hour_data.get('time')}: Sea Level = {hour_data.get('seaLevel', {}).get('sg')}m")
        else:
            print("Nenhum dado de 'hours' encontrado na resposta da API.")

    else:
        print(f"Erro na requisição StormGlass: {response.status_code} - {response.text}")
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump({"error": response.status_code, "message": response.text}, f, ensure_ascii=False, indent=4)
        print(f"Erro detalhado salvo em '{output_filename}'")

if __name__ == "__main__":
    coordenadas = carregar_coordenadas()
    if not coordenadas:
        print("Erro ao carregar coordenadas. Saindo.")
    else:
        nome_praia_selecionada, coordenadas_selecionadas = selecionar_praia(coordenadas)
        test_tide_api_request(nome_praia_selecionada, coordenadas_selecionadas)