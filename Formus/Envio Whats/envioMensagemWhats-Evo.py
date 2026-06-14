import os
import re
import time
import random
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


TOKEN_PATH_DRIVE = "/home/envioMensagens/token_drive.json"
TOKEN_PATH = "/home/envioMensagens/token.json"
CLIENT_SECRET_PATH = "/home/envioMensagens/client_secret.json"

# TOKEN_PATH_DRIVE = r"C:\\Users\\Nicol\\OneDrive\\Cursos online\\Treinamento Python - Hashtag\\Códigos\\Nex.ai - Empresa\\Formus\\Envio Whats\\token_drive.json"
# TOKEN_PATH = r"C:\\Users\\Nicol\\OneDrive\\Cursos online\\Treinamento Python - Hashtag\\Códigos\\Nex.ai - Empresa\\Formus\\Envio Whats\\token.json"
# CLIENT_SECRET_PATH = r"C:\\Users\\Nicol\\OneDrive\\Cursos online\\Treinamento Python - Hashtag\\Códigos\\Nex.ai - Empresa\\Formus\\Envio Whats\\client_secret.json"

# Roda query para executar o SQL
def conecta_pg(sql):
    """
    Roda query para executar o SQL

    Parameters:
    Sql = string

    Returns:
    tabela_sql = datatable
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
    tabela_sql = cursor.fetchall()
    cursor.close()
    connection.close()

    # Retorna o resultado da consulta do SQL para o usuário
    return tabela_sql



def executa_groq(mensagem):
    # Obtém o caminho do diretório onde o script está localizado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Procura o .env a partir do diretório do script
    dotenv_path = find_dotenv(os.path.join(script_dir, '.env'))
    # Carrega o .env
    load_dotenv(dotenv_path)

    client = Groq(
    # This is the default and can be omitted
    api_key=os.getenv("GROQ_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                Você deve agir apenas como um reescritor de texto.
                Sua função é mudar algumas frases e palavras, tornando o texto mais natural, fluido e com variações de expressão, sem alterar o sentido, o tom ou a intenção da mensagem original.

                Regras importantes:
                Mantenha o mesmo significado e as mesmas ideias principais, mas alterando todas as frases do texto.
                Não adicione novas informações.
                Não omita nenhuma parte importante.
                Não altere NENHUM link ou nome de arquivo que será enviado.
                Apenas reformule algumas frases e expressões para que o texto soe diferente, mas continue transmitindo exatamente a mesma mensagem.
                Preserve o estilo geral (exemplo: se for informal, continue informal; se for institucional, mantenha formalidade).
                Mude o máximo possível, mas mantenha o sentido original e os links/nomes de arquivos intactos.

                Saída esperada: APENAS O TEXTO REESCRITO, SEM NENHUMA OUTRA INFORMAÇÃO.
                """
            },
            {
                "role": "user",
                "content": f"Aqui está o texto: {mensagem}",
            }
        ],
        model=f"meta-llama/llama-4-maverick-17b-128e-instruct",
        temperature=0,
    )

    return chat_completion.choices[0].message.content


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


