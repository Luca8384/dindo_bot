# main_bot.py
import ccxt
import time
import requests
from dados_bot import TOKEN, CHAT_ID, HOT_LIST
from indicadores import calcular_rsi, detectar_acumulo, calcular_dados_velas

exchange = ccxt.mexc()

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}"
    requests.get(url)

def check_logic(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=40)
        if not ohlcv: return

        # Usamos a função do arquivo indicadores.py
        preco, var, ratio, fechamentos = calcular_dados_velas(ohlcv)
        rsi_atual = calcular_rsi(fechamentos)
        is_acumulando, var_ac, r_vol_ac = detectar_acumulo(ohlcv)

        link = f"https://www.mexc.com/exchange/{symbol.replace('/', '_')}"

        # 1. Alerta de Acúmulo (Oportunidade Antecipada)
        if is_acumulando:
            msg = f"💎 ACÚMULO: {symbol}\n🤫 Var: {var_ac:.3f}%\n🐋 Vol: {r_vol_ac:.2f}x\n🔗 {link}"
            enviar_telegram(msg)

        # 2. Alerta de Entrada (Volume + Preço)
        elif ratio > 4.0 and var > 0.3 and rsi_atual < 65:
            msg = f"🚀 ENTRADA: {symbol}\n📈 +{var:.2f}%\n📊 Vol: {ratio:.2f}x\n🔗 {link}"
            enviar_telegram(msg)

        # 3. Alerta de Saída (RSI Alto)
        elif rsi_atual > 80:
            msg = f"⚠️ SAÍDA: {symbol}\n🚨 RSI: {rsi_atual:.1f}\n🔗 {link}"
            enviar_telegram(msg)

    except: pass

# --- LOOP PRINCIPAL ---
print("--- Robô Dindo Organizado Ativado ---")
while True:
    try:
        tickers = exchange.fetch_tickers()
        symbols = [t for t in tickers if t.endswith('/USDT')]
        top_100 = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:100]
        
        for s in top_100:
            check_logic(s)
            time.sleep(0.05)
    except:
        time.sleep(10)