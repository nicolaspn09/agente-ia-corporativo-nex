import re
import os.path
import requests
import psycopg2
from datetime import datetime, date
from dotenv import load_dotenv, find_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/user.emails.read",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/user.phonenumbers.read"
]

def main():
    creds = None

    # token_path = r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\token-Paulo.json"
    # credentials_path = r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\credentials-Paulo.json"

    token_path = "/home/envioMensagens/token-Paulo.json"
    credentials_path = "/home/envioMensagens/credentials-Paulo.json"

    # Carregar token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # Atualizar / criar token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("people", "v1", credentials=creds)

        all_contacts = []
        page_token = None

        while True:
            results = (
                service.people()
                .connections()
                .list(
                    resourceName="people/me",
                    pageSize=100,
                    personFields="names,emailAddresses,phoneNumbers,metadata",
                    pageToken=page_token
                )
                .execute()
            )

            connections = results.get("connections", [])
            all_contacts.extend(connections)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        # Agora vamos montar uma lista com nome + emails + telefones
        contatos_extraidos = []

        for person in all_contacts:

            # Nome
            name = None
            if "names" in person and person["names"]:
                name = person["names"][0].get("displayName")

            # Emails
            emails = []
            if "emailAddresses" in person:
                for e in person["emailAddresses"]:
                    if "value" in e:
                        emails.append(e["value"])

            # Telefones
            phones = []
            if "phoneNumbers" in person:
                for p in person["phoneNumbers"]:
                    if "value" in p:
                        phones.append(p["value"])

            update_time = None
            if "metadata" in person and "sources" in person["metadata"]:
                for src in person["metadata"]["sources"]:
                    if src.get("type") == "CONTACT" and "updateTime" in src:
                        update_time = src["updateTime"]
                        break

            contatos_extraidos.append({
                "nome": name,
                "emails": emails,
                "telefones": phones,
                "update_time": update_time
            })

        return contatos_extraidos

    except HttpError as err:
        print(err)


# Roda query para executar o SQL
def conecta_pg(sql):
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
    tabela_sql = cursor.fetchall()
    cursor.close()
    connection.close()

    # Retorna o resultado da consulta do SQL para o usuário
    return tabela_sql


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


def limpar_telefone(telefone: str) -> str:
    if not telefone:
        return ""
    # Remove tudo que não for número
    telefone_limpo = re.sub(r'\D', '', telefone)
    return telefone_limpo


def is_update_today(update_time_str):
    if not update_time_str:
        return False

    # Converte string ISO do Google em datetime
    dt = datetime.fromisoformat(update_time_str.replace("Z", "+00:00"))

    # Compara apenas a DATA (ignora horas, minutos etc.)
    return dt.date() == date.today()


if __name__ == "__main__":
    contatos = main()

    for i in contatos:
        nome = i['nome']
        telefones = i['telefones']
        update_time = i['update_time']

        if is_update_today(update_time):
            for telefone in telefones:
                telefone = limpar_telefone(telefone)

                if not str(telefone).strip().startswith("55") and not str(telefone).strip().startswith("0"):
                    telefone = f"55{str(telefone).strip()}"

                sql = f"""select * from envio.numeros_telefone where numero_telefone = '{str(telefone).replace("'", "").replace("+", "").strip()}'"""
                tabela_sql = conecta_pg(sql)

                if len(tabela_sql) == 0 and (str(telefone).strip() != "" and (len(str(telefone).strip()) >= 10 and len(str(telefone).strip()) < 14) and not (str(telefone).strip().startswith("0") or str(telefone).strip().startswith("55800"))):                    
                    url_novos_numeros = f"https://script.google.com/macros/s/AKfycbwT5IHtp8YYOxuRv2zd84OKv9W6LQfOqGucUU3JV0XM0ipavOYp8deuug5xOYnlWnlv0w/exec"
                    campos = f"""?nome_cliente={str(nome).replace("'", "").strip()}&numero_cliente={str(telefone).replace("'", "").replace("+", "").strip()}&enviar=False"""

                    url_completa = url_novos_numeros + campos
                    resposta = requests.get(url_completa)
                    # print(resposta.text)

                    sql = f"""insert into envio.numeros_telefone (nome_pessoa, numero_telefone) values ('{str(nome).replace("'", "").strip()}', '{str(telefone).replace("'", "").replace("+", "").strip()}')"""
                    conecta_pg_insert(sql=sql)