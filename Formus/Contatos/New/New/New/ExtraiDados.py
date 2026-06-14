import pandas as pd
import re
import os

# === CONFIGURAÇÃO ===
# Caminhos dos arquivos CSV a serem processados
arquivos = [
    r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\New\New\contacts - Paulo.csv",
    r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\New\New\contacts - Marcelo.csv"
]

# === FUNÇÕES AUXILIARES ===

def limpar_numero(texto):
    """
    Limpa e formata o número no padrão +55XXXXXXXXXXX.
    Remove símbolos, espaços e prefixos indevidos como 021, 21 ou 0.
    """
    if not isinstance(texto, str):
        texto = str(texto)

    # Remove tudo que não for número
    num = re.sub(r'\D', '', texto)

    # Remove prefixos desnecessários (021, 21, etc.)
    num = re.sub(r'^(0*21|0*021|55*21)', '', num)

    # Garante que o número comece com +55
    if not num.startswith('55'):
        num = '55' + num

    return f'+{num}'


def extrair_nomes(row):
    """
    Constrói o nome da pessoa usando as colunas de nome.
    """
    partes = []
    for campo in ['First Name', 'Middle Name', 'Last Name']:
        val = row.get(campo, '')
        if pd.notna(val) and str(val).strip().lower() != 'nan':
            partes.append(str(val).strip())

    nome = ' '.join(partes).strip()

    # Se ainda não tiver nome, tenta outras colunas
    if not nome:
        for alt in ['File As', 'Nickname', 'Organization Name']:
            val = row.get(alt, '')
            if pd.notna(val) and str(val).strip():
                nome = str(val).strip()
                break

    return nome


# === PROCESSAMENTO ===

resultados = []

for caminho in arquivos:
    if not os.path.exists(caminho):
        print(f"⚠️ Arquivo não encontrado: {caminho}")
        continue

    # Tenta detectar o separador automaticamente
    try:
        df = pd.read_csv(caminho, encoding='utf-8', sep=None, engine='python', dtype=str)
    except Exception:
        df = pd.read_csv(caminho, encoding='latin1', sep=None, engine='python', dtype=str)

    print(f"🔍 Processando {caminho} — {len(df)} linhas")

    # Percorre todas as linhas
    for _, row in df.iterrows():
        nome = extrair_nomes(row)

        # Passa por todas as colunas da linha
        for col in df.columns:
            valor = row.get(col, '')
            if pd.isna(valor) or not str(valor).strip():
                continue

            texto = str(valor)

            # Encontra padrões de números de telefone
            candidatos = re.findall(r'[\+\d\(\)\-\s]{8,}', texto)

            for cand in candidatos:
                numero = limpar_numero(cand)
                # Filtra números muito curtos ou longos
                if 10 <= len(re.sub(r'\D', '', numero)) <= 15:
                    resultados.append({'Nome': nome, 'Número': numero})


# === RESULTADO FINAL ===

df_saida = pd.DataFrame(resultados).drop_duplicates().reset_index(drop=True)

# Caminho de saída
saida_path = r"C:\Users\nicol\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Contatos\New\New\New\contatos_formatados.xlsx"
df_saida.to_excel(saida_path, index=False)

print(f"✅ Extração concluída! {len(df_saida)} contatos salvos em:")
print(saida_path)