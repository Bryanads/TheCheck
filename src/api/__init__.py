from flask import Flask

def create_app():
    app = Flask(__name__)

    # Importa e registra as blueprints aqui
    from .routes.recommendation_routes import recommendation_bp
    app.register_blueprint(recommendation_bp)

    # NOVO: Importa e registra a blueprint de previsões puras
    from .routes.forecast_routes import forecast_bp
    app.register_blueprint(forecast_bp)

    return app