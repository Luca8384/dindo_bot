import os
import time
import ccxt
import telebot
import pandas as pd
import pandas_ta as ta
import threading

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = telebot.TeleBot(TOKEN)

exchanges = {
    'MEXC': ccxt.mexc(),
    'BINANCE': ccxt.binance()
}

SYMBOLS = ['SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT']
TIMEFRAME = '15m'
PERCENTUAL_STOP_MOVEL = 0.02
posicoes_abertas = {}

# --- FUNÇÃO DE DADOS ---
def buscar_dados(exchange_obj, symbol):
    try:
        ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=150)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['ema_200'] = ta.ema(df['close'], length=200)
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['vol_avg'] = ta.sma(df['volume'], length=20)
        return df
    except:
        return None

# --- COMANDO INTERATIVO: /preco ---
@bot.message_handler(commands=['preco'])
def responder_preco(message):
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Use: `/preco MOEDA` (Ex: /preco SUI)", parse_mode='Markdown')
        return

    coin = texto[1].upper()
    if '/' not in coin:
        coin = f"{coin}/USDT"

    resposta = f"🔍 **Consulta de Preço: {coin}**\n\n"
    for name, ex in exchanges.items():
        try:
            ticker = ex.fetch_ticker(coin)
            preco = ticker['last']
            variacao = ticker['percentage']
            resposta += f"🏛️ **{name}**: ${preco:.4f} ({variacao:+.2f}%)\n"
        except:
            resposta += f"🏛️ **{name}**: Moeda não encontrada.\n"
    
    bot.send_message(message.chat.id, resposta, parse_mode='Markdown')

# --- MONITORAMENTO AUTOMÁTICO ---
def loop_monitoramento():
    while True:
        try:
            for symbol in SYMBOLS:
                for ex_name, ex_obj in exchanges.items():
                    df = buscar_dados(ex_obj, symbol)
                    if df is None or df.empty: continue
                    
                    atual = df.iloc[-1]
                    preco = atual['close']
                    vol_ratio = atual['volume'] / atual['vol_avg']

                    # Entrada: Volume 2.5x + Preço > EMA 200 + Candle Verde
                    if (vol_ratio > 2.5) and (preco > atual['ema_200']) and (preco > atual['open']):
                        pos_key = f"{symbol}_{ex_name}"
                        if pos_key not in posicoes_abertas:
                            posicoes_abertas[pos_key] = {'maior_preco': preco}
                            bot.send_message(CHAT_ID, f"🚀 **ALERTA DE ALTA ({ex_name})**\n💎 {symbol}\n💰 Preço: ${preco:.4f}\n🔥 Volume: {vol_ratio:.1f}x", parse_mode='Markdown')

            time.sleep(40) # Evita bloqueio de API
        except Exception as e:
            time.sleep(10)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("🤖 Robô Iniciado...")
    # Rodar o monitoramento em uma "linha" separada (Thread) para não travar o Telegram
    t = threading.Thread(target=loop_monitoramento)
    t.start()
    
    # Rodar o bot do Telegram para ouvir comandos
    bot.infinity_polling()