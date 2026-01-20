# indicadores.py
def calcular_rsi(prices, period=14):
    if len(prices) < period: return 50
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def detectar_acumulo(ohlcv):
    try:
        fechamentos = [c[4] for c in ohlcv[-6:-1]]
        max_p = max(fechamentos)
        min_p = min(fechamentos)
        variacao = ((max_p - min_p) / min_p) * 100
        vols = [c[5] for c in ohlcv]
        ratio_vol = vols[-1] / (sum(vols[-11:-1]) / 10)
        if variacao < 0.15 and ratio_vol > 2.5:
            return True, variacao, ratio_vol
        return False, 0, 0
    except: return False, 0, 0

def calcular_dados_velas(ohlcv):
    fechamentos = [c[4] for c in ohlcv]
    abertura = ohlcv[-1][1]
    preco = ohlcv[-1][4]
    var = ((preco - abertura) / abertura) * 100
    vols = [c[5] for c in ohlcv]
    ratio_vol = vols[-1] / (sum(vols[-15:-1]) / 14)
    return preco, var, ratio_vol, fechamentos