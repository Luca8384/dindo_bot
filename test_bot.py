# test_bot.py
import requests
from dados_bot import TOKEN, CHAT_ID

def testar_conexao():
    print("🔄 Tentando enviar mensagem de teste...")
    texto = "✅ O Dindo Bot está conectado com sucesso!"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={texto}"
    
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            print("🚀 Sucesso! Verifique seu Telegram.")
        else:
            print(f"❌ Erro {resposta.status_code}: {resposta.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    testar_conexao()