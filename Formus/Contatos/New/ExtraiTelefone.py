import re
import pandas as pd

# Caminhos dos dois arquivos
file_marcelo = r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\Contatos Marcelo atual 14-08-25.csv"
file_paulo   = r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\Contatos Paulo atual 14-08-25.csv"

# Saída única
output_path = r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\CONCATENADO_2.xlsx"

def extrair_contatos(file_path):
    """Extrai nomes e telefones de um arquivo vCard exportado (CSV da agenda)."""
    contatos = []
    nome_atual = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:  # pula linhas vazias
                continue

            if line.startswith("FN:"):  # Nome
                nome_atual = line.replace("FN:", "").replace(";", "").strip()

            elif line.startswith("TEL") and nome_atual:  # Telefone
                telefone = line.split(":")[-1]
                telefone = re.sub(r";+", "", telefone).strip()  # remove ;;;
                telefone = telefone.replace("-", "").replace("+", "").replace(" ", "")
                if len(telefone) > 6:
                    contatos.append({"Nome": nome_atual, "Telefone": telefone})
    return pd.DataFrame(contatos)

# Extrair dos dois arquivos
df_marcelo = extrair_contatos(file_marcelo)
df_paulo   = extrair_contatos(file_paulo)

# Juntar os dois em um só DataFrame
df = pd.concat([df_marcelo, df_paulo], ignore_index=True)

# Normalizar telefones
def normalizar_numero(num):
    if not isinstance(num, str):
        return num
    num = num.strip()
    if num.startswith("021"):
        return "55" + num[3:]
    elif num.startswith("21"):
        return "55" + num[2:]
    elif num.startswith("048"):
        return "55" + num[3:]
    elif num.startswith("41"):
        return "55" + num[2:]
    return num

df["Telefone"] = df["Telefone"].apply(normalizar_numero)

# Remover duplicados (baseado apenas no telefone)
df = df.drop_duplicates(subset=["Telefone"], keep="first")

# Exportar tudo em um só Excel
df.to_excel(output_path, index=False)

print(f"Arquivo unificado salvo em: {output_path}")