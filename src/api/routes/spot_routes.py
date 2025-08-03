from flask import Blueprint, jsonify
from src.db.queries import get_all_spots

spot_bp = Blueprint('spots', __name__)

@spot_bp.route('/spots', methods=['GET'])
def get_all_spots_endpoint():
    """
    Endpoint para retornar uma lista de todos os spots disponíveis.
    """
    try:
        spots_raw = get_all_spots() 
        if spots_raw is not None: 
            formatted_spots = []
            for spot in spots_raw:
                formatted_spots.append({
                    'spotId': spot.get('spotId'),   
                    'spotName': spot.get('spotName'),   
                    'latitude': spot.get('latitude'),
                    'longitude': spot.get('longitude'),
                    'timezone': spot.get('timezone')
                })
            return jsonify(formatted_spots), 200
        else:
            # Retorna 200 OK com uma lista vazia se get_all_spots retornar None ou uma lista vazia
            return jsonify([]), 200
    except Exception as e:
        print(f"Erro ao buscar spots: {e}") # Log mais detalhado
        # Retorna um erro 500 com a mensagem de erro detalhada
        return jsonify({"error": f"Erro interno ao carregar spots: {str(e)}"}), 500