def padroniza_numero_whatsapp(numero_bruto):
    """
    Padroniza o número de telefone para o formato E.164 (55DDNNNNNNNNN).
    Remove tudo que não for dígito e garante 55 no início.
    """
    if not isinstance(numero_bruto, str):
        numero_bruto = str(numero_bruto) # Converte para string se não for

    # Remove todos os caracteres não numéricos
    numero_limpo = re.sub(r'\D', '', numero_bruto)

    # Se o número já começa com 55 (código do Brasil), usa como está
    if numero_limpo.startswith('55'):
        # Verifica se tem o DDD (2 dígitos após 55)
        if len(numero_limpo) >= 4 and numero_limpo[2].isdigit() and numero_limpo[3].isdigit():
            return numero_limpo
        else:
            print(f"Aviso: Número '{numero_bruto}' parece ser do Brasil mas não tem DDD completo após o 55. Tentando corrigir.")
            # Tenta adicionar um DDD padrão ou retorna o que tem
            return numero_limpo # Deixa a Evolution API validar

    # Se o número tem 9 dígitos e não tem DDD/código do país, assume 48 (SC) e 55 (Brasil)
    if len(numero_limpo) == 9: # Ex: 999044726
        print(f"Aviso: Número '{numero_bruto}' com 9 dígitos, assumindo DDD 48 e código de país 55.")
        return '5548' + numero_limpo
    # Se o número tem 10 dígitos e não tem DDD/código do país, assume 48 (SC) e 55 (Brasil)
    elif len(numero_limpo) == 10: # Ex: 48999044726
        print(f"Aviso: Número '{numero_bruto}' com 10 dígitos, assumindo código de país 55.")
        return '55' + numero_limpo
    # Se o número tem 11 dígitos e não tem DDD/código do país, assume 55 (Brasil)
    elif len(numero_limpo) == 11: # Ex: 999044726
         print(f"Aviso: Número '{numero_bruto}' com 11 dígitos, assumindo código de país 55.")
         return '55' + numero_limpo


    # Adiciona 55 se o número limpo tiver 11 ou 13 dígitos e não começar com 55
    # 11 dígitos: DDD + 9 dígitos (ex: 48999044726)
    # 13 dígitos: 55 + DDD + 9 dígitos (ex: 5548999044726)
    if len(numero_limpo) == 11 and not numero_limpo.startswith('55'): # Ex: 48999044726
         return '55' + numero_limpo
    elif len(numero_limpo) == 13 and not numero_limpo.startswith('55'): # Ex: 5548999044726 (já tem 55)
         return numero_limpo # Já está no formato esperado

    # Retorna o número limpo como último recurso se não se encaixar nos padrões conhecidos
    print(f"Aviso: Número '{numero_bruto}' não se encaixa em padrões comuns de WhatsApp, retornando como '{numero_limpo}'.")
    return numero_limpo


# Função principal para enviar e-mails para uma lista de destinatários
def envia_email(mensagem_email, destinatarios_email, assunto_email):
    """Envia um e-mail para múltiplos destinatários usando SMTP e senha de app."""
    
    # Obtém o caminho do diretório onde o script está localizado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Procura o .env a partir do diretório do script
    dotenv_path = find_dotenv(os.path.join(script_dir, '.env'))
    # Carrega o .env
    load_dotenv(dotenv_path)

    # Obtém o e-mail e a senha do arquivo .env
    usuario_email = os.getenv("EMAIL")  # E-mail do remetente
    senha_app = os.getenv("SENHA_APP_EMAIL")  # Senha de app configurada no Gmail

    if not usuario_email or not senha_app:
        print("Erro: Certifique-se de que EMAIL e SENHA_APP_EMAIL estão definidos no .env")
        return

    # Itera pelos destinatários e envia os e-mails
    send_email_via_smtp(usuario_email, senha_app, destinatarios_email, assunto_email, mensagem_email)


# Função para enviar o e-mail via SMTP usando a senha de app
def send_email_via_smtp(sender, password, to, subject, message_text):
    """Envia o e-mail usando SMTP do Gmail."""
    try:
        # Se 'to' for uma lista, formata o header "To" como string separada por vírgulas
        to_header = ", ".join(to) if isinstance(to, list) else to

        # Cria a mensagem de e-mail
        message = create_message(sender, to_header, subject, message_text)

        # Conecta ao servidor SMTP do Gmail
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Inicia a conexão segura (TLS)
            server.login(sender, password)  # Autentica com o Gmail usando a senha de app
            server.sendmail(sender, to, message.as_string())  # Envia o e-mail

        print(f"E-mail enviado para {to}")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")


# Função para criar a mensagem de e-mail no formato MIME
def create_message(sender, to, subject, message_text):
    """Cria uma mensagem de e-mail no formato MIME."""
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = to
    message['Subject'] = subject

    # Anexa o corpo da mensagem (pode ser plain/text ou HTML)
    msg = MIMEText(message_text, 'html')  # Use 'plain' para texto simples
    message.attach(msg)

    return message


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
  

def envia_status(linha, mensagem):
    url = f"https://script.google.com/macros/s/AKfycbwN8hpNxu2cSWIPlckxs_IczLs587OzlUKMj8zF0bf3YxjQDjEmd7Gl-HTSkD06SRCPow/exec?linha={linha}&status={mensagem}"

    # Fazendo a requisição para a API
    response = requests.get(url)


