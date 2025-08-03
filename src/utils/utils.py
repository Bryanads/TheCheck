import arrow
import os
import json

def convert_to_localtime(data, timezone='America/Sao_Paulo'):
    for entry in data:
        try:
            local_time = arrow.get(entry['time']).to(timezone)
            entry['time'] = local_time.isoformat()
        except Exception as e:
            print(f"Erro ao converter horário: {entry.get('time')} | {e}")
    return data

def convert_to_localtime_string(timestamp_str, timezone='America/Sao_Paulo'):
    """Converte um timestamp string UTC para uma string no fuso horário local e formata."""
    if not timestamp_str:
        return ""
    try:
        utc_time = arrow.get(timestamp_str).to('utc')
        local_time = utc_time.to(timezone)
        return local_time.format('YYYY-MM-DD HH:mm:ss ZZZ')
    except Exception as e:
        print(f"Erro ao converter string de horário '{timestamp_str}' para horário local: {e}")
        return ""

def load_config(file_path='config.json'):
    """Carrega as configurações de um arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo de configuração '{file_path}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{file_path}' não é um JSON válido.")
        return None
    except Exception as e:
        print(f"Erro ao carregar o arquivo de configuração '{file_path}': {e}")
        return None

def save_config(config_data, file_path='config.json'):
    """Salva as configurações em um arquivo JSON."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        print(f"Configuração salva em '{file_path}'.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo de configuração '{file_path}': {e}")