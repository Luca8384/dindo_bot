import ccxt
import time
import requests
import os
from flask import Flask
from threading import Thread
# Importamos as funções que criamos no arquivo indicadores.py
from indicadores import calcular_rsi, detectar_acumulo, calcular_dados_velas

# ==========================================
# TRUQUE PARA RODAR GRÁTIS NO RENDER (Web Service)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "O Dindo Bot está operando!"

def run_web_server():
    # O Render exige que um Web Service escute em uma porta (8080)
    app.run(host='0.0.0.0', port=8080)

# Iniciamos o servidor web em uma linha separada para não travar o robô
Thread(target=run_web_server).start()
# ==========================================

# --- CONFIGURAÇÃO DE ACESSO ---
try:
    from dados_bot import TOKEN, CHAT_ID, HOT_LIST
    print("✅ Configurações locais carregadas.")
except ImportError:
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    HOT_LIST = ['AIF/USDT', 'RENDER/USDT', 'OORT/USDT', 'ONDO/USDT', 'DUSK/USDT']
    print("☁️ Configurações de Nuvem (Render) carregadas.")

# --- INICIALIZAÇÃO DA EXCHANGE ---
exchange = ccxt.mexc({'enableRateLimit': True})

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        requests.get(url, params=params)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def check_logic(symbol):
    """Análise técnica de cada moeda"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=40)
        if len(ohlcv) < 30: return

        preco_atual, variacao, ratio_vol, fechamentos = calcular_dados_velas(ohlcv)
        rsi_atual = calcular_rsi(fechamentos)
        is_acumulando, var_acumulo, ratio_acumulo = detectar_acumulo(ohlcv)

        link_mexc = f"https://www.mexc.com/exchange/{symbol.replace('/', '_')}"

        # 1. Alerta de Acúmulo
        if is_acumulando:
            msg = (f"💎 <b>ACÚMULO (BALEIAS)</b>\n"
                   f"🪙 Ativo: {symbol}\n"
                   f"🤫 Lateral: {var_acumulo:.3f}%\n"
                   f"🐋 Vol: {ratio_acumulo:.2f}x\n"
                   f"🔗 <a href='{link_mexc}'>Gráfico</a>")
            enviar_telegram(msg)

        # 2. Alerta de Entrada (Pico de Volume)
        elif ratio_vol > 5.0 and variacao > 0.4 and rsi_atual < 68:
            msg = (f"🚀 <b>PICO DE VOLUME</b>\n"
                   f"🪙 Ativo: {symbol}\n"
                   f"📈 Alta: +{variacao:.2f}%\n"
                   f"📊 Força: {ratio_vol:.2f}x\n"
                   f"🔗 <a href='{link_mexc}'>Gráfico</a>")
            enviar_telegram(msg)

        # 3. Alerta de Saída (Exaustão)
        elif rsi_atual > 83:
            msg = (f"⚠️ <b>SOBRECOMPRA (RSI)</b>\n"
                   f"🪙 Ativo: {symbol}\n"
                   f"🚨 RSI em {rsi_atual:.1f}\n"
                   f"🔗 <a href='{link_mexc}'>Gráfico</a>")
            enviar_telegram(msg)

    except:
        pass

# --- LOOP PRINCIPAL ---
print("🚀 Robô Dindo v5.0 iniciado!")
enviar_telegram("🤖 <b>Dindo Bot Online!</b>\nMonitorando Top 100 MEXC.")

while True:
    try:
        tickers = exchange.fetch_tickers()
        usdt_symbols = [s for s in tickers if s.endswith('/USDT')]
        
        # Filtra as 100 moedas com mais volume nas últimas 24h
        top_100 = sorted(usdt_symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:100]
        lista_final = list(set(top_100 + HOT_LIST))
        
        print(f"🔍 Escaneando {len(lista_final)} ativos...")

        for s in lista_final:
            check_logic(s)
            time.sleep(0.1)

        print("✅ Ciclo completo. Aguardando 1 minuto...")
        time.sleep(60)

    except Exception as e:
        print(f"Erro Loop: {e}")
        time.sleep(15)