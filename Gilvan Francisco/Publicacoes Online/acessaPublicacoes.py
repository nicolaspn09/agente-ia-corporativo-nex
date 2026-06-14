# Rodar: 01:00
# Comentar código
# Subir para o git

import os
import sys
import time
import base64
import psutil
import locale
import smtplib
import requests
import psycopg2
import datetime
import subprocess
from groq import Groq
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import google.generativeai as genai


# Função para chamar o Groq
def executa_groq_texto(texto, texto2):
    # Carrega as variáveis do ambiente
    load_dotenv()

    api_key = os.getenv('GROQ_API_KEY')

    client = Groq(api_key=api_key)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                Você é um especialista em análises jurídicas. Vou enviar dois textos de intimações para análise. Compare o Texto1 e o Texto2 e diga se são iguais.

                Critério de igualdade:
                Se a única diferença entre os textos for o destinatário da intimação ou o nome das partes, considere os textos iguais e responda apenas 'Sim'.
                Verifique apenas o teor da intimação, se forem iguais, me retorne 'Sim'.
                Se houver qualquer outra diferença no conteúdo (fora o destinatário ou nomes das partes), responda apenas 'Não'.
                
                Instruções:
                Não analise detalhes além do conteúdo principal da intimação.
                Ignore diferenças de formatação, espaços ou variações triviais.
                Responda exclusivamente com 'Sim' ou 'Não'. Não explique, não interprete além do necessário.
                Se forem iguais, interprete os dois textos e veja qual deles o reclamante/intimado é a empresa, me informando com: Texto1 ou Texto2. Se ambos forem empresas, me retorne: Empresas.
                
                Resposta esperada:
                Sim | Texto1
                Sim | Texto2
                Sim | Empresas
                Não
                """
            },
            {
                "role": "user",
                "content": f"Texto1: {texto}. Texto2: {texto2}",
            }
        ],

        # The language model which will generate the completion.
        model="llama-3.3-70b-versatile",
        temperature=0,
        stream=False,
    )

    return chat_completion.choices[0].message.content


# Função para chamar o Groq
def executa_groq_extrai_teor(texto):
    # Carrega as variáveis do ambiente
    load_dotenv()

    api_key = os.getenv('GROQ_API_KEY')

    client = Groq(api_key=api_key)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                Você é um especialista em análises jurídicas. Vou enviar um texto de uma intimação e quero que você extraia o teor dela, excluindo toda parte do nome das partes e destinatários. Extraia também o reclamante/intimados (normalmente fica bem no final, depois do teor) e me retorne apenas se é uma empresa ou uma pessoa (pode acontecer de ter o nome de uma pessoa e do lado ME/EPP/MEI ou o CPF da pessoa, esse caso você também deve considerar como uma empresa).
                Caso o reclamante/intimado seja o escritório de advocacia, considere como empresa.
                Caso o reclamente/intimado seja o Gilvan Francisco, considere como empresa.
         
                Me responda EXATAMENTE assim:
                Teor: texto do teor extraído | Tipo: Empresa ou Pessoa
                """
            },
            {
                "role": "user",
                "content": f"Texto: {texto}",
            }
        ],

        # The language model which will generate the completion.
        model="llama-3.3-70b-versatile",
        temperature=0,
        stream=False,
    )

    return chat_completion.choices[0].message.content


# Executa o Gemini para interpretar texto
def executa_gemini_texto(texto, texto2):
    api_key = os.getenv("GEMINI_API")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(
        [f"""
        Você é um especialista em análises jurídicas. Vou enviar dois textos de intimações para análise. Compare o Texto1 e o Texto2 e diga se são iguais.

        Critério de igualdade:
        Se a única diferença entre os textos for o destinatário da intimação ou o nome das partes, considere os textos iguais e responda apenas 'Sim'.
        Verifique apenas o teor da intimação, se forem iguais, me retorne 'Sim'.
        Se houver qualquer outra diferença no conteúdo (fora o destinatário ou nomes das partes), responda apenas 'Não'.
        
        Instruções:
        Não analise detalhes além do conteúdo principal da intimação.
        Ignore diferenças de formatação, espaços ou variações triviais.
        Responda exclusivamente com 'Sim' ou 'Não'. Não explique, não interprete além do necessário.
        Se forem iguais, interprete os dois textos e veja qual deles o reclamante/intimado é a empresa, me informando com: Texto1 ou Texto2. Se ambos forem empresas, me retorne: Empresas.
        
        Resposta esperada:
        Sim | Texto1
        Sim | Texto2
        Sim | Empresas
        Não
        
        Texto1: {texto}. Texto2: {texto2}
        """],
        stream=True
    )
    response.resolve()
    
    return str(response.text).replace("\n", "")


