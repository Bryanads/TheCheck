from flask import Blueprint, jsonify
from src.db.queries import get_all_spots

spot_bp = Blueprint('spots', __name__)

@spot_bp.route('/spots', methods=['GET'])
def get_all_spots_endpoint():
    """
    Endpoint para retornar uma lista de todos os spots disponíveis.
    """
    try:
        # get_all_spots agora retorna dados com chaves em snake_case
        spots_raw = get_all_spots()
        if spots_raw is not None:
            # Não é mais necessário formatar, pois já vem em snake_case
            return jsonify(spots_raw), 200
        else:
            return jsonify({"message": "Nenhum spot encontrado."}), 404
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar spots: {e}"}), 500