def envia_status_sheet(linha, mensagem):
    url = f"https://script.google.com/macros/s/AKfycbypxKFgL9AYmAHe92TI-IzPfQvkXmH_LuKuruiJh0z9obq1vg1w8PnQ3E7qCiQzifZuzA/exec?linha={linha}&status={mensagem}"

    # Fazendo a requisição para a API
    response = requests.get(url)


def movimenta_backup(nome, numero, tipo, status):
    url = f"https://script.google.com/macros/s/AKfycbyhxuc6K2iUTWRmi6Npi37oVVxrGKDZCf8ZMlI7gPaqn5roaxw2LyJsHYcXSwdlB_t1/exec?nome_cliente={nome}&numero_cliente={numero}&tipo_cliente={tipo}&status_cliente={status}"

    # Fazendo a requisição para a API
    response = requests.get(url)


def exclui_linha(linha):
    url = f"https://script.google.com/macros/s/AKfycby4HQoUyW8wBFa84XD-K9iz5MtPeaSClVlh8KomyXw-7nz4arr4lbMRAjdDDLW_xp8oVQ/exec?linha={linha}"

    # Fazendo a requisição para a API
    response = requests.get(url)
    

def le_informacoes_envio():
    url = f"https://script.google.com/macros/s/AKfycbypxKFgL9AYmAHe92TI-IzPfQvkXmH_LuKuruiJh0z9obq1vg1w8PnQ3E7qCiQzifZuzA/exec?action=getInfo"

    # Fazendo a requisição para a API
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        data = response.json()

        return data
    

def guarda_dados_envios(nome, numero, tipo, mensagem, arquivo, data_hora, status):
    url = f"https://script.google.com/macros/s/AKfycbzGVmj7C_DPgp_wnxLcr-CYmJ7VNo0-D99Wx32ehb3ff4pK09ejM9X4ocBO9mfDgVS9rg/exec?nome_cliente={nome}&numero_cliente={numero}&tipo_cliente={tipo}&mensagem={mensagem}&arquivo={arquivo}&&data_hora={data_hora}&status_cliente={status}"

    requests.get(url)


