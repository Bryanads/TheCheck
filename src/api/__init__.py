# TheCheck/src/api/__init__.py
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Importa e registra as blueprints aqui
    from .routes.recommendation_routes import recommendation_bp
    app.register_blueprint(recommendation_bp)

    # Importa e registra a blueprint de previsões puras
    from .routes.forecast_routes import forecast_bp
    app.register_blueprint(forecast_bp)

    # NOVO: Importa e registra a blueprint de spots
    from .routes.spot_routes import spot_bp # <--- Adicione esta linha
    app.register_blueprint(spot_bp) # <--- Adicione esta linha

    return app