# Executa o Gemini para interpretar texto
def executa_gemini_extrai_teor(texto):
    api_key = os.getenv("GEMINI_API")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(
        [f"""
        Você é um especialista em análises jurídicas. Vou enviar um texto de uma intimação e quero que você extraia o teor dela, excluindo toda parte do nome das partes e destinatários. Extraia também o reclamante/intimados (normalmente fica bem no final, depois do teor) e me retorne apenas se é uma empresa ou uma pessoa.
         
        Me responda EXATAMENTE assim:
        Teor: texto do teor extraído | Tipo: Empresa ou Pessoa
        
        Texto: {texto}.
        """],
        stream=True
    )
    response.resolve()
    
    return str(response.text).replace("\n", "")


def obtem_data():
    """
    Obtem a data atual

    Returns:
    data_atual: string
    """

    # Obtem a data atual
    data_atual = time.strftime("%d/%m/%Y")

    return data_atual


# Roda query para executar o PG
def conecta_pg(sql):
    """
    Roda query para executar

    Parameters:
    Sql = string

    Returns:
    tabela_sql = datatable
    """

    # Carrega as variáveis do ambiente
    load_dotenv()

    host_database = os.getenv("HOST")
    database_database = os.getenv("DATABASE")
    user_database = os.getenv("USER_PG")
    password_database = os.getenv("PASSWORD")

    print(f"User: {user_database}")

    host = host_database # Endereço do servidor
    database = database_database  # Nome do banco de dados
    user = user_database  # Nome de usuário para acessar o banco de dados
    password = password_database  # Senha do usuário para acessar o banco de dados
    port = 5433

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


# Roda query para executar o MySQL
def conecta_pg_insert(sql):
    """
    Roda query para executar o MySQL

    Parameters: 
    sql = string
    """

    # Carrega as variáveis do ambiente
    load_dotenv()

    host_database = os.getenv("HOST")
    database_database = os.getenv("DATABASE")
    user_database = os.getenv("USER_PG")
    password_database = os.getenv("PASSWORD")

    host = host_database # Endereço do servidor
    database = database_database  # Nome do banco de dados
    user = user_database  # Nome de usuário para acessar o banco de dados
    password = password_database  # Senha do usuário para acessar o banco de dados
    port = 5433

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


# Função principal para enviar e-mails para uma lista de destinatários
def envia_email(mensagem_email, destinatarios_email, assunto_email):
    """Envia um e-mail para múltiplos destinatários usando SMTP e senha de app."""
    
    # Carrega as variáveis de ambiente (do arquivo .env)
    load_dotenv()

    # Obtém o e-mail e a senha do arquivo .env
    usuario_email = os.getenv("EMAIL")  # E-mail do remetente
    senha_app = os.getenv("SENHA_APP_EMAIL")  # Senha de app configurada no Gmail

    if not usuario_email or not senha_app:
        print("Erro: Certifique-se de que EMAIL e SENHA_APP_EMAIL estão definidos no .env")
        return

    # Itera pelos destinatários e envia os e-mails
    send_email_via_smtp(usuario_email, senha_app, destinatarios_email, assunto_email, mensagem_email)


def diretorio_json():
    return r"Token Sheets/token.json"
    # return "token.json"


def credentials_json():
    return "Token Sheets/secret.json"
    # return "credentials.json"