def baixar_arquivo_do_drive_por_pasta(arquivo, folder_id="105tCcqy10othx4cccSlVmhtf35d_vO8H", destino_local="/tmp/documento_baixado"):
    """
    Lista e baixa arquivos de uma pasta específica do Google Drive para um diretório local.

    Parameters:
    folder_id (str): O ID da pasta do Google Drive de onde os arquivos serão baixados.
    destino_local (str): O caminho do diret diretório onde os arquivos serão salvos.

    Returns:
    list: Uma lista de caminhos dos arquivos baixados.
    """
    # Escopos para Google Sheets e Google Drive (leitura)
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    creds = None
    # ATENÇÃO: Ajuste estes caminhos para o seu ambiente na Hostinger
    # Exemplo para Hostinger (Linux):

    # Lógica de autenticação (reutilizada e ajustada)
    if os.path.exists(TOKEN_PATH_DRIVE):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH_DRIVE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH_DRIVE, 'w') as token:
            token.write(creds.to_json())

    baixados = []
    try:
        service = build('drive', 'v3', credentials=creds)

        # Buscar arquivos dentro da pasta específica
        # A query '"{folder_id}" in parents' busca arquivos que são filhos dessa pasta.
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false", # trashed = false para não pegar arquivos na lixeira
            fields='files(id, name, mimeType)'
        ).execute()
        items = results.get('files', [])

        if not items:
            print(f"Nenhum arquivo encontrado na pasta: {folder_id}")
            return baixados
        else:
            print(f"Arquivos encontrados na pasta {folder_id}:")
            for file_info in items:
                file_id = file_info['id']
                file_name = file_info['name']

                # --- INÍCIO DA CORREÇÃO ---
                file_mime_type = file_info.get('mimeType') # Usa .get() para evitar KeyError

                # Se mimeType estiver ausente ou for uma pasta, pule este item
                if file_mime_type is None or file_mime_type == 'application/vnd.google-apps.folder':
                    print(f"  - Pulando '{file_name}' (ID: {file_id}) pois não é um arquivo baixável (mimeType ausente ou é uma pasta).")
                    continue # Pula para o próximo item no loop
                # --- FIM DA CORREÇÃO ---

                # Determina a extensão do arquivo e o mimeType para exportação se for um documento do Google
                export_mime_type = None
                extension = ""

                if 'application/vnd.google-apps.document' in file_mime_type:
                    export_mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' # .docx
                    extension = ".docx"
                elif 'application/vnd.google-apps.spreadsheet' in file_mime_type:
                    export_mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' # .xlsx
                    extension = ".xlsx"
                elif 'application/vnd.google-apps.presentation' in file_mime_type:
                    export_mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation' # .pptx
                    extension = ".pptx"
                elif 'application/pdf' in file_mime_type:
                    extension = ".pdf"
                elif '.' in file_name:
                    extension = f".{file_name.split('.')[-1]}"
                else:
                    # Tenta inferir da parte final do mimeType se não tiver extensão
                    if '/' in file_mime_type:
                        extension = f".{file_mime_type.split('/')[-1]}"
                    else:
                        extension = "" # Se não conseguir inferir, deixa sem extensão

                # Para todos os outros tipos de arquivos (PDF, PNG, MP3, DOCX comum, etc.)
                if export_mime_type: # Se foi definido um export_mime_type (é um arquivo nativo do Google)
                    request_to_download = service.files().export_media(fileId=file_id, mimeType=export_mime_type)
                else: # Se não é um arquivo nativo do Google, baixe diretamente (get_media)
                    request_to_download = service.files().get_media(fileId=file_id)
                    # Para arquivos não-nativos do Google, a extensão é normalmente inferida do nome do arquivo
                    # ou do mimeType se não houver extensão no nome.
                    # Já temos essa lógica logo abaixo.
                    if 'application/pdf' in file_mime_type:
                        extension = ".pdf"
                    elif '.' in file_name: # Se o nome já tem extensão, usa a que tem
                        extension = f".{file_name.split('.')[-1]}"
                    elif '/' in file_mime_type: # Tenta inferir da parte final do mimeType se não tiver extensão
                        extension = f".{file_mime_type.split('/')[-1]}"
                    # Se for um docx que foi apenas carregado, o mimeType será algo como 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    # e ele cairá aqui no 'else' e será baixado corretamente.

                # Garante que o diretório de destino exista
                os.makedirs(destino_local, exist_ok=True)

                if str(arquivo).lower() in str(file_name).lower():              
                    # Constrói o caminho completo do arquivo usando o nome original
                    local_file_path = os.path.join(destino_local, file_name)

                    # Abre o arquivo com o nome original para escrita binária
                    with open(local_file_path, 'wb') as temp_file: # temp_file agora é o arquivo com nome original
                        downloader = MediaIoBaseDownload(temp_file, request_to_download)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                            # print(f"Download de '{file_name}': {int(status.progress() * 100)}%.") # Descomente para ver o progresso

                    print(f"Arquivo '{file_name}' baixado para '{local_file_path}'")
                    baixados.append(local_file_path)

            return baixados

    except Exception as e:
        print(f"Ocorreu um erro ao baixar os arquivos do Drive: {e}")
        return []
    

def send_whatsapp_message(number, text):
    # Obtém o caminho do diretório onde o script está localizado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Procura o .env a partir do diretório do script
    dotenv_path = find_dotenv(os.path.join(script_dir, '.env'))
    # Carrega o .env
    load_dotenv(dotenv_path)

    evolution_api_url = os.getenv("EVOLUTION_API_URL")
    evolution_instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
    evolution_api_key = os.getenv("EVOLUTION_API_KEY")

    # Monta a base de URL para enviar a mensagem
    url = f"{evolution_api_url}/message/sendText/{evolution_instance_name}"

    # Monta o cabeçalho da requisição
    # O cabeçalho é onde estão os dados que identificam a requisição
    headers = {
        "apikey": f"{evolution_api_key}",
        "Content-Type": "application/json",
    }

    # Monta o payload da requisição
    # O payload é o corpo da requisição, onde estão os dados que queremos enviar
    payload = {
        "number": f"{number}",
        "text": f"""{text}""",
        "delay": 10,
    }

    print(f"[EVOLUTION_API] Enviando para URL: {url}")
    print(f"[EVOLUTION_API] Headers: {headers}")
    print(f"[EVOLUTION_API] Payload: {payload}")

    # Faz a requisição POST para enviar a mensagem
    # A requisição POST é usada para enviar dados para o servidor
    # requests.post(url=url, headers=headers, json=payload)

    try:
        response = requests.post(url=url, headers=headers, json=payload)
        response.raise_for_status() # Levanta um erro para status de erro (4xx ou 5xx)
        print(f"[EVOLUTION_API] Resposta da API: {response.status_code} - {response.text}")

        return True, ""
    
    except requests.exceptions.RequestException as e:
        print(f"[EVOLUTION_API] Erro ao enviar mensagem: {e}")

        return False, ""


