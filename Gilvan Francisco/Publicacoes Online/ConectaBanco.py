import os
import psycopg2
from dotenv import load_dotenv

class ConectaBanco:
    def __init__(self, sql):
        self.sql = sql

    # Roda query para executar o MySQL
    def conecta_pg(self):
        """
        Roda query para executar o MySQL

        Parameters:
        Sql = string

        Returns:
        tabela_sql = datatable
        """
        load_dotenv(dotenv_path=r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Gilvan Francisco\Publicacoes Online\.env")

        host = os.getenv('HOST')
        database = os.getenv('DATABASE')
        user = os.getenv('USER_PG')
        password = os.getenv('PASSWORD')
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
        cursor.execute(self.sql)
        tabela_sql = cursor.fetchall()
        cursor.close()
        connection.close()

        # Retorna o resultado da consulta do SQL para o usuário
        return tabela_sql


    # Roda query para executar o MySQL
    def conecta_pg_insert(self):
        """
        Roda query para executar o MySQL

        Parameters: 
        sql = string
        """
        load_dotenv(dotenv_path=r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Gilvan Francisco\Publicacoes Online\.env")

        host = os.getenv('HOST')
        database = os.getenv('DATABASE')
        user = os.getenv('USER_PG')
        password = os.getenv('PASSWORD')
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
        cursor.execute(self.sql)
        connection.commit()
        cursor.close()
        connection.close()