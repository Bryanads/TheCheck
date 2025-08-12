import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Adiciona o diretório 'src' ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))


# Inicializa o pool de conexões do banco de dados
from src.db.connection import init_db_pool
init_db_pool()

from src.api import create_app

app = create_app()

if __name__ == '__main__':
    # Certifique-se que o host e a porta correspondem ao que está no seu frontend JS
    # '0.0.0.0' permite que a aplicação seja acessível de outras máquinas na rede,
    # '127.0.0.1' ou 'localhost' restringe ao acesso local.
    # O frontend está usando 'http://127.0.0.1:5000', então 'host=127.0.0.1' ou '0.0.0.0' é ok.
    app.run(debug=True, host='127.0.0.1', port=5000)