def send_whatsapp_media(number, caminho_arquivo, caption=None):
    """
    Envia um arquivo (documento, imagem, vídeo, áudio) via API Evolution.

    Parameters:
    number (str): O número de telefone do destinatário (ex: "5511987654321").
    caminho_arquivo (str): O caminho completo para o arquivo local a ser enviado.
    caption (str, optional): A legenda para a mídia (visível para o usuário no WhatsApp).
                             Se não for fornecido, será o nome do arquivo.
    """
    # Obtém o caminho do diretório onde o script está localizado
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Procura o .env a partir do diretório do script
    dotenv_path = find_dotenv(os.path.join(script_dir, '.env'))
    # Carrega o .env
    load_dotenv(dotenv_path)

    EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
    EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
    EVOLUTION_INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME")

    if not EVOLUTION_API_URL or not EVOLUTION_API_KEY or not EVOLUTION_INSTANCE_NAME:
        print("Erro: Variáveis de ambiente da API Evolution não configuradas. Verifique .env")
        return False, ""

    url = f"{EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE_NAME}"

    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }

    # Verifica se o arquivo existe
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: Arquivo não encontrado no caminho: {caminho_arquivo}")

    # Lê o arquivo e converte para base64
    with open(caminho_arquivo, "rb") as f:
        encoded_file = base64.b64encode(f.read()).decode("utf-8")

    # Extrai o nome do arquivo e a extensão
    nome_base = os.path.basename(caminho_arquivo) # Ex: "documento.pdf"
    nome_sem_extensao, extensao = os.path.splitext(nome_base) # Ex: ("documento", ".pdf")

    # Se a legenda não for fornecida, usa o nome do arquivo sem extensão
    if caption is None:
        caption = nome_sem_extensao

    # --- DETERMINAÇÃO DO mediatype E mimetype ---
    # Usamos a biblioteca 'mimetypes' para uma detecção mais robusta
    mimetype, _ = mimetypes.guess_type(caminho_arquivo)
    
    # Define valores padrão caso a detecção falhe
    if mimetype is None:
        mimetype = "application/octet-stream" # Tipo genérico para binários

    # Lógica para definir o 'mediatype' da Evolution API
    mediatype = "document" # Padrão para arquivos não identificados explicitamente

    if mimetype.startswith("image/"):
        mediatype = "image"
    elif mimetype.startswith("video/"):
        mediatype = "video"
    elif mimetype.startswith("audio/"):
        mediatype = "audio"
    # Para PDFs e outros documentos, 'document' é o correto.

    # Caso específico para Excel, que pode não ser pego pelo mimetypes de forma exata como .xlsx
    if extensao.lower() == ".xlsx" and mediatype == "document":
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif extensao.lower() == ".xls" and mediatype == "document":
        mimetype = "application/vnd.ms-excel"
    elif extensao.lower() == ".pdf" and mediatype == "document":
        mimetype = "application/pdf"
    elif extensao.lower() == ".doc" and mediatype == "document":
        mimetype = "application/msword"
    elif extensao.lower() == ".docx" and mediatype == "document":
        mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif extensao.lower() == ".txt" and mediatype == "document":
        mimetype = "text/plain"


    payload = {
        "number": number,
        "mediatype": mediatype,
        "mimetype": mimetype,
        "caption": caption,
        "media": encoded_file,
        "delay": 10,
        "fileName": nome_base # Usa o nome do arquivo original completo (com extensão)
    }

    print(f"[EVOLUTION_API] Enviando para URL: {url}")
    print(f"[EVOLUTION_API] Headers: {headers}")
    print(f"[EVOLUTION_API] Payload: {payload}")

    try:
        response = requests.post(url=url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"[EVOLUTION_API] Resposta da API: {response.status_code} - {response.text}")
        return True, ""

    except requests.exceptions.RequestException as e:
        print(f"[EVOLUTION_API] Erro ao enviar mídia: {e}")

        # Envio dos e-mails de erro
        destinatarios_email = []
        destinatarios_email.append('nicolaspn09@gmail.com')

        assunto_email = "ERRO Envio Arquivos Whats - Setor Reformas"

        mensagem = f"""
        Olá!<br<br>

        Há erro ao enviar os arquivos no whats!<br><br>

        Erro: {e}
        """

        envia_email(mensagem_email=mensagem, destinatarios_email=destinatarios_email, assunto_email=assunto_email)

        return False, e