# Função que obtém a margem informada pelo usuário
def solicita_tabela_sheets(id_planilha, range_dados):
    """
    Solicita as informações do Google Sheet, guia de margens

    Returns:
    Valores: collection
    """
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"] #Acessa o google sheets

    # The ID and range of a sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = id_planilha
    SAMPLE_RANGE_NAME = range_dados

    creds = None

    # Faz o login da API do Google
    if os.path.exists(diretorio_json()):
        creds = Credentials.from_authorized_user_file(diretorio_json(), SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(diretorio_json(), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(diretorio_json(), 'w') as token:
            token.write(creds.to_json())

    # Faz a leitura e edição da planilha
    #try:
    service = build('sheets', 'v4', credentials=creds)

    # Ler informacoes do Google Sheets
    sheet = service.spreadsheets()
    # Lê a planilha através do .get, o .update altera informações
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    valores = result['values']

    # Retorna uma lista
    return valores


# Função para encontrar subprocessos do ChromeDriver
def find_chrome_processes(ppid):
    """
    Função para encontrar subprocessos do ChromeDriver

    Parameters:
    ppid: string

    Returns:
    chrome_pids: list
    """

    chrome_pids = []
    for proc in psutil.process_iter(['pid', 'ppid', 'name']):
        try:
            # Ajusta o nome do processo conforme necessário
            if proc.info['ppid'] == ppid and proc.info['name'].lower() in ['chrome', 'chrome.exe']:
                chrome_pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return chrome_pids


def verifica_intimacoes_bd(texto_extraido, numero_processo, data_disponibilizacao):
    sql = f"""SELECT texto_extraido, linha FROM "gilvanFrancisco".intimacoes WHERE numero_processo = {numero_processo} and data_disponibilizacao = '{str(data_disponibilizacao)}'"""

    return conecta_pg(sql=sql)


def excluir_linhas_sheet(aba_nome):
    # URL do Apps Script
    url = "https://script.google.com/macros/s/AKfycbzlSxEvxu67pUXv9hRYU4zn3cXOBmXxm1WxTFMckNQqLBnBxnxWIChNfpAhq3HnaVCV/exec"

    # Nome da aba que você quer manipular
    aba_nome = aba_nome

    # Parâmetros para a requisição GET
    params = {
        "action": "excluirLinhas",
        "abaNome": aba_nome
    }

    # Fazendo a requisição GET
    requests.get(url, params=params)


def enviar_backup():
    try:
        tabela = solicita_tabela_sheets(id_planilha="12xCoiJB925z-3seNWia7mJzSi_HE8ydpdzsFgfb74Y4", range_dados="Intimações!A1:K")

        try:
            for data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, teor, situacao in tabela:
                if "data de cadastro" not in str(data_cadastro).lower():
                    url = f"https://script.google.com/macros/s/AKfycbzJmWaP4oVQJgsyM263A_WjH_qKGT9ZMODGpqY4jvgJ6KFl9TQtQ2PKsX3ms9tUfioo/exec"
                    dados = dados = f"data_cadastro={data_cadastro}&data_disponibilizacao={data_disponibilizacao}&intimacao={intimacao}&data_inicio_prazo={data_inicio}&codigo={codigo}&comarca={comarca}&orgao={orgao}&numero_processo={numero_processo}&texto_extraido={texto_extraido}&teor={teor}&situacao={situacao}"

                    requests.get(f"{url}?{dados}")

        except:
            for data_cadastro, data_disponibilizacao, intimacao, codigo, comarca, orgao, numero_processo, texto_extraido, teor in tabela:
                if "data de cadastro" not in str(data_cadastro).lower():
                    url = f"https://script.google.com/macros/s/AKfycbzJmWaP4oVQJgsyM263A_WjH_qKGT9ZMODGpqY4jvgJ6KFl9TQtQ2PKsX3ms9tUfioo/exec"
                    dados = dados = f"data_cadastro={data_cadastro}&data_disponibilizacao={data_disponibilizacao}&intimacao={intimacao}&data_inicio_prazo={data_inicio}&codigo={codigo}&comarca={comarca}&orgao={orgao}&numero_processo={numero_processo}&texto_extraido={texto_extraido}&teor={teor}&situacao=Não excluído"

                    requests.get(f"{url}?{dados}")

        excluir_linhas_sheet(aba_nome="Intimações")

    except Exception as e:
        print(f"Erro ao enviar os dados para o backup: {e}")
        pass


def get_geckodriver_version():
    """
    Retorna a tag da versão mais recente do GeckoDriver usando a API do GitHub.
    """
    url = "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['tag_name']
    else:
        raise Exception("Não foi possível obter a versão mais recente do GeckoDriver.")


def baixar_geckodriver():
    """
    Baixa e extrai o GeckoDriver mais recente para o sistema.
    """
    # Obtém a versão mais recente do GeckoDriver
    geckodriver_version = get_geckodriver_version()
    
    # Monta a URL para download
    url = f"https://github.com/mozilla/geckodriver/releases/download/{geckodriver_version}/geckodriver-{geckodriver_version}-linux64.tar.gz"
    download_path = "/tmp/geckodriver.tar.gz"
    
    # Baixa o arquivo
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Erro ao baixar o GeckoDriver.")
    with open(download_path, "wb") as file:
        file.write(response.content)
    
    # Extrai o arquivo para /usr/local/bin/
    subprocess.run(["tar", "-xvzf", download_path, "-C", "/usr/local/bin/"], check=True)
    os.remove(download_path)

    print("GeckoDriver baixado e instalado com sucesso!")


def baixar_chromedriver():
    """
    Baixa e extrai o chromedriver mais recente.
    """
    # Supondo que você tenha o ChromeDriver já baixado e no local correto
    chromedriver_path = "/usr/local/bin/chromedriver"

    # Verifique se o chromedriver está no diretório correto
    if not Path(chromedriver_path).exists():
        print("Chromedriver não encontrado no caminho especificado.")
        raise Exception("Chromedriver não encontrado!")
    
    # Caso tenha o chromedriver, garanta que ele tem permissões de execução
    os.chmod(chromedriver_path, 0o755)  # Dá permissão de execução
    
    print("Chromedriver encontrado!")


def acessa_navegador(caminho_arquivo):
    print("Entrando no bloco de acesso do navegador...")

    # Verifica se o chromedriver está instalado
    chromedriver_path = "/usr/local/bin/chromedriver"
    if not Path(chromedriver_path).exists():
        print("Chromedriver não encontrado, baixando a versão correta...")
        baixar_chromedriver()  # Implementação de baixar_chromedriver não foi dada, mas você pode usá-la se necessário
    else:
        print("Chromedriver encontrado!")

    print("Iniciando options!")

    # Configurações para o Chrome
    options = Options()

    print("Options finalizado!")

    # sys.stdout = open(caminho_arquivo, 'w')  # Redireciona a saída para um arquivo
    # user_agent = ("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  # "(KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36")
    options.add_argument('--headless')  # Executa o Chrome em modo headless
    options.add_argument("--disable-gpu")
    options.add_argument('--no-sandbox')  # Necessário para rodar o Chrome em ambientes sem display
    options.add_argument('--remote-debugging-port=9222')  # Para o Chrome rodar em modo headless sem erros
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    # options.set_preference("general.useragent.override", user_agent)
    options.add_argument('--ignore-certificate-errors')

    print("Iniciando o serviço do Chrome...")

    # Define o serviço do ChromeDriver
    servico = ChromeService(executable_path=chromedriver_path)

    print("Iniciando o Chrome...")

    try:
        navegador = webdriver.Chrome(options=options, service=servico)
    except Exception as e:
        print(f"Erro ao iniciar o Chrome: {e}")
        # return None, None

    # navegador.maximize_window()

    # Obtém o PID do processo do Chrome
    chrome_pid = servico.process.pid

    # Função fictícia para encontrar subprocessos do Chrome
    chrome_pids = find_chrome_processes(chrome_pid)

    print(f"Navegador: {navegador}")

    return navegador, chrome_pids


    # ### FIREFOX
    # print("Entrando no bloco de acesso do navegador...")


    # # Verifica se o geckodriver está instalado
    # geckodriver_path = "/usr/local/bin/geckodriver"
    # if not Path(geckodriver_path).exists():
    #     print("GeckoDriver não encontrado, baixando a versão correta...")
    #     baixar_geckodriver()
    # else:
    #     print("GeckoDriver encontrado!")

    # print("Iniciando options!")

    # # sys.stdout = open(caminho_arquivo, 'w')  # Redireciona a saída para um arquivo
    # # user_agent = ("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    #             # "(KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36")
    # options = FirefoxOptions()
    # options.headless = True
    # options.binary_location = "/usr/bin/firefox"  # Força o caminho do Firefox
    # options.add_argument("--width=1920")
    # options.add_argument("--height=1080")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--ignore-certificate-errors")
    
    # print("Options finalizado!")

    # print("Iniciando o serviço do Firefox...")

    # # Define o serviço do FirefoxDriver
    # servico = FirefoxService(executable_path=geckodriver_path)

    # print("Iniciando o Firefox...")

    # try:
    #     navegador = webdriver.Firefox(options=options, service=servico)
    # except Exception as e:
    #     print(f"Erro ao iniciar o Firefox: {e}")

    # # navegador.maximize_window()

    # # Obtém o PID do processo do Firefox e encontra subprocessos
    # firefox_pid = servico.process.pid
    # chrome_pids = find_chrome_processes(firefox_pid)

    # print(f"Navegador: {navegador}")

    # return navegador, chrome_pids


def acessa_site():
    try:
        #Envio dos e-mails de erro
        destinatarios_email = []
        destinatarios_email.append('nicolaspn09@gmail.com')
        # destinatarios_email.append('advogados@gilvanfrancisco.adv.br')

        assunto_email = "Intimações"

        mensagem = f"Olá!<br><br>O robô iniciou!"

        envia_email(mensagem_email=mensagem, destinatarios_email=destinatarios_email, assunto_email=assunto_email)

        # Envia os dados para o backup
        enviar_backup()

        # Obtém os dados do ambiente
        load_dotenv()

        # Obtém os dados do ambiente
        usuario = os.getenv("LOGIN")
        senha = os.getenv("SENHA")

        print("Acessando navegador...")

        # tabela_sheets = solicita_tabela_sheets(id_planilha="12xCoiJB925z-3seNWia7mJzSi_HE8ydpdzsFgfb74Y4", range_dados="Intimações!A1:I")

        navegador, firefox_pids = acessa_navegador(caminho_arquivo="Log/Log.txt")
        # navegador, firefox_pids = acessa_navegador(caminho_arquivo=r"C:\Users\Nícolas Nasário\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Gilvan Francisco\Publicacoes Online\Log\Log.txt")

        url = "https://publicacoesonline.com.br/"

        navegador.get(url=url)

        efetua_login(navegador=navegador, usuario=usuario, senha=senha)

        boolean_intimacoes = acessa_intimacoes(navegador=navegador)

        if boolean_intimacoes == True:
            verifica_intimacoes(navegador=navegador)

        
        envia_email_final()

        print("Finalizou o processo!")


    except Exception as e:
        #Envio dos e-mails de erro
        destinatarios_email = []
        destinatarios_email.append('nicolaspn09@gmail.com')
        # destinatarios_email.append('advogados@gilvanfrancisco.adv.br')

        assunto_email = "Robô Processos"

        mensagem = f"Olá!<br><br>Há erro no processo do Gilvan!<br><br>Erro: <strong>{e}</strong>"

        envia_email(mensagem_email=mensagem, destinatarios_email=destinatarios_email, assunto_email=assunto_email)

    finally:
        if navegador:
            navegador.quit()


def efetua_login(navegador, usuario, senha):
    ### Propaganda
    try:
        print("Buscando propaganda")
        # Espera o elemento de Propaganda
        elemento_propaganda = WebDriverWait(navegador, 5).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[7]/div[4]/div/div/div/div/div/div/div")))

        if elemento_propaganda.is_displayed():
            try:
                print("Propaganda encontrada")
                # Verifica se o elemento está carregado na página
                botao_propaganda = navegador.find_element(By.XPATH, "/html/body/div[7]/div[4]/div/div/div/div/div/div/div")

                # Clica nos botão por Javascript
                navegador.execute_script("arguments[0].click();", botao_propaganda)
            except:
                print("Propaganda não encontrada")
                pass
    
    except:
        pass

    time.sleep(0.5)

    print("Efetuando login")

    ### Logar
    try:
        print("Botão login 1")
        # Espera o elemento de logar
        WebDriverWait(navegador, 15).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/header/nav/div/div/ul/li[8]/a")))

        # Verifica se o elemento está carregado na página
        botao_login = navegador.find_element(By.XPATH, "/html/body/div[2]/header/nav/div/div/ul/li[8]/a")
    except:
        print("Botão login 2")
        # Espera o elemento de logar
        WebDriverWait(navegador, 15).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/header/nav/div/div/ul/li[8]/a")))

        # Verifica se o elemento está carregado na página
        botao_login = navegador.find_element(By.XPATH, "/html/body/div[3]/header/nav/div/div/ul/li[8]/a")    

    # Clica nos botão por Javascript
    navegador.execute_script("arguments[0].click();", botao_login)

    print("UF")

    ### UF    
    # Esperar até que o combobox esteja presente
    combobox = WebDriverWait(navegador, 60).until(EC.presence_of_element_located((By.ID, "oab_uf")))

    # Aguarda um tempo
    time.sleep(0.5)

    print("UF combobox")

    # Criar um objeto Select
    # select = Select(combobox)

    # print(f"UF select: {select}")

    # Seleciona o valor desejado (exemplo: "1" ou o valor correspondente à UF)
    # select.select_by_value("1")

    # Cria um objeto Select
    select = Select(combobox)

    # Lista as opções disponíveis
    opcoes = [option.get_attribute("value") for option in select.options]
    print("Opções disponíveis no combobox:", opcoes)

    navegador.execute_script("""
    var select = document.getElementById('oab_uf');
    for (var i = 0; i < select.options.length; i++) {
        if (select.options[i].value === '1') {
            select.selectedIndex = i;
            // Dispara o evento change
            var event = new Event('change', { bubbles: true });
            select.dispatchEvent(event);
            break;
        }
    }
    """)
    time.sleep(1)
    valor_selecionado = navegador.execute_script("return document.getElementById('oab_uf').value;")
    console_msg = "Valor selecionado via JS (iterando): " + valor_selecionado
    print(console_msg)

    # Aguarda um tempo
    time.sleep(0.3)

    valor_selecionado = navegador.execute_script("return document.getElementById('oab_uf').value;")
    print("Valor selecionado:", valor_selecionado)

    # Aguarda um tempo
    time.sleep(0.3)

    print("Usuário")

    ### Usuário
    # Espera o elemento de usuário
    WebDriverWait(navegador, 60).until(EC.presence_of_element_located((By.ID, "adv_oab")))

    # Aguarda um tempo
    time.sleep(0.3)

    # Verifica se o elemento está carregado na página
    # navegador.find_element(By.ID, "adv_oab").send_keys(str(usuario))

    navegador.execute_script("""
    var campo = document.getElementById('adv_oab');
    campo.value = arguments[0];
    campo.dispatchEvent(new Event('input'));
    campo.dispatchEvent(new Event('change'));
    """, str(usuario))

    # Aguarda um tempo
    time.sleep(0.3)

    print("Senha")

    ### Senha
    # Espera o elemento de senha
    WebDriverWait(navegador, 60).until(EC.presence_of_element_located((By.ID, "adv_senha")))

    # Aguarda um tempo
    time.sleep(0.3)

    # Verifica se o elemento está carregado na página
    # navegador.find_element(By.ID, "adv_senha").send_keys(str(senha))
    navegador.execute_script("""
    var campo = document.getElementById('adv_senha');
    campo.value = arguments[0];
    campo.dispatchEvent(new Event('input'));
    campo.dispatchEvent(new Event('change'));
    """, str(senha))

    # Aguarda um tempo
    time.sleep(0.3)

    print("Logar")

    ### Logar
    try:
        print("Elemento logar 1")
        # Espera o elemento de logar
        WebDriverWait(navegador, 5).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/header/nav/div/div/ul/li[8]/div/div[2]/div[1]/form/div[3]/input")))

        # Verifica se o elemento está carregado na página
        elemento_logar = navegador.find_element(By.XPATH, "/html/body/div[2]/header/nav/div/div/ul/li[8]/div/div[2]/div[1]/form/div[3]/input")
    except:
        print("Elemento logar 2")
        # Espera o elemento de logar
        WebDriverWait(navegador, 5).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/header/nav/div/div/ul/li[8]/div/div[2]/div[1]/form/div[3]/input")))

        # Verifica se o elemento está carregado na página
        elemento_logar = navegador.find_element(By.XPATH, "/html/body/div[3]/header/nav/div/div/ul/li[8]/div/div[2]/div[1]/form/div[3]/input")

    # Clica nos botão por Javascript
    navegador.execute_script("arguments[0].click();", elemento_logar)

    # Aguarda um tempo
    time.sleep(3)

    print("Login efetuado!")


def acessa_intimacoes(navegador):
    ### Logar
    # Espera o elemento de intimações
    WebDriverWait(navegador, 60).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[3]/div/nav/ul/li[2]/a/div/div[2]/span")))

    for linha in range(1, 10):
        # Verifica se o elemento está carregado na página
        botao = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[3]/div/nav/ul/li[{linha}]/a/div/div[2]/span")
        valor = navegador.execute_script("return arguments[0].innerText;", botao)

        print(valor)

        if "intimações" in str(valor).lower():
            # Verifica se o elemento está carregado na página
            valor = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[3]/div/nav/ul/li[{linha}]/a/div/div[2]/span")

            # Clica nos botão por Javascript
            navegador.execute_script("arguments[0].click();", valor)

            return True
        
    return False


def verifica_intimacoes(navegador):
    ### Obtém a data atual
    data_atual = obtem_data()

    ### Tabela de intimações
    # Espera o elemento de intimações
    tabela_intimacoes = WebDriverWait(navegador, 60).until(EC.presence_of_element_located((By.ID, "tabelaPublicacoes")))

    linhas_tabela = tabela_intimacoes.find_elements(By.TAG_NAME, 'tr')

    quantidade_linhas = len(linhas_tabela)

    linha_atual = 0

    for i in range(1, 10):
        for linha in range(1, quantidade_linhas + 25):
            linha_atual += 1

            if linha_atual > quantidade_linhas:
                break

            try:
                data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido = extrair_dados_intimacoes(navegador=navegador, linha=linha_atual)

                tabela_sql = verifica_intimacoes_bd(texto_extraido=texto_extraido, numero_processo=numero_processo, data_disponibilizacao=data_disponibilizacao)

                print(len(tabela_sql))           

                
                # if len(tabela_sql) == 0:
                if data_atual in data_disponibilizacao and len(tabela_sql) == 0:
                    texto1 = executa_gemini_extrai_teor(texto_extraido)
                    print(f"Texto1: {texto1}")
                    # texto1 = executa_groq_extrai_teor(texto_extraido)

                    informar_dados_banco(data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, texto1, "Não excluído", linha_atual)

                    time.sleep(59)

                # elif len(tabela_sql) > 0:
                elif data_atual in data_disponibilizacao and len(tabela_sql) > 0:
                    for texto_extraido_tabela, linha_tabela_sql in tabela_sql:
                        texto1 = executa_gemini_extrai_teor(texto_extraido)
                        # texto1 = executa_groq_extrai_teor(texto_extraido)

                        time.sleep(20)
                        
                        texto2 = executa_gemini_extrai_teor(texto_extraido_tabela)
                        # texto2 = executa_groq_extrai_teor(texto_extraido_tabela)

                        time.sleep(20)

                        retorno_gemini = executa_gemini_texto(texto=texto1, texto2=texto2)
                        # retorno_gemini = executa_groq_texto(texto=texto1, texto2=texto2)

                        if "sim" in str(retorno_gemini).lower():
                            if "texto1" in str(retorno_gemini).lower():
                                # print(f"Excluir linha: {linha}")
                                excluir_intimacao(navegador=navegador, linha=linha_atual)

                                informar_dados_banco(data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, texto1, "Excluído", linha_atual)

                                linha_atual -= 1

                                break

                            elif "texto2" in str(retorno_gemini).lower():
                                # print(f"Excluir linha: {linha_tabela_sql}")
                                excluir_intimacao(navegador=navegador, linha=linha_tabela_sql)

                                informar_dados_banco(data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, texto1, "Excluído", linha_atual)

                                linha_atual -= 1

                                break

                            elif "empresas" in str(retorno_gemini).lower():
                                informar_dados_banco(data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, texto1, "Não Excluído", linha_atual)

                            else:
                                informar_dados_banco(data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, texto1, "Não Excluído", linha_atual)

                        else:
                            informar_dados_banco(data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, texto1, "Não excluído", linha_atual)

                        time.sleep(20)

                elif data_atual not in data_disponibilizacao:
                    return True
                
            except Exception as e:
                print(f"Erro no bloco de verificação das intimações: {e}")


        # Verifica se o elemento está carregado na página
        botao_proxima_pagina = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/nav/ul/li[4]/a")

        # Clica nos botão por Javascript
        navegador.execute_script("arguments[0].click();", botao_proxima_pagina)

        linha_atual = 0

        time.sleep(5)


def extrair_dados_intimacoes(navegador, linha):
    WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[4]")))

    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[4]")
    data_cadastro = navegador.execute_script("return arguments[0].innerText;", elemento)
    
    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[5]")
    data_disponibilizacao = navegador.execute_script("return arguments[0].innerText;", elemento)

    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[6]")
    intimacao = navegador.execute_script("return arguments[0].innerText;", elemento)

    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[7]")
    data_inicio = navegador.execute_script("return arguments[0].innerText;", elemento)

    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[8]")
    codigo = navegador.execute_script("return arguments[0].innerText;", elemento)

    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[9]")
    comarca = navegador.execute_script("return arguments[0].innerText;", elemento)

    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[10]")
    orgao = navegador.execute_script("return arguments[0].innerText;", elemento)

    elemento = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[11]")
    numero_processo = navegador.execute_script("return arguments[0].innerText;", elemento)

    # Verifica se o elemento está carregado na página
    elemento_numero_processo = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[11]")

    # Faz scroll até o elemento para garantir que ele esteja visível
    navegador.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", elemento_numero_processo)

    time.sleep(0.5)

    # Clica nos botão por Javascript
    navegador.execute_script("arguments[0].click();", elemento_numero_processo)

    time.sleep(0.5)

    # Espera aparecer o elemento de texto extraído
    WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.ID, f"conteudoPublicacao")))

    elemento = navegador.find_element(By.ID, f"conteudoPublicacao")
    texto_extraido = navegador.execute_script("return arguments[0].innerText;", elemento)

    time.sleep(0.5)

    # Verifica se o elemento está carregado na página
    elemento_fechar_texto = navegador.find_element(By.ID, f"btnFecharModal")

    # Clica nos botão por Javascript
    navegador.execute_script("arguments[0].click();", elemento_fechar_texto)

    WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[4]")))

    time.sleep(0.5)

    print(f"Data cadastro: {data_cadastro}")
    print(f"Texto extraído: {texto_extraido[:20]}")

    return data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido


