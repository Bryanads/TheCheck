import os
import secrets

# Gera uma string aleatória segura de 32 bytes (256 bits), boa para HS256
# Pode ser convertida para Base64 para mais compactação se quiser, mas string bruta é ok
print(secrets.token_urlsafe(32))