def main():
    try:
        envia_status_sheet(linha=2, mensagem=f"⏳️")
        data_atual = datetime.now()
        data_convertida = data_atual.strftime("%Y-%m-%d")

        envio = True
        tabela_numeros = solicita_tabela()
        tabela_mensagem = le_informacoes_envio()

        contador = 0
        linha_atual = 1
        linhas_excluidas = 0
        caminhos_arquivos_baixados = []
        caminho = None

        sql = f"select * from envio.envio_whats where date(data_envio) = '{data_convertida}'"
        tabela = conecta_pg(sql=sql)
        contador = len(tabela)

        if contador < 40:
            for informacao_mensagem in tabela_mensagem:
                mensagem = informacao_mensagem["mensagem"]
                nome_arquivo = informacao_mensagem["nome_arquivo"]

                break

            for informacao_numero in tabela_numeros:
                linha_atual += 1
                linha = informacao_numero["linha"]
                numero = informacao_numero["numero"]
                numero = padroniza_numero_whatsapp(numero_bruto=numero)
                tipo_cliente = informacao_numero["tipo"]
                enviar = informacao_numero["enviar"]
                nome = informacao_numero["nome"]
                status = informacao_numero["status"]

                ### AQUI TEMOS QUE CONSULTAR SE O NÚMERO JÁ FOI ENVIADO HOJE (ESTÁ DENTRO DA TABELA)
                for i in tabela:
                    numero_enviado = i[1]
                    mensagem_enviada = i[3]

                    if numero_enviado in numero and str(mensagem).lower() in mensagem_enviada.lower():
                        envio = False
                        break

                if ("true" in str(enviar).lower() and envio == True) and nome_arquivo == "NA" and mensagem != "NA":
                    mensagem = executa_groq(mensagem=mensagem)
                    retorno, _ = send_whatsapp_message(numero, f"""{mensagem}""")

                    # Se o retorno foi falso, apagar a linha e jogar para o backup
                    if retorno == False:
                        envia_status(linha, f"Erro  | {datetime.now()}")
                        movimenta_backup(nome, numero, tipo_cliente, status)
                        # exclui_linha(linha_atual)

                        linha_atual -= 1
                        linhas_excluidas += 1

                        time.sleep(random.randint(30, 120))

                        continue

                    else:
                        linha -= linhas_excluidas
                        envia_status(linha, f"Enviado | {datetime.now()}")

                        guarda_dados_envios(nome, numero, tipo_cliente, mensagem, "", datetime.now(), f"Enviado | {datetime.now()}")

                        contador += 1

                    sql = f"insert into envio.envio_whats (numero, data_envio, mensagem) values ('{numero}', '{data_convertida}', '{mensagem}')"
                    conecta_pg_insert(sql=sql)

                    time.sleep(random.randint(30, 120))

                elif ("true" in str(enviar).lower() and envio == True) and nome_arquivo != "NA" and mensagem != "NA":
                    # Baixa os arquivos da pasta do Google Drive
                    caminhos_arquivos_baixados = baixar_arquivo_do_drive_por_pasta(arquivo=nome_arquivo)

                    for caminho in caminhos_arquivos_baixados:
                        if caminho:
                            mensagem = executa_groq(mensagem=mensagem)
                            retorno, _ = send_whatsapp_media(numero, caminho, mensagem)

                            # Se o retorno foi falso, apagar a linha e jogar para o backup
                            if retorno == False:
                                envia_status(linha, f"Erro  | {datetime.now()}")
                                movimenta_backup(nome, numero, tipo_cliente, "Telefone não encontrado")
                                # exclui_linha(linha_atual)

                                linha_atual -= 1
                                linhas_excluidas += 1
                                
                                time.sleep(random.randint(30, 120))

                                continue

                            else:
                                linha -= linhas_excluidas                    
                                envia_status(linha, f"Arquivo e Mensagem Enviados | {datetime.now()}")

                                guarda_dados_envios(nome, numero, tipo_cliente, mensagem, nome_arquivo, datetime.now(), f"Arquivo e Mensagem Enviados | {datetime.now()}")

                                contador += 1

                            sql = f"insert into envio.envio_whats (numero, data_envio, mensagem) values ('{numero}', '{data_convertida}', '{mensagem}')"
                            # conecta_pg_insert(sql=sql)

                            time.sleep(random.randint(30, 120))

                            break

                elif ("true" in str(enviar).lower() and envio == True) and nome_arquivo != "NA" and mensagem == "NA":
                    # Baixa os arquivos da pasta do Google Drive
                    caminhos_arquivos_baixados = baixar_arquivo_do_drive_por_pasta(arquivo=nome_arquivo)

                    for caminho in caminhos_arquivos_baixados:
                        if caminho:
                            retorno, _ = send_whatsapp_media(numero, caminho)

                            # Se o retorno foi falso, apagar a linha e jogar para o backup
                            if retorno == False:
                                envia_status(linha, f"Erro  | {datetime.now()}")
                                movimenta_backup(nome, numero, tipo_cliente, status)
                                # exclui_linha(linha_atual)

                                linha_atual -= 1
                                linhas_excluidas += 1

                                time.sleep(random.randint(30, 120))

                                continue
                            
                            else:
                                linha -= linhas_excluidas
                                envia_status(linha, f"Arquivo Enviado | {datetime.now()}")

                                guarda_dados_envios(nome, numero, tipo_cliente, "", nome_arquivo, datetime.now(), f"Arquivo Enviado | {datetime.now()}")

                                contador += 1

                            sql = f"insert into envio.envio_whats (numero, data_envio, mensagem) values ('{numero}', '{data_convertida}', '{mensagem}')"
                            # conecta_pg_insert(sql=sql)

                            time.sleep(random.randint(30, 120))

                            break

                # Estoura o envio para somente X mensagens
                if contador > 1000:
                    break

            if caminho:
                os.remove(caminho)  # Remove o arquivo baixado após o envio

        envia_status_sheet(linha=2, mensagem=f"✅")

    except Exception as e:
        envia_status_sheet(linha=2, mensagem=f"❌ | {datetime.now()}")

        # Envio dos e-mails de erro
        destinatarios_email = []
        destinatarios_email.append('nicolaspn09@gmail.com')

        assunto_email = "ERRO Envio Mensagem Whats - Setor Reformas"

        mensagem = f"""
        Olá!<br<br>

        Há erro ao enviar as mensagens no whats!<br><br>

        Erro: {e}
        """

        envia_email(mensagem_email=mensagem, destinatarios_email=destinatarios_email, assunto_email=assunto_email)



