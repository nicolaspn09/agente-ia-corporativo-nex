from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import json
import subprocess

# Escopos de acesso
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def open_browser_anonymous(auth_url):
    """
    Abre o navegador Chrome em modo anônimo.
    """
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'  # Caminho para o Chrome
    try:
        subprocess.Popen([chrome_path, '--incognito', auth_url])  # Abre o Chrome com o link em modo anônimo
    except FileNotFoundError:
        print("Erro: Caminho para o Chrome está incorreto ou o Chrome não está instalado.")
        raise

def main():
    creds = None
    token_path = r'CAMINHO PARA O TOKEN'
    client_secret_path = r'CAMINHO PARA O CREDENTIALS'

    # Remover token antigo, se existir
    if os.path.exists(token_path):
        os.remove(token_path)

    # Iniciar fluxo de autenticação
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)

    # Use `run_local_server()` diretamente, que gerencia o redirecionamento automaticamente
    creds = flow.run_local_server(port=8080, open_browser=False)  # Certifique-se de usar a porta autorizada

    # Salvar o token para reutilizar no formato UTF-8
    with open(token_path, 'w', encoding='utf-8') as token_file:
        token_file.write(creds.to_json())

    print("Token salvo como token.json")

if __name__ == '__main__':
    main()