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

# Configuração robusta para as Exchanges
# 'defaultType': 'spot' força a Binance a olhar apenas para o mercado à vista
exchanges = {
    'MEXC': ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'spot'}}),
    'BINANCE': ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
}

SYMBOLS = [
    'SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT',
    'FET/USDT', 'NEAR/USDT', 'TIA/USDT', 'PYTH/USDT', 'LINK/USDT',
    'ARB/USDT', 'OP/USDT', 'APT/USDT', 'ONDO/USDT', 'TAO/USDT',
    'STX/USDT', 'INJ/USDT', 'SEI/USDT', 'DOT/USDT', 'POL/USDT', 
    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 
    'BONK/USDT', 'FLOKI/USDT', 'POPCAT/USDT', 'BRETT/USDT', 'BOME/USDT', 'BTC/USDT'
]

def buscar_preco_seguro(exchange_obj, symbol):
    try:
        # Tenta carregar mercados apenas se estiverem vazios
        if not exchange_obj.markets:
            exchange_obj.load_markets()
        
        ticker = exchange_obj.fetch_ticker(symbol)
        return ticker['last'], ticker['percentage']
    except Exception as e:
        print(f"Erro na {exchange_obj.id} para {symbol}: {e}")
        return None, None

@bot.message_handler(commands=['preco'])
def responder_preco(message):
    try:
        partes = message.text.split()
        if len(partes) < 2:
            bot.reply_to(message, "💡 Use: `/preco SOL` ou `/preco PEPE`")
            return

        coin = partes[1].upper().strip()
        symbol = f"{coin}/USDT"
        
        msg = bot.reply_to(message, f"🔍 Pesquisando {symbol} no mercado Spot...")
        
        linhas_resposta = []
        for name, ex in exchanges.items():
            preco, var = buscar_preco_seguro(ex, symbol)
            if preco:
                linhas_resposta.append(f"🏛️ **{name}**: `${preco:.4f}` ({var:+.2f}%)")
            else:
                linhas_resposta.append(f"🏛️ **{name}**: Sem dados (Spot)")

        texto_final = f"📊 **Cotações: {symbol}**\n\n" + "\n".join(linhas_resposta)
        bot.edit_message_text(texto_final, message.chat.id, msg.message_id, parse_mode='Markdown')

    except Exception as e:
        print(f"Erro comando preco: {e}")

def loop_monitoramento():
    print("🚀 Monitoramento de Volume Ativo...")
    while True:
        try:
            for symbol in SYMBOLS:
                for name, ex in exchanges.items():
                    try:
                        ohlcv = ex.fetch_ohlcv(symbol, timeframe='15m', limit=50)
                        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        df['vol_avg'] = ta.sma(df['volume'], length=20)
                        atual = df.iloc[-1]
                        ratio = atual['volume'] / atual['vol_avg']
                        
                        if ratio > 2.5 and atual['close'] > atual['open']:
                            bot.send_message(CHAT_ID, f"🚀 **PICO DE VOLUME!**\n💎 {symbol} na {name}\n📊 Vol: {ratio:.1f}x", parse_mode='Markdown')
                    except:
                        continue
            time.sleep(60)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    print("✅ Sistema Iniciado v14.0")
    t = threading.Thread(target=loop_monitoramento)
    t.daemon = True
    t.start()
    bot.infinity_polling()