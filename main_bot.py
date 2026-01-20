import ccxt
import time
import requests
import os
# Importamos as funções que criamos no arquivo indicadores.py
from indicadores import calcular_rsi, detectar_acumulo, calcular_dados_velas

# --- CONFIGURAÇÃO DE ACESSO (Híbrida: Local ou Nuvem) ---
try:
    # Tenta ler do seu arquivo local
    from dados_bot import TOKEN, CHAT_ID, HOT_LIST
    print("✅ Configurações carregadas do arquivo local (dados_bot.py)")
except ImportError:
    # Se o arquivo não existir (como no Render), busca nas variáveis de ambiente
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    # Moedas de IA e RWA favoritas para monitorar sempre
    HOT_LIST = ['AIF/USDT', 'RENDER/USDT', 'OORT/USDT', 'ONDO/USDT', 'DUSK/USDT']
    print("☁️ Configurações carregadas das Variáveis de Ambiente (Nuvem)")

# --- INICIALIZAÇÃO ---
exchange = ccxt.mexc({
    'enableRateLimit': True,
})

def enviar_telegram(mensagem):
    """Envia alertas para o seu bot no Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        requests.get(url, params=params)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def check_logic(symbol):
    """Executa a análise técnica para cada moeda"""
    try:
        # Buscamos candles de 5 minutos para maior agilidade
        ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=40)
        if len(ohlcv) < 30: return

        # Cálculos de indicadores vindos do indicadores.py
        preco_atual, variacao, ratio_vol, fechamentos = calcular_dados_velas(ohlcv)
        rsi_atual = calcular_rsi(fechamentos)
        is_acumulando, var_acumulo, ratio_acumulo = detectar_acumulo(ohlcv)

        link_mexc = f"https://www.mexc.com/exchange/{symbol.replace('/', '_')}"

        # 1. LÓGICA DE ACÚMULO (Oportunidade Antecipada)
        if is_acumulando:
            msg = (f"💎 <b>ACÚMULO DETECTADO</b>\n"
                   f"🪙 Ativo: {symbol}\n"
                   f"🤫 Preço Lateral: {var_acumulo:.3f}%\n"
                   f"🐋 Volume subindo: {ratio_acumulo:.2f}x\n"
                   f"🔗 <a href='{link_mexc}'>Abrir Gráfico</a>")
            enviar_telegram(msg)
            print(f"Sinal de Acúmulo: {symbol}")

        # 2. LÓGICA DE ENTRADA (Volume Explosivo + RSI Saudável)
        elif ratio_vol > 5.0 and variacao > 0.4 and rsi_atual < 65:
            msg = (f"🚀 <b>PICO DE VOLUME (ENTRADA)</b>\n"
                   f"🪙 Ativo: {symbol}\n"
                   f"📈 Alta: +{variacao:.2f}%\n"
                   f"📊 Força: {ratio_vol:.2f}x a média\n"
                   f"🔥 RSI: {rsi_atual:.1f}\n"
                   f"🔗 <a href='{link_mexc}'>Abrir Gráfico</a>")
            enviar_telegram(msg)
            print(f"Sinal de Entrada: {symbol}")

        # 3. LÓGICA DE SAÍDA (RSI Sobrecomprado - Exaustão)
        elif rsi_atual > 82:
            msg = (f"⚠️ <b>ALERTA DE SOBRECOMPRA (SAÍDA)</b>\n"
                   f"🪙 Ativo: {symbol}\n"
                   f"🚨 RSI em {rsi_atual:.1f}\n"
                   f"💰 Considere realizar lucro ou subir o Stop!\n"
                   f"🔗 <a href='{link_mexc}'>Ver Gráfico</a>")
            enviar_telegram(msg)
            print(f"Sinal de Saída: {symbol}")

    except Exception as e:
        # Erros individuais de moedas não param o robô
        pass

# --- LOOP PRINCIPAL ---
print("🚀 Robô Dindo v5.0 iniciado com sucesso!")
enviar_telegram("🤖 <b>Robô Dindo v5.0 Online!</b>\nMonitorando Top 100 moedas e Setores Quentes.")

while True:
    try:
        # 1. Busca todos os tickers e filtra as Top 100 por volume
        tickers = exchange.fetch_tickers()
        usdt_symbols = [s for s in tickers if s.endswith('/USDT')]
        
        # Ordena pelo volume das últimas 24h
        top_100 = sorted(usdt_symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:100]
        
        # Une com as moedas que você sempre quer vigiar (IA/RWA)
        lista_final = list(set(top_100 + HOT_LIST))
        
        print(f"🔍 Escaneando {len(lista_final)} ativos com maior liquidez...")

        for s in lista_final:
            check_logic(s)
            time.sleep(0.1) # Evita ser bloqueado pela API da MEXC

        print("✅ Varredura completa. Aguardando 60 segundos...")
        time.sleep(60)

    except Exception as e:
        print(f"Erro no loop principal: {e}")
        time.sleep(10)