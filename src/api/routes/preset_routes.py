from flask import Blueprint, request, jsonify
import datetime
from src.db.queries import (
    create_user_recommendation_preset,
    get_user_recommendation_presets,
    get_user_recommendation_preset_by_id,
    update_user_recommendation_preset,
    delete_user_recommendation_preset,
    get_user_by_id,
    get_default_user_recommendation_preset # Importar a nova função
)

preset_bp = Blueprint('presets', __name__)

@preset_bp.route('/presets', methods=['POST'])
def create_preset_endpoint():
    data = request.get_json()
    user_id = data.get('user_id')
    preset_name = data.get('preset_name')
    spot_ids = data.get('spot_ids')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    day_offset_default = data.get('day_offset_default') # Não assume mais 0, pode ser None se não enviado
    is_default = data.get('is_default', False)

    if not all([user_id, preset_name, spot_ids, start_time_str, end_time_str]):
        return jsonify({"error": "Todos os campos obrigatórios (user_id, preset_name, spot_ids, start_time, end_time) são necessários."}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": f"Usuário com ID {user_id} não encontrado."}), 404

    try:
        spot_ids = [int(s_id) for s_id in spot_ids]
        start_time = datetime.time.fromisoformat(start_time_str)
        end_time = datetime.time.fromisoformat(end_time_str)

        if day_offset_default is not None:
            if not isinstance(day_offset_default, list):
                return jsonify({"error": "day_offset_default deve ser uma lista de números inteiros."}), 400
            day_offset_default = [int(offset) for offset in day_offset_default]
        
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Erro de formato de dados. Verifique spot_ids (lista de inteiros), horários (HH:MM:SS) e day_offset_default (lista de inteiros). Erro: {e}"}), 400

    try:
        preset_id = create_user_recommendation_preset(
            user_id, preset_name, spot_ids, start_time, end_time, day_offset_default, is_default
        )
        return jsonify({"message": "Preset criado com sucesso!", "preset_id": preset_id}), 201
    except Exception as e:
        return jsonify({"error": f"Falha ao criar preset: {e}"}), 500

@preset_bp.route('/presets', methods=['GET'])
def get_presets_endpoint():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Campo 'user_id' é obrigatório como parâmetro de query."}), 400
    
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": f"Usuário com ID {user_id} não encontrado."}), 404

    try:
        presets = get_user_recommendation_presets(user_id)
        for preset in presets:
            if isinstance(preset.get('start_time'), datetime.time):
                preset['start_time'] = preset['start_time'].strftime('%H:%M:%S')
            if isinstance(preset.get('end_time'), datetime.time):
                preset['end_time'] = preset['end_time'].strftime('%H:%M:%S')
        return jsonify(presets), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao buscar presets: {e}"}), 500

@preset_bp.route('/presets/<int:preset_id>', methods=['GET'])
def get_preset_by_id_endpoint(preset_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Campo 'user_id' é obrigatório como parâmetro de query."}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": f"Usuário com ID {user_id} não encontrado."}), 404

    try:
        preset = get_user_recommendation_preset_by_id(preset_id, user_id)
        if not preset:
            return jsonify({"error": f"Preset com ID {preset_id} não encontrado para o usuário {user_id}."}), 404
        
        if isinstance(preset.get('start_time'), datetime.time):
            preset['start_time'] = preset['start_time'].strftime('%H:%M:%S')
        if isinstance(preset.get('end_time'), datetime.time):
            preset['end_time'] = preset['end_time'].strftime('%H:%M:%S')

        return jsonify(preset), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao buscar preset: {e}"}), 500

@preset_bp.route('/presets/<int:preset_id>', methods=['PUT'])
def update_preset_endpoint(preset_id):
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "Campo 'user_id' é obrigatório no corpo da requisição."}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": f"Usuário com ID {user_id} não encontrado."}), 404
    
    updates = {}
    if 'preset_name' in data:
        updates['preset_name'] = data['preset_name']
    if 'spot_ids' in data:
        try:
            updates['spot_ids'] = [int(s_id) for s_id in data['spot_ids']]
        except (ValueError, TypeError):
            return jsonify({"error": "spot_ids deve ser uma lista de IDs de spots inteiros."}), 400
    
    if 'start_time' in data:
        try:
            updates['start_time'] = datetime.time.fromisoformat(data['start_time'])
        except ValueError:
            return jsonify({"error": "Formato de start_time inválido. Use HH:MM:SS."}), 400
    if 'end_time' in data:
        try:
            updates['end_time'] = datetime.time.fromisoformat(data['end_time'])
        except ValueError:
            return jsonify({"error": "Formato de end_time inválido. Use HH:MM:SS."}), 400
    
    if 'day_offset_default' in data:
        try:
            if not isinstance(data['day_offset_default'], list):
                return jsonify({"error": "day_offset_default deve ser uma lista de números inteiros."}), 400
            updates['day_offset_default'] = [int(offset) for offset in data['day_offset_default']]
        except (ValueError, TypeError):
            return jsonify({"error": "day_offset_default deve ser uma lista de números inteiros."}), 400
    
    if 'is_default' in data:
        updates['is_default'] = bool(data['is_default'])
    if 'is_active' in data:
        updates['is_active'] = bool(data['is_active'])

    if not updates:
        return jsonify({"message": "Nenhum campo fornecido para atualização."}), 400

    try:
        success = update_user_recommendation_preset(preset_id, user_id, updates)
        if success:
            return jsonify({"message": "Preset atualizado com sucesso!"}), 200
        else:
            return jsonify({"error": "Preset não encontrado ou não autorizado para atualização."}), 404
    except Exception as e:
        return jsonify({"error": f"Falha ao atualizar preset: {e}"}), 500

@preset_bp.route('/presets/<int:preset_id>', methods=['DELETE'])
def delete_preset_endpoint(preset_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Campo 'user_id' é obrigatório como parâmetro de query."}), 400
    
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": f"Usuário com ID {user_id} não encontrado."}), 404

    try:
        success = delete_user_recommendation_preset(preset_id, user_id)
        if success:
            return jsonify({"message": "Preset desativado (excluído logicamente) com sucesso!"}), 200
        else:
            return jsonify({"error": "Preset não encontrado ou não autorizado para desativação."}), 404
    except Exception as e:
        return jsonify({"error": f"Falha ao desativar preset: {e}"}), 500

# NOVO ENDPOINT: Obter preset padrão
@preset_bp.route('/presets/default', methods=['GET'])
def get_default_preset_endpoint():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "Campo 'user_id' é obrigatório como parâmetro de query."}), 400
    
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": f"Usuário com ID {user_id} não encontrado."}), 404

    try:
        preset = get_default_user_recommendation_preset(user_id)
        if not preset:
            return jsonify({"message": "Nenhum preset padrão encontrado para este usuário."}), 200
        
        # Formatar horários para string para JSON
        if isinstance(preset.get('start_time'), datetime.time):
            preset['start_time'] = preset['start_time'].strftime('%H:%M:%S')
        if isinstance(preset.get('end_time'), datetime.time):
            preset['end_time'] = preset['end_time'].strftime('%H:%M:%S')

        return jsonify(preset), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao buscar preset padrão: {e}"}), 500