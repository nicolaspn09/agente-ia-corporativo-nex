import sys
import requests

sys.path.append(r"C:\Users\Nícolas Nasário\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos")
from Classes.GoogleSheets.GoogleSheets.GoogleSheets import GoogleSheets




def preenche_linha(linha, informacao, numero=None):
    # url = f"https://script.google.com/macros/s/AKfycbziWaci7VKi2GHWXZs2QyeoKt1YrtOfnjdcs3TjClAIn2NawA5C9AKfJ-pSH4rnX0iNEw/exec?linha={linha}&status={informacao}"
    url = f"https://script.google.com/macros/s/AKfycbwq_gNcLAJUM6mEQ1os0KT7WbHnKWqPLk9RBwjSQo84klHeLSdeECBBlljuZZsRDA4O6Q/exec?linha={linha}&status={informacao}"

    requests.get(url)


def check_whatsapp(numero):
    url = "http://rpa-evolution-api.2hswyv.easypanel.host/chat/whatsappNumbers/Nexus"

    payload = { "numbers": [f"{numero}"] }
    headers = {
        "apikey": "429683C4C977415CAAFCCE10F7D57E11",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


id = "1hRfFqUdPDQPIbn7lvo_kUB59mqr1m9LuQV1kWK50BLE"
range = "Novos Números!A2:E"


sheets = GoogleSheets(id, range, r"C:\Users\Nícolas Nasário\OneDrive\Cursos online\Treinamento Python - Hashtag\Códigos\Nex.ai - Empresa\Formus\Envio Whats\token.json")
tabela = sheets.solicita_tabela()

linha = 2

for i in tabela:
    status = i[2]
    if status == "" or status == "INATIVO":
        retorno = check_whatsapp(numero=i[1])
        retorno = retorno[0]["exists"]

        if retorno:
            retorno = "ATIVO"
        else:
            numero = i[0]
            numero = numero[:4] + "9" + numero[4:]
            retorno = check_whatsapp(numero=i[0])
            retorno = retorno[0]["exists"]

            if retorno:
                retorno = "ATIVO"
            else:
                numero = i[0]
                numero = numero[:4] + numero[5:]
                retorno = check_whatsapp(numero=i[0])
                retorno = retorno[0]["exists"]

                if retorno:
                    retorno = "ATIVO"
                else:
                    retorno = "INATIVO"

        preenche_linha(linha, informacao=retorno)
        
    linha += 1