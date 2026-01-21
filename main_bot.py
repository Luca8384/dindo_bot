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

TIMEFRAME = '15m'
PERCENTUAL_STOP_MOVEL = 0.02
posicoes_abertas = {}

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

# --- COMANDO /PRECO ---
@bot.message_handler(commands=['preco'])
def responder_preco(message):
    texto = message.text.split()
    if len(texto) < 2:
        bot.reply_to(message, "❌ Use: `/preco MOEDA` (Ex: /preco SUI)", parse_mode='Markdown')
        return
    coin = texto[1].upper()
    if '/' not in coin: coin = f"{coin}/USDT"
    resposta = f"🔍 **Consulta: {coin}**\n\n"
    for name, ex in exchanges.items():
        try:
            ticker = ex.fetch_ticker(coin)
            resposta += f"🏛️ **{name}**: ${ticker['last']:.4f} ({ticker['percentage']:+.2f}%)\n"
        except:
            resposta += f"🏛️ **{name}**: Não encontrada.\n"
    bot.send_message(message.chat.id, resposta, parse_mode='Markdown')

# --- MONITORAMENTO COM DETECTOR DE ANOMALIA ---
def loop_monitoramento():
    while True:
        try:
            for symbol in SYMBOLS:
                dados_exchanges = {}
                
                for ex_name, ex_obj in exchanges.items():
                    df = buscar_dados(ex_obj, symbol)
                    if df is not None and not df.empty:
                        dados_exchanges[ex_name] = df.iloc[-1]
                
                # Se temos dados de ambas, comparamos as anomalias
                if 'MEXC' in dados_exchanges and 'BINANCE' in dados_exchanges:
                    mexc = dados_exchanges['MEXC']
                    binance = dados_exchanges['BINANCE']
                    
                    vol_ratio_mexc = mexc['volume'] / mexc['vol_avg']
                    vol_ratio_binance = binance['volume'] / binance['vol_avg']
                    
                    # --- ALERTA DE ANOMALIA (MEXC > BINANCE) ---
                    # Se o volume na MEXC for 3x maior que o ratio da Binance
                    if vol_ratio_mexc > (vol_ratio_binance * 3) and vol_ratio_mexc > 2.5:
                        msg = (f"⚠️ **ANOMALIA DE VOLUME DETECTADA!**\n\n"
                               f"💎 Moeda: {symbol}\n"
                               f"🚀 Volume MEXC: {vol_ratio_mexc:.1f}x acima da média\n"
                               f"🐢 Volume Binance: {vol_ratio_binance:.1f}x acima da média\n"
                               f"💡 **Oportunidade:** Fluxo forte iniciando na MEXC!")
                        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')

                    # --- LÓGICA PADRÃO DE ENTRADA ---
                    if (vol_ratio_mexc > 2.5) and (mexc['close'] > mexc['ema_200']) and (mexc['close'] > mexc['open']):
                        pos_key = f"{symbol}_MEXC"
                        if pos_key not in posicoes_abertas:
                            posicoes_abertas[pos_key] = {'maior_preco': mexc['close']}
                            bot.send_message(CHAT_ID, f"🚀 **ALERTA DE ALTA (MEXC)**\n💎 {symbol}\n💰 Preço: ${mexc['close']:.4f}", parse_mode='Markdown')

            time.sleep(60)
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    t = threading.Thread(target=loop_monitoramento)
    t.start()
    bot.infinity_polling()