import pandas as pd
import re

# Caminho do arquivo CSV de entrada
file_path = r"C:\Users\Nícolas Nasário\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\New\Contatos_Consolidados (1).csv"

# Lê o CSV com separador correto
df = pd.read_csv(file_path, sep=";", encoding="utf-8")

# Função para normalizar número
def normalizar_numero(num):
    if pd.isna(num):
        return ""
    num = str(num)
    num = re.sub(r"\D", "", num)  # remove tudo que não for dígito

    # Normalização do número
    if num.startswith("55"):
        num_final = num
    elif num.startswith("21"):
        num_final = "55" + num[2:]
    else:
        # assume DDI 55 e DDD 48
        num_final = "5548" + num

    # Verifica o tamanho — se tiver mais de 12 caracteres, remove os dois últimos
    if len(num_final) > 12:
        num_final = num_final[:-3]

    return num_final

# Cria a nova coluna com os números normalizados
df["telefone_normalizado"] = df["telefone"].apply(normalizar_numero)

# Caminho de saída (Excel)
output_path = r"C:\Users\Nícolas Nasário\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\New\Contatos_normalizados (1).xlsx"

# Exporta para Excel
df.to_excel(output_path, index=False)

print(f"Arquivo com telefones normalizados salvo em: {output_path}")