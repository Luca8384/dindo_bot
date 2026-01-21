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

# Inicializamos as corretoras
exchanges = {
    'MEXC': ccxt.mexc({'enableRateLimit': True}),
    'BINANCE': ccxt.binance({'enableRateLimit': True})
}

SYMBOLS = [
    'SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT',
    'FET/USDT', 'NEAR/USDT', 'TIA/USDT', 'PYTH/USDT', 'LINK/USDT',
    'ARB/USDT', 'OP/USDT', 'APT/USDT', 'ONDO/USDT', 'TAO/USDT',
    'STX/USDT', 'INJ/USDT', 'SEI/USDT', 'DOT/USDT', 'POL/USDT', 
    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 
    'BONK/USDT', 'FLOKI/USDT', 'POPCAT/USDT', 'BRETT/USDT', 'BOME/USDT'
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

# --- FUNÇÃO DE BUSCA INTELIGENTE ---
def encontrar_par_exato(exchange_obj, coin_name):
    try:
        # Forçamos o carregamento de todos os símbolos da corretora
        mercados = exchange_obj.load_markets()
        opcoes_possiveis = [f"{coin_name}/USDT", f"{coin_name}/USDC", f"{coin_name}/BTC"]
        
        for par in opcoes_possiveis:
            if par in exchange_obj.symbols:
                return par
        return None
    except:
        return None

# --- COMANDO /PRECO ---
@bot.message_handler(commands=['preco'])
def responder_preco(message):
    try:
        partes = message.text.split()
        if len(partes) < 2:
            bot.reply_to(message, "💡 Use: `/preco SOL`")
            return

        coin = partes[1].upper().strip()
        msg_aguarde = bot.reply_to(message, f"🔍 Localizando {coin} nas exchanges...")
        resposta = f"📊 **Cotações: {coin}**\n\n"
        
        for name, ex in exchanges.items():
            # Tenta encontrar o par correto (Spot) na corretora
            par_correto = encontrar_par_exato(ex, coin)
            
            if par_correto:
                try:
                    ticker = ex.fetch_ticker(par_correto)
                    preco = ticker['last']
                    variacao = ticker['percentage']
                    resposta += f"🏛️ **{name}**: `${preco:.4f}` ({variacao:+.2f}%)\n"
                except:
                    resposta += f"🏛️ **{name}**: Erro ao obter preço.\n"
            else:
                resposta += f"🏛️ **{name}**: Não encontrada no Spot.\n"
        
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
                            msg = (f"🚀 **PICO DE VOLUME!**\n"
                                   f"💎 Moeda: {symbol} em {name}\n"
                                   f"📊 Volume: {ratio:.1f}x acima da média\n"
                                   f"💰 Preço: ${atual['close']:.4f}")
                            bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            time.sleep(60)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    print("✅ Robô Dindo v12.0 Online.")
    t = threading.Thread(target=loop_monitoramento)
    t.daemon = True
    t.start()
    bot.infinity_polling()