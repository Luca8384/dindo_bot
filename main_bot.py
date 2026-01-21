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

SYMBOLS = [
    'SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT',
    'FET/USDT', 'NEAR/USDT', 'TIA/USDT', 'PYTH/USDT', 'LINK/USDT',
    'ARB/USDT', 'OP/USDT', 'APT/USDT', 'ONDO/USDT', 'TAO/USDT',
    'STX/USDT', 'INJ/USDT', 'SEI/USDT', 'DOT/USDT', 'MATIC/USDT', 'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 
    'BONK/USDT', 'FLOKI/USDT', 'POPCAT/USDT', 'BRETT/USDT', 'BOME/USDT'
]
    

def buscar_dados(exchange_obj, symbol):
    try:
        ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe='15m', limit=150)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['ema_200'] = ta.ema(df['close'], length=200)
        df['vol_avg'] = ta.sma(df['volume'], length=20)
        return df
    except Exception as e:
        print(f"Erro ao buscar {symbol} na {exchange_obj.id}: {e}")
        return None

@bot.message_handler(commands=['preco'])
def responder_preco(message):
    print(f"Recebi comando /preco de {message.chat.id}")
    coin = message.text.split()[1].upper() if len(message.text.split()) > 1 else "SUI"
    if '/' not in coin: coin = f"{coin}/USDT"
    bot.reply_to(message, f"Buscando preço de {coin}...")

# Linha de seguranca para forcar o push v10.4
def loop_monitoramento():
    print("🚀 Monitoramento Automático Iniciado...")
    while True:
        try:
            for symbol in SYMBOLS:
                # Diminuí o filtro para 1.5x apenas para testar se ele envia algo!
                for ex_name, ex_obj in exchanges.items():
                    df = buscar_dados(ex_obj, symbol)
                    if df is not None:
                        atual = df.iloc[-1]
                        vol_ratio = atual['volume'] / atual['vol_avg']
                        print(f"Check {symbol} em {ex_name}: Vol {vol_ratio:.2f}x") # Veremos isso no Log!
                        
                        if vol_ratio > 1.5 and atual['close'] > atual['open']:
                             bot.send_message(CHAT_ID, f"📢 Sinal de Teste: {symbol} na {ex_name} com {vol_ratio:.1f}x volume")

            time.sleep(60)
        except Exception as e:
            print(f"Erro no Loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("✅ Sistema Online. Verifique o Telegram.")
    bot.send_message(CHAT_ID, "🤖 Robô Dindo v10.1 Online e Monitorando!")
    
    t = threading.Thread(target=loop_monitoramento)
    t.setDaemon(True) # Garante que a thread morra se o programa parar
    t.start()
    
    bot.infinity_polling()