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

# Inicializamos as corretoras com carregamento automático de mercados
exchanges = {
    'MEXC': ccxt.mexc({'enableRateLimit': True}),
    'BINANCE': ccxt.binance({'enableRateLimit': True})
}

# Lista de 29 moedas (Já com POL no lugar de MATIC)
SYMBOLS = [
    'SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT',
    'FET/USDT', 'NEAR/USDT', 'TIA/USDT', 'PYTH/USDT', 'LINK/USDT',
    'ARB/USDT', 'OP/USDT', 'APT/USDT', 'ONDO/USDT', 'TAO/USDT',
    'STX/USDT', 'INJ/USDT', 'SEI/USDT', 'DOT/USDT', 'POL/USDT', 
    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 
    'BONK/USDT', 'FLOKI/USDT', 'POPCAT/USDT', 'BRETT/USDT', 'BOME/USDT', 'BTC/USDT'
]

def buscar_dados(exchange_obj, symbol):
    try:
        ohlcv = exchange_obj.fetch_ohlcv(symbol, timeframe='15m', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['ema_200'] = ta.ema(df['close'], length=200)
        df['vol_avg'] = ta.sma(df['volume'], length=20)
        return df
    except:
        return None

# --- COMANDO /PRECO ROBUSTO ---
@bot.message_handler(commands=['preco'])
def responder_preco(message):
    try:
        partes = message.text.split()
        if len(partes) < 2:
            bot.reply_to(message, "💡 Use: `/preco SOL`")
            return

        coin = partes[1].upper().strip()
        symbol = f"{coin}/USDT" if '/' not in coin else coin
        
        msg_aguarde = bot.reply_to(message, f"🔍 Consultando {symbol}...")
        resposta = f"📊 **Cotações: {symbol}**\n\n"
        
        for name, ex in exchanges.items():
            try:
                # Carregamento preventivo se o mercado ainda não estiver na memória
                if symbol not in ex.symbols:
                    ex.load_markets()
                
                ticker = ex.fetch_ticker(symbol)
                preco = ticker['last']
                variacao = ticker['percentage']
                resposta += f"🏛️ **{name}**: `${preco:.4f}` ({variacao:+.2f}%)\n"
            except Exception:
                resposta += f"🏛️ **{name}**: Não encontrada.\n"
        
        bot.edit_message_text(resposta, message.chat.id, msg_aguarde.message_id, parse_mode='Markdown')
    except Exception as e:
        print(f"Erro no comando preco: {e}")

# --- LOOP DE MONITORAMENTO ---
def loop_monitoramento():
    print("🚀 Monitoramento Ativo...")
    while True:
        try:
            for symbol in SYMBOLS:
                for name, ex in exchanges.items():
                    df = buscar_dados(ex, symbol)
                    if df is not None:
                        atual = df.iloc[-1]
                        ratio = atual['volume'] / atual['vol_avg']
                        
                        if ratio > 2.5 and atual['close'] > atual['open']:
                            msg = (f"🚀 **PICO DE VOLUME!**\n\n"
                                   f"💎 Moeda: {symbol}\n"
                                   f"🏛️ Exchange: {name}\n"
                                   f"📊 Volume: {ratio:.1f}x acima da média\n"
                                   f"💰 Preço: ${atual['close']:.4f}")
                            bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            time.sleep(60)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    print("✅ Robô Dindo v11.1 Online.")
    # Forçamos o carregamento inicial dos mercados para não dar erro de "não encontrada"
    for ex in exchanges.values():
        try: ex.load_markets()
        except: pass

    t = threading.Thread(target=loop_monitoramento)
    t.daemon = True
    t.start()
    bot.infinity_polling()