def informar_dados_banco(data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, teor, situacao, linha):
    data_cadastro = str(data_cadastro).replace("'", "")
    data_disponibilizacao = str(data_disponibilizacao).replace("'", "")
    intimacao = str(intimacao).replace("'", "")
    data_inicio = str(data_inicio).replace("'", "")
    codigo = str(codigo).replace("'", "")
    comarca = str(comarca).replace("'", "")
    orgao = str(orgao).replace("'", "")
    numero_processo = str(numero_processo).replace("'", "")
    texto_extraido = str(texto_extraido).replace("'", "")
    teor = str(teor).replace("'", "")
    situacao = str(situacao).replace("'", "")

    url = f"https://script.google.com/macros/s/AKfycbwBsSTMEKRFkHUoCXjijdMiyIehW1OtERNorK94m1XHEb5Mw6krNefpLYLxfOt7FC5M/exec"
    dados = f"data_cadastro={data_cadastro}&data_disponibilizacao={data_disponibilizacao}&intimacao={intimacao}&data_inicio_prazo={data_inicio}&codigo={codigo}&comarca={comarca}&orgao={orgao}&numero_processo={numero_processo}&texto_extraido={texto_extraido}&teor={teor}&situacao={situacao}"

    requests.get(f"{url}?{dados}")

    texto_extraido = texto_extraido.replace("'", "")

    sql = f"""INSERT INTO "gilvanFrancisco".intimacoes (data_cadastro, data_disponibilizacao, intimacao, data_inicio_prazo, codigo, comarca, orgao, numero_processo, texto_extraido, situacao, teor, linha) VALUES('{data_cadastro}', '{data_disponibilizacao}', '{intimacao}', '{data_inicio}', {codigo}, '{comarca}', '{orgao}', {numero_processo}, '{texto_extraido}', '{situacao}', '{teor}', {int(linha)})"""

    conecta_pg_insert(sql=sql)


