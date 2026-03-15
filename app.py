import os
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

def hisseleri_getir():
    if os.path.exists("hisseler.txt"):
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            # Render donmasın diye listeyi 40 hisse ile sınırlayalım, stabilse artırırsın
            return [line.strip() for line in f if line.strip()][:40]
    return []

def hesapla_supertrend(df, period=10, multiplier=3):
    if len(df) < period: return np.zeros(len(df))
    hl2 = (df['High'] + df['Low']) / 2
    atr = (df['High'] - df['Low']).abs().rolling(window=period).mean()
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    trend = np.ones(len(df))
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > upperband.iloc[i-1]: trend[i] = 1
        elif df['Close'].iloc[i] < lowerband.iloc[i-1]: trend[i] = -1
        else: trend[i] = trend[i-1]
    return trend

def hisse_analiz_et(hisse):
    try:
        # download yerine Ticker.history kullanımı ücretsiz sunucularda daha stabildir
        t = yf.Ticker(hisse)
        df = t.history(period="1y", interval="1d")
        
        if df.empty or len(df) < 200: return None
        
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['ST_YON'] = hesapla_supertrend(df)
        
        son, once = df.iloc[-1], df.iloc[-2]
        fiyat, ema = float(son['Close']), float(son['EMA200'])
        gecmis = "".join(["🟩" if x == 1 else "🟥" for x in df['ST_YON'].tail(5).tolist()])
        
        if once['ST_YON'] == -1 and son['ST_YON'] == 1 and fiyat > ema:
            d, r, o = "YENİ AL SİNYALİ", "bg-success", 1
        elif once['ST_YON'] == 1 and son['ST_YON'] == -1 and fiyat < ema:
            d, r, o = "YENİ SAT SİNYALİ", "bg-danger", 2
        else:
            d = "Yükseliş Trendi" if son['ST_YON'] == 1 else "Düşüş Trendi"
            r = "bg-primary" if son['ST_YON'] == 1 else "bg-secondary"
            o = 3 if son['ST_YON'] == 1 else 4
            
        return {"hisse": hisse.replace(".IS",""), "fiyat": round(fiyat,2), "durum": d, "renk_class": r, "gecmis": gecmis, "oncelik": o}
    except: return None

@app.route('/')
def index():
    sonuclar = []
    bist_listesi = hisseleri_getir()
    # max_workers=2 yaparak Render'ın boğulmasını engelliyoruz
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(hisse_analiz_et, h) for h in bist_listesi]
        for f in as_completed(futures):
            res = f.result()
            if res: sonuclar.append(res)
    return render_template('index.html', hisseler=sorted(sonuclar, key=lambda x: (x['oncelik'], x['hisse'])))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
