import os
import time
import ccxt
import telebot
import pandas as pd
import pandas_ta as ta

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = telebot.TeleBot(TOKEN)

# Inicializando as duas corretoras
exchanges = {
    'MEXC': ccxt.mexc(),
    'BINANCE': ccxt.binance()
}

SYMBOLS = ['SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT']
TIMEFRAME = '15m'
PERCENTUAL_STOP_MOVEL = 0.02
posicoes_abertas = {}

def buscar_dados(exchange_obj, symbol):
    try:
        # A Binance usa símbolos sem a barra em alguns casos, o ccxt trata isso
        ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=200)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Indicadores
        df['ema_200'] = ta.ema(df['close'], length=200)
        df['rsi'] = ta.rsi(df['close'], length=14)
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        df = pd.concat([df, adx], axis=1)
        df['vol_avg'] = ta.sma(df['volume'], length=20)
        
        return df
    except Exception as e:
        return None

def monitorar():
    print(f"📡 Varrendo MEXC e Binance... {time.strftime('%H:%M:%S')}")
    
    for symbol in SYMBOLS:
        for ex_name, ex_obj in exchanges.items():
            df = buscar_dados(ex_obj, symbol)
            if df is None or df.empty: continue

            atual = df.iloc[-1]
            # Verificando se os indicadores foram calculados (evita erros de dados insuficientes)
            if 'ADX_14' not in atual: continue

            preco = atual['close']
            vol_ratio = atual['volume'] / atual['vol_avg']
            
            # --- LÓGICA DE ENTRADA MULTI-EXCHANGE ---
            if (vol_ratio > 2.5) and (preco > atual['ema_200']) and (atual['ADX_14'] > 25) and (preco > atual['open']):
                if f"{symbol}_{ex_name}" not in posicoes_abertas:
                    posicoes_abertas[f"{symbol}_{ex_name}"] = {'maior_preco': preco}
                    
                    msg = (f"🔥 **ALERTA DE VOLUME: {symbol}**\n"
                           f"🏛️ Corretora: **{ex_name}**\n\n"
                           f"💰 Preço: ${preco:.4f}\n"
                           f"📊 Volume: {vol_ratio:.1f}x acima da média\n"
                           f"📈 ADX: {atual['ADX_14']:.1f}\n"
                           f"✅ Sinal detectado primeiro na {ex_name}!")
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')

            # --- LÓGICA DE TRAILING STOP ---
            pos_key = f"{symbol}_{ex_name}"
            if pos_key in posicoes_abertas:
                if preco > posicoes_abertas[pos_key]['maior_preco']:
                    posicoes_abertas[pos_key]['maior_preco'] = preco
                
                preco_stop = posicoes_abertas[pos_key]['maior_preco'] * (1 - PERCENTUAL_STOP_MOVEL)
                
                if preco <= preco_stop or atual['rsi'] > 80:
                    msg = (f"🏁 **SAÍDA ESTRATÉGICA ({ex_name}): {symbol}**\n"
                           f"💰 Preço: ${preco:.4f}\n"
                           f"📢 Motivo: Trailing Stop ou RSI Alto\n"
                           f"💵 Proteja seu lucro!")
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    del posicoes_abertas[pos_key]

if __name__ == "__main__":
    bot.send_message(CHAT_ID, "🤖 **Dindo v8.0 Multi-Exchange Online!**\nMonitorando MEXC + Binance 24h.")
    while True:
        try:
            monitorar()
            time.sleep(30) # Verifica a cada 30 segundos (mais rápido!)
        except Exception as e:
            time.sleep(10)