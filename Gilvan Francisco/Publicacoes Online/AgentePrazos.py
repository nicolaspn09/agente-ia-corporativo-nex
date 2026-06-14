import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# LangChain & Groq
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# Calendário Brasileiro
from workalendar.america import Brazil

# --- CONFIGURAÇÕES DE CAMINHOS E AMBIENTE ---
caminho_projeto = r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Gilvan Francisco\Publicacoes Online"
sys.path.append(caminho_projeto)

# Importação do módulo de Banco do usuário
try:
    from ConectaBanco import ConectaBanco
except ImportError:
    print(f"ERRO CRÍTICO: Não foi possível importar 'ConectaBanco'. Verifique se o arquivo está em: {caminho_projeto}")
    sys.exit()

# Carregar variáveis de ambiente
load_dotenv(dotenv_path=os.path.join(caminho_projeto, ".env"))

# Configuração do caminho do Excel de saída
caminho_excel = os.path.join(caminho_projeto, r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Gilvan Francisco\Publicacoes Online\analise_intimacoes_v2.xlsx")


# --- 1. DEFINIÇÃO DA TOOL DE CALENDÁRIO ---
@tool
def calcular_vencimento_legal(data_evento: str, dias_prazo: int, tipo_contagem: str = "uteis") -> str:
    """
    Calcula a data final de um prazo processual brasileiro considerando feriados nacionais.
    Args:
        data_evento (str): Data da disponibilização ou publicação (DD/MM/AAAA ou AAAA-MM-DD).
        dias_prazo (int): Prazo em dias (ex: 5, 8, 15).
        tipo_contagem (str): 'uteis' (Padrão CPC/CLT) ou 'corridos'.
    """
    cal = Brazil()
    
    # Normalização da data
    try:
        if "/" in data_evento:
            dt_inicial = datetime.strptime(data_evento, "%d/%m/%Y").date()
        else:
            dt_inicial = datetime.strptime(data_evento, "%Y-%m-%d").date()
    except ValueError:
        return f"Erro: Data '{data_evento}' inválida. Use DD/MM/AAAA."

    # Lógica de Início: Publicação (D) -> Início Contagem (D+1 útil)
    # Assume-se que a IA envia a data de PUBLICAÇÃO.
    dia_inicio_contagem = cal.add_working_days(dt_inicial, 1)

    dia_atual = dia_inicio_contagem
    dias_contados = 0
    
    # Cálculo
    if tipo_contagem == "uteis":
        while dias_contados < dias_prazo:
            dia_atual += timedelta(days=1)
            if cal.is_working_day(dia_atual):
                dias_contados += 1
    else:
        # Prazos corridos
        dia_atual = dia_inicio_contagem + timedelta(days=dias_prazo)
        # Prorroga se cair em não útil
        if not cal.is_working_day(dia_atual):
            dia_atual = cal.add_working_days(dia_atual, 0)

    return f"{dia_atual.strftime('%d/%m/%Y')} ({dia_atual.strftime('%A')})"


# --- 2. CONFIGURAÇÃO DO AGENTE ---
def analisar_intimacao_com_agente(texto_intimacao):
    # Inicializa o LLM
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"), 
        model="llama-3.3-70b-versatile", # Modelo recomendado para lógica
        temperature=0
    )

    tools = [calcular_vencimento_legal]

    # Prompt do Sistema
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        Você é um assistente jurídico sênior (Controladoria).
        Sua função é EXTRAIR dados da intimação e usar a tool 'calcular_vencimento_legal' para obter a data final.
        
        PASSO A PASSO OBRIGATÓRIO:
        1. Identifique a LEI (CLT ou CPC).
        2. Identifique a DATA DE PUBLICAÇÃO (se houver apenas "Disponibilização", considere Publicação = dia útil seguinte).
        3. Identifique o PRAZO em dias (ex: 8 dias Recurso Ordinário, 15 dias Contestação/Apelação, 5 dias Embargos).
        4. CHAME A TOOL `calcular_vencimento_legal` com esses dados.
        5. Retorne APENAS um JSON estrito com o resumo, sem markdown code blocks.
        
        Formato de Saída (JSON):
        {{
            "tipo_processo": "...",
            "ato_processual": "...",
            "data_publicacao_base": "...",
            "prazo_dias": 0,
            "data_final_calculada": "RETORNO DA TOOL",
            "observacao": "..."
        }}
        """),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False) # Verbose False para limpar terminal

    try:
        response = agent_executor.invoke({"input": texto_intimacao})
        return response["output"]
    except Exception as e:
        return f"Erro na execução do agente: {str(e)}"


# --- 3. EXECUÇÃO PRINCIPAL (BANCO -> EXCEL) ---
def main():
    print("--- Iniciando Processamento de Intimações ---")
    
    # 3.1 Conexão com Banco
    # Selecionando 10 registros para teste de produção
    sql = """select * from "gilvanFrancisco".publicacoes order by 1 limit 10"""
    conexao = ConectaBanco(sql=sql)
    tabela = conexao.conecta_pg()

    resultados = []
    
    if not tabela:
        print("Nenhum dado retornado do banco.")
        return

    print(f"Foram encontrados {len(tabela)} registros. Iniciando análise...")

    # 3.2 Iteração
    # Desempacotamento exato da tupla conforme seu código original
    for (id, oab, codigo, processo, data, jornal, orgao, cidade, vara, pagina, texto, cod_advogado, cod_fase_processo, data_baixado, lido, cancelado, nome, nome_usuario, data_cancelamento, data_publicacao, cod_empresa, data_veiculacao, ano_publicacao, edicao_diario, descricao_diario, pagina_final, numero_cadastro, despacho_publicacao, publicacao_corrigida, oab_estado, cod_integracao, publicacao_exportada, idws, id_externo, numero_processo_cnj, esfera, data_divulgacao) in tabela:
        
        print(f"\nProcessando ID: {id}...")
        
        try:
            # Chama o Agente
            analise_json = analisar_intimacao_com_agente(texto)
            
            # Compila o resultado
            dados_resultado = {
                "ID": id,
                "Processo": processo,
                "Data Divulgacao": data_divulgacao,
                # "Texto Original": texto[:200] + "...", # Truncado para visualização no excel não ficar gigante
                "Texto Original": texto, # Truncado para visualização no excel não ficar gigante
                "Analise Agente": analise_json
            }
            
            resultados.append(dados_resultado)
            
            # 3.3 Salvamento Incremental (Segurança)
            df_temp = pd.DataFrame(resultados)
            df_temp.to_excel(caminho_excel, index=False)
            print(f" -> ID {id} salvo no Excel.")

        except Exception as e:
            print(f"ERRO no ID {id}: {e}")
            # Salva erro no excel também para não perder o rastro
            resultados.append({"ID": id, "Analise Agente": f"FALHA DE PROCESSAMENTO: {e}"})
            pd.DataFrame(resultados).to_excel(caminho_excel, index=False)

        # Delay para evitar Rate Limit do Groq (Ajustado para 2s, 59s é muito tempo se tiver volume)
        # Se sua conta for Tier Gratuito agressivo, aumente para 10s ou mantenha 59s.
        time.sleep(2) 

    print(f"\n--- Concluído. Arquivo salvo em: {caminho_excel} ---")

if __name__ == "__main__":
    main()