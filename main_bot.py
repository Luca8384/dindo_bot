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

# Sua lista completa de 29 moedas
SYMBOLS = [
    'SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT',
    'FET/USDT', 'NEAR/USDT', 'TIA/USDT', 'PYTH/USDT', 'LINK/USDT',
    'ARB/USDT', 'OP/USDT', 'APT/USDT', 'ONDO/USDT', 'TAO/USDT',
    'STX/USDT', 'INJ/USDT', 'SEI/USDT', 'DOT/USDT', 'MATIC/USDT', 
    'DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT', 'WIF/USDT', 
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
        return None

# --- COMANDO /PRECO (AGORA COM BUSCA REAL) ---
@bot.message_handler(commands=['preco'])
def responder_preco(message):
    try:
        texto = message.text.split()
        coin = texto[1].upper() if len(texto) > 1 else "SUI"
        if '/' not in coin: coin = f"{coin}/USDT"
        
        # Mensagem temporária
        msg_aguarde = bot.reply_to(message, f"🔍 Consultando {coin} nas exchanges...")
        
        resposta = f"📊 **Cotações em Tempo Real: {coin}**\n\n"
        encontrou = False
        
        for name, ex in exchanges.items():
            try:
                ticker = ex.fetch_ticker(coin)
                preco = ticker['last']
                variacao = ticker['percentage']
                resposta += f"🏛️ **{name}**: `${preco:.4f}` ({variacao:+.2f}%)\n"
                encontrou = True
            except:
                resposta += f"🏛️ **{name}**: Moeda não listada.\n"
        
        if not encontrou:
            bot.edit_message_text(f"❌ A moeda **{coin}** não foi encontrada.", message.chat.id, msg_aguarde.message_id)
        else:
            bot.edit_message_text(resposta, message.chat.id, msg_aguarde.message_id, parse_mode='Markdown')
            
    except Exception as e:
        print(f"Erro no comando preco: {e}")

def loop_monitoramento():
    print("🚀 Monitoramento de Volume Iniciado...")
    while True:
        try:
            for symbol in SYMBOLS:
                for ex_name, ex_obj in exchanges.items():
                    df = buscar_dados(ex_obj, symbol)
                    if df is not None:
                        atual = df.iloc[-1]
                        vol_ratio = atual['volume'] / atual['vol_avg']
                        
                        # Filtro Profissional: Volume > 2.5x e Candle Verde
                        if vol_ratio > 2.5 and atual['close'] > atual['open']:
                             msg = (f"🚀 **PICO DE VOLUME DETECTADO!**\n\n"
                                    f"💎 Moeda: {symbol}\n"
                                    f"🏛️ Exchange: {ex_name}\n"
                                    f"📊 Volume: {vol_ratio:.1f}x acima da média\n"
                                    f"💰 Preço: ${atual['close']:.4f}")
                             bot.send_message(CHAT_ID, msg, parse_mode='Markdown')

            time.sleep(60)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    print("✅ Robô Dindo em execução.")
    t = threading.Thread(target=loop_monitoramento)
    t.daemon = True
    t.start()
    bot.infinity_polling()
    # Versao Final 10.7 - Logica de Precos Ativada