def excluir_intimacao(navegador, linha):
    # Verifica se o elemento está carregado na página
    elemento_numero_processo = navegador.find_element(By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[11]")

    # Clica nos botão por Javascript
    navegador.execute_script("arguments[0].click();", elemento_numero_processo)

    time.sleep(0.5)

    for i in range(10, 20):
        try:
            # Verifica se o elemento está carregado na página
            elemento_numero_processo = navegador.find_element(By.XPATH, f"/html/body/div[{i}]/div/div/div[2]/div[1]/button[5]")
        
        except:
            pass

    # Clica nos botão por Javascript
    navegador.execute_script("arguments[0].click();", elemento_numero_processo)

    time.sleep(0.5)

    try:
        WebDriverWait(navegador, 5).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[11]/div[7]/div/button")))

        # Verifica se o elemento está carregado na página
        elemento_confirmacao_exclusao = navegador.find_element(By.XPATH, f"/html/body/div[11]/div[7]/div/button")

        # Clica nos botão por Javascript
        navegador.execute_script("arguments[0].click();", elemento_confirmacao_exclusao)

    except:
        pass

    time.sleep(0.5)

    try:
        WebDriverWait(navegador, 5).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[11]/div[7]/div/button")))

        # Verifica se o elemento está carregado na página
        elemento_confirmacao_exclusao = navegador.find_element(By.XPATH, f"/html/body/div[11]/div[7]/div/button")

        # Clica nos botão por Javascript
        navegador.execute_script("arguments[0].click();", elemento_confirmacao_exclusao)

    except:
        pass

    time.sleep(0.5)
    
    try:
        # Verifica se o elemento está carregado na página
        elemento_fechar_texto = navegador.find_element(By.ID, f"btnFecharModal")

        # Clica nos botão por Javascript
        navegador.execute_script("arguments[0].click();", elemento_fechar_texto)
    
    except:
        pass

    time.sleep(0.5)

    WebDriverWait(navegador, 10).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[3]/div[4]/div/div[2]/div/div[2]/div/div[2]/div/div/table/tbody/tr[{linha}]/td[4]")))

    time.sleep(0.5)


def verifica_intimacoes_finais_bd(data_disponibilizacao):
    sql = f"""SELECT * FROM "gilvanFrancisco".intimacoes WHERE data_disponibilizacao = '{str(data_disponibilizacao)}'"""

    return conecta_pg(sql=sql)


def envia_email_final():
    ### Obtém a data atual
    data_atual = obtem_data()

    tabela_sql = verifica_intimacoes_finais_bd(data_disponibilizacao=data_atual)

    tabela_secoes = []
    tabela_secoes_excluida = []
    
    for pk_intimacao, data_cadastro, data_disponibilizacao, intimacao, data_inicio, codigo, comarca, orgao, numero_processo, texto_extraido, situacao, teor, linha in tabela_sql:
        if "não" in str(situacao).lower():
            tabela_secoes.append(f"""<tr><td>{data_disponibilizacao}</td><td>{intimacao}</td><td>{codigo}</td><td>{comarca}</td><td>{numero_processo}</td><td>{teor}</td><td>{situacao}</td>""")
        else:
            tabela_secoes_excluida.append(f"""<tr><td>{data_disponibilizacao}</td><td>{intimacao}</td><td>{codigo}</td><td>{comarca}</td><td>{numero_processo}</td><td>{teor}</td><td>{situacao}</td>""")

    corpo_do_email = ''.join(tabela_secoes) #Converte para uma linha só em formato de string
    corpo_do_email_excluida = ''.join(tabela_secoes_excluida) #Converte para uma linha só em formato de string

    # Envio dos e-mails de erro
    destinatarios_email = []
    destinatarios_email.append('nicolaspn09@gmail.com')
    destinatarios_email.append('advogados@gilvanfrancisco.adv.br')

    assunto_email = "Finalização da Análise de Processos"

    mensagem = f"""
    Olá!<br><br>
    O código finalizou a análise das intimações!<br><br>
    Segue abaixo a tabela com as intimações analisadas:<br><br>
    
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Análise Processos</title>
        <style>
        body {{font-family: Arial, sans-serif;
            line-height: 1.6;
        }}
        h1 {{
            font-size: 22px;
            font-weight: bold;
        }}
        strong {{
            font-weight: bold;
        }}
        em {{
            font-style: italic;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        table, th, td {{
            border: 1px solid black;
        }}
        th, td {{
            padding: 8px;
            text-align: center;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        </style>
    </head>
    <p><strong>ITENS NÃO EXCLUÍDOS</strong></p><br>
    <body>
        <table>
                <tr>
                    <th>Data de Disponibilização</th>
                    <th>Intimação</th>
                    <th>Código</th>
                    <th>Comarca</th>
                    <th>Número do processo</th>
                    <th>Teor</th>
                    <th>Situação da Análise (Robô)</th>
                </tr>
                    {corpo_do_email}
        </table><br><br>
        <p><strong>ITENS EXCLUÍDOS</strong></p><br>
        <table>
                <tr>
                    <th>Data de Disponibilização</th>
                    <th>Intimação</th>
                    <th>Código</th>
                    <th>Comarca</th>
                    <th>Número do processo</th>
                    <th>Teor</th>
                    <th>Situação da Análise (Robô)</th>
                </tr>
                    {corpo_do_email_excluida}
        </table><br>
    <p>Atenciosamente,</p>
    <p>Equipe de RPA Nex.AI.</p><br>
    </body>
    </html>
    """

    envia_email(mensagem_email=mensagem, destinatarios_email=destinatarios_email, assunto_email=assunto_email)

if __name__ == "__main__":
    acessa_site()