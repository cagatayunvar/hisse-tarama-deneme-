from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

app = Flask(__name__)

def hisseleri_getir():
    if os.path.exists("hisseler.txt"):
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

# Dış kütüphane kullanmadan SuperTrend hesaplayan fonksiyon
def hesapla_supertrend(df, period=10, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    atr = (df['High'] - df['Low']).abs().rolling(window=period).mean() # Basit ATR
    
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    
    trend = np.ones(len(df))
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > upperband.iloc[i-1]:
            trend[i] = 1
        elif df['Close'].iloc[i] < lowerband.iloc[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
    return trend

def hisse_analiz_et(hisse):
    try:
        df = yf.Ticker(hisse).history(period="1y")
        if len(df) < 200: return None
        
        # 200 EMA ve SuperTrend hesapla
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        df['ST_YON'] = hesapla_supertrend(df)
        
        son = df.iloc[-1]
        once = df.iloc[-2]
        
        fiyat, ema = son['Close'], son['EMA200']
        gecmis = "".join(["🟩" if x == 1 else "🟥" for x in df['ST_YON'].tail(5)])
        
        if once['ST_YON'] == -1 and son['ST_YON'] == 1 and fiyat > ema:
            durum, renk, oncelik = "YENİ AL SİNYALİ", "bg-success", 1
        elif once['ST_YON'] == 1 and son['ST_YON'] == -1 and fiyat < ema:
            durum, renk, oncelik = "YENİ SAT SİNYALİ", "bg-danger", 2
        else:
            durum = "Yükseliş Trendi" if son['ST_YON'] == 1 else "Düşüş Trendi"
            renk = "bg-primary" if son['ST_YON'] == 1 else "bg-secondary"
            oncelik = 3 if son['ST_YON'] == 1 else 4
            
        return {"hisse": hisse.replace(".IS",""), "fiyat": round(fiyat,2), "durum": durum, "renk_class": renk, "gecmis": gecmis, "oncelik": oncelik}
    except: return None

@app.route('/')
def index():
    sonuclar = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(hisse_analiz_et, h) for h in hisseleri_getir()]
        for f in as_completed(futures):
            res = f.result()
            if res: sonuclar.append(res)
    return render_template('index.html', hisseler=sorted(sonuclar, key=lambda x: (x['oncelik'], x['hisse'])))

if __name__ == '__main__':
    app.run(debug=True)
