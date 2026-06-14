import os
import re
import time
import base64
import smtplib
import requests
import psycopg2
import mimetypes
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


TOKEN_PATH_DRIVE = r"C:\\Users\\Nicol\\OneDrive\\Cursos online\\Treinamento Python - Hashtag\\Códigos\\Nex.ai - Empresa\\Formus\\Envio Whats\\token_drive.json"
TOKEN_PATH = r"C:\\Users\\Nicol\\OneDrive\\Cursos online\\Treinamento Python - Hashtag\\Códigos\\Nex.ai - Empresa\\Formus\\Envio Whats\\token.json"
CLIENT_SECRET_PATH = r"C:\\Users\\Nicol\\OneDrive\\Cursos online\\Treinamento Python - Hashtag\\Códigos\\Nex.ai - Empresa\\Formus\\Envio Whats\\client_secret.json"


# Função que obtém a margem informada pelo usuário
def solicita_tabela():
    """
    Solicita as informações do Google Sheet, guia de margens

    Returns:
    tabela_numeros: list of dict
        Uma lista de dicionários, onde cada dicionário representa uma linha
        da planilha com as chaves: "linha", "nome", "numero", "enviar", "status".
    """
    # Se modificar esses escopos, delete o arquivo token.json.
    # O escopo 'spreadsheets' permite leitura e escrita em planilhas.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # O ID da planilha e o intervalo de exemplo.
    SAMPLE_SPREADSHEET_ID = "1hRfFqUdPDQPIbn7lvo_kUB59mqr1m9LuQV1kWK50BLE"
    # Ajuste o intervalo para incluir a coluna 'E' (Status)
    SAMPLE_RANGE_NAME = "Números!A2:E" # Agora vai até a coluna E

    creds = None
    # Define o caminho completo para os arquivos token.json e client_secret.json
    # É uma boa prática usar caminhos absolutos se o script for executado de diferentes diretórios."

    # Faz o login da API do Google
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # Se não houver credenciais válidas disponíveis, permite que o usuário faça login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Salva as credenciais para a próxima execução
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    # Faz a leitura da planilha
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # Lê as informações do Google Sheets
        # Para garantir que colunas vazias sejam retornadas, a API preenche com strings vazias
        # se o valor não estiver presente no intervalo especificado.
        # Não é necessário um parâmetro especial para isso, a API retorna o que está dentro do range.
        # O tratamento para "trailing empty cells" será feito no Python.
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        valores = result.get('values', []) # Garante que 'values' seja uma lista vazia se não houver dados

        # Processa os valores para incluir colunas vazias e formatar como dicionário
        tabela_numeros = []
        # Definimos o número esperado de colunas com base no seu intervalo 'A:E'
        # e nas chaves que você quer: nome, numero, enviar, status (4 colunas de dados + 1 para linha)
        num_colunas_esperadas = 5 # A (Nome), B (Número), C (Cliente), D (Enviar), E (Status)

        for i, row in enumerate(valores):
            # 'linha' é o índice da linha na planilha, começando de 2 (A2)
            linha_planilha = i + 2
            
            # Preenche a linha com strings vazias se ela tiver menos colunas do que o esperado
            # Isso garante que row[0], row[1], etc., existam
            padded_row = row + [''] * (num_colunas_esperadas - len(row))

            informacao_numero = {
                "linha": linha_planilha,
                "nome": padded_row[0],  # Coluna A
                "numero": padded_row[1], # Coluna B
                "tipo": padded_row[2], # Coluna B
                # padded_row[2] seria a coluna C ("Cliente"), que não está na sua lista desejada
                "enviar": padded_row[3], # Coluna D
                "status": padded_row[4]  # Coluna E
            }
            tabela_numeros.append(informacao_numero)

        return tabela_numeros

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return [] # Retorna uma lista vazia em caso de erro
    

# Roda query para executar o SQL
def conecta_pg_insert(sql):
    """
    Roda query para executar o SQL

    Parameters: 
    sql = string
    """

    # Obtém o caminho do diretório onde o script está localizado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Procura o .env a partir do diretório do script
    dotenv_path = find_dotenv(os.path.join(script_dir, '.env'))
    # Carrega o .env
    load_dotenv(dotenv_path)

    host = 'REMOVED'
    database = 'REMOVED'
    user = 'REMOVED'
    password = 'REMOVED_FOR_GITHUB'
    port = 5432

    # Estabelece a conexão com o banco de dados
    connection = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port
    )

    cursor = connection.cursor()
    cursor.execute(sql)
    connection.commit()
    cursor.close()
    connection.close()
    


tabela_numeros = solicita_tabela()

for i in tabela_numeros:
    nome = i["nome"]
    numero = i["numero"]

    sql = f"""insert into envio.numeros_telefone (nome_pessoa, numero_telefone) values ('{str(nome).replace("'", "").strip()}', '{numero}')"""
    conecta_pg_insert(sql=sql)