main()


# if __name__ == "__main__":
#     DIRETORIO_DESTINO = r"C:\Users\nicol\Downloads"

#     # Baixa os arquivos da pasta do Google Drive
#     caminhos_arquivos_baixados = baixar_arquivo_do_drive_por_pasta(destino_local=DIRETORIO_DESTINO)

#     if caminhos_arquivos_baixados:
#         print(f"Arquivos baixados com sucesso: {caminhos_arquivos_baixados}")
#         for caminho in caminhos_arquivos_baixados:
#             print(f"Arquivo baixado: {caminho}")

#             send_whatsapp_media("5548999044726", caminho)
#         # Agora você tem os caminhos dos arquivos baixados.
#         # Você pode iterar sobre 'caminhos_arquivos_baixados'
#         # e usar cada caminho na sua função send_whatsapp_message (se sua API Evolution suportar arquivos).
#         # Lembre-se de que os arquivos temporários criados por tempfile.NamedTemporaryFile(delete=False)
#         # não são automaticamente excluídos. Você precisará gerenciar a exclusão (ex: os.remove(caminho_arquivo))
#         # quando não precisar mais deles.

#         # Exemplo de como usar os arquivos baixados (depende da sua API Evolution)
#         # for caminho_arquivo in caminhos_arquivos_baixados:
#         #     send_whatsapp_message(numero, f"Sua mensagem com anexo!", caminho_do_arquivo=caminho_arquivo)

#     else:
#         print("Nenhum arquivo foi baixado ou ocorreu um erro.")