import xml.etree.ElementTree as ET
from collections import defaultdict
from dotenv import load_dotenv
import os
from groq import Groq
import psycopg2
import time


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
        model="deepseek-r1-distill-llama-70b",
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
        model="deepseek-r1-distill-llama-70b",
        temperature=0,
        stream=False,
    )

    return chat_completion.choices[0].message.content


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


def obtem_data():
    """
    Obtem a data atual

    Returns:
    data_atual: string
    """

    # Obtem a data atual
    data_atual = time.strftime("%d/%m/%Y")

    return data_atual


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


def verifica_intimacoes_bd(texto_extraido, numero_processo, data_disponibilizacao):
    sql = f"""SELECT texto_extraido, linha FROM "gilvanFrancisco".intimacoes WHERE numero_processo = {numero_processo} and data_disponibilizacao = '{str(data_disponibilizacao)}'"""

    return conecta_pg(sql=sql)


def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    records = []
    for row in root.findall("row"):
        record = {child.tag: child.text.strip() if child.text else "" for child in row}
        records.append(record)
    
    return records


def remove_duplicates(records):
    unique_records = []
    seen = set()
    
    for record in records:
        key = (record["nome"], record["oab"], record["processo"], record["texto"])
        if key not in seen:
            seen.add(key)
            unique_records.append(record)
    
    return unique_records


def generate_xml(records, output_file):
    root = ET.Element("root")
    
    for record in records:
        row = ET.SubElement(root, "row")
        for key, value in record.items():
            element = ET.SubElement(row, key)
            element.text = f"<![CDATA[ {value} ]]>"
    
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


def analisa_dados(file_path):
    records = parse_xml(file_path)
    
    return records


if __name__ == "__main__":
    ### Obtém a data atual
    data_atual = obtem_data()

    file_path = rf"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Gilvan Francisco\Publicacoes Online\XML\2_GILVAN_FRANCISCO_20_03_2025_14h35m11s_67DC51CFA1B36 3.xml"  # Substitua pelo caminho do arquivo XML
    
    records = analisa_dados(file_path)

    linha = 0

    for record in records:
        linha += 1

        nome, oab, codigo, processo, processo_antigo, data, data_publicacao, jornal, orgao, cidade, vara, pagina, texto = record.values()
        tabela_sql = verifica_intimacoes_bd(texto_extraido=texto, numero_processo=processo, data_disponibilizacao=data_publicacao)

        if data_atual in data_publicacao and len(tabela_sql) == 0:
            texto1 = executa_groq_extrai_teor(texto)

            informar_dados_banco(data, data_publicacao, processo, data_publicacao, codigo, "", orgao, processo, texto, texto1, "Não excluído", 1)