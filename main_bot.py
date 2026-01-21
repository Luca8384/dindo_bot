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
exchange_mexc = ccxt.mexc()

SYMBOLS = ['SUI/USDT', 'SOL/USDT', 'PEPE/USDT', 'RENDER/USDT']

def loop_monitoramento():
    print("🔎 Iniciando varredura de mercado...")
    while True:
        try:
            for symbol in SYMBOLS:
                # Pegando dados simplificados para teste
                ohlcv = exchange_mexc.fetch_ohlcv(symbol, timeframe='15m', limit=50)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                # Cálculo simples de volume
                vol_atual = df['volume'].iloc[-1]
                vol_medio = df['volume'].mean()
                ratio = vol_atual / vol_medio
                
                print(f"DEBUG: {symbol} está com {ratio:.2f}x de volume.")
                
                # Filtro baixo (1.2x) apenas para forçar o robô a mandar mensagem agora!
                if ratio > 1.2:
                    msg = f"🔔 **TESTE DE SINAL**: {symbol}\nVolume: {ratio:.1f}x\nO robô está funcionando!"
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            
            time.sleep(60)
        except Exception as e:
            print(f"Erro no Loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("✅ Robô Ligado!")
    # Mensagem de Inicialização (Se não chegar, o Token ou ID está errado)
    try:
        bot.send_message(CHAT_ID, "🤖 **Robô Dindo v10.1 Online!**\nSe você recebeu isso, a conexão está perfeita.")
    except Exception as e:
        print(f"ERRO AO ENVIAR MENSAGEM: {e}")

    t = threading.Thread(target=loop_monitoramento)
    t.start()
    bot.infinity_polling()s