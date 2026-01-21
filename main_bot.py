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
exchange = ccxt.mexc()

# Configuração do Stop Móvel (Ex: 2% de queda a partir do topo)
PERCENTUAL_STOP_MOVEL = 0.02 
SYMBOLS = ['SUI/USDT', 'RENDER/USDT', 'JASMY/USDT', 'DUSK/USDT', 'SOL/USDT']
TIMEFRAME = '15m'

# Dicionário para "lembrar" as moedas compradas e o maior preço atingido
posicoes_abertas = {} # Estrutura: {'SUI/USDT': {'maior_preco': 1.50}}

def buscar_dados(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=250)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Indicadores Profissionais
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_21'] = ta.ema(df['close'], length=21)
        df['ema_200'] = ta.ema(df['close'], length=200)
        df['rsi'] = ta.rsi(df['close'], length=14)
        adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
        df = pd.concat([df, adx_df], axis=1)
        df['vol_avg'] = ta.sma(df['volume'], length=20)
        
        return df
    except Exception as e:
        print(f"Erro ao buscar dados de {symbol}: {e}")
        return None

def monitorar_mercado():
    print(f"Verificando oportunidades... {time.strftime('%H:%M:%S')}")
    
    for symbol in SYMBOLS:
        df = buscar_dados(symbol)
        if df is None: continue

        atual = df.iloc[-1]
        anterior = df.iloc[-2]
        
        preco_atual = atual['close']
        abertura = atual['open']
        volume_atual = atual['volume']
        vol_medio = atual['vol_avg']
        rsi = atual['rsi']
        ema_200 = atual['ema_200']
        adx = atual['ADX_14']

        # --- LÓGICA DE ENTRADA (PRO) ---
        # Filtros: Volume > 2.5x, Acima da EMA 200, ADX forte (>25), Candle Verde Limpo
        condicao_compra = (
            (volume_atual > vol_medio * 2.5) and 
            (preco_atual > ema_200) and 
            (adx > 25) and 
            (preco_atual > abertura) and # Candle Verde
            (symbol not in posicoes_abertas) # Só entra se não estiver nela
        )

        if condicao_compra:
            posicoes_abertas[symbol] = {'maior_preco': preco_atual}
            msg = (f"💎 **ENTRADA PROFISSIONAL: {symbol}**\n\n"
                   f"💰 Preço: ${preco_atual}\n"
                   f"🔥 Volume: {volume_atual/vol_medio:.1f}x acima da média\n"
                   f"📈 ADX (Força): {adx:.1f}\n"
                   f"🛡️ Stop Móvel Ativado: {PERCENTUAL_STOP_MOVEL*100}%")
            bot.send_message(CHAT_ID, msg, parse_mode='Markdown')

        # --- LÓGICA DE TRAILING STOP (SAÍDA) ---
        if symbol in posicoes_abertas:
            # Atualiza o maior preço se a moeda subiu
            if preco_atual > posicoes_abertas[symbol]['maior_preco']:
                posicoes_abertas[symbol]['maior_preco'] = preco_atual
            
            maior_preco_atingido = posicoes_abertas[symbol]['maior_preco']
            preco_stop = maior_preco_atingido * (1 - PERCENTUAL_STOP_MOVEL)

            # Se o preço cair abaixo do Stop Móvel ou RSI esticar demais
            if preco_atual <= preco_stop or rsi > 80:
                lucro_estimado = ((preco_atual / preco_stop) - 1) * 100 # Simbólico
                motivo = "Stop Móvel Atingido 🛡️" if preco_atual <= preco_stop else "RSI Sobrecomprado ⚠️"
                
                msg = (f"🏁 **SAÍDA ESTRATÉGICA: {symbol}**\n\n"
                       f"💰 Preço de Saída: ${preco_atual}\n"
                       f"📢 Motivo: {motivo}\n"
                       f"💵 Coloque o lucro no bolso!")
                
                bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                del posicoes_abertas[symbol] # Remove da memória para poder entrar de novo

# --- LOOP ---
if __name__ == "__main__":
    bot.send_message(CHAT_ID, "🚀 **Dindo Pro v7.0 Online**\nMonitorando Altas Reais com Stop Móvel.")
    while True:
        try:
            monitorar_mercado()
            time.sleep(60)
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(10)