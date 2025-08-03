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

def convert_to_localtime_string(timestamp_str, timezone='America/Sao_Paulo', fmt='DD/MM HH:mm'):
    try:
        local_time = arrow.get(timestamp_str).to(timezone)
        return local_time.format(fmt)
    except Exception as e:
        print(f"Erro ao converter horário '{timestamp_str}': {e}")
        return timestamp_str 

def load_json_data(filename, folder):
    path = os.path.join(folder, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar '{path}': {e}")
        return None

def save_json_data(data, filename, folder):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return path