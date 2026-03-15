from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

app = Flask(__name__)

# Hisseleri okuyan güvenli fonksiyon
def hisseleri_getir():
    path = os.path.join(os.getcwd(), "hisseler.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()][:50] # İlk etapta max 50 hisse
    return []

def hesapla_supertrend(df, period=10, multiplier=3):
    if len(df) < period: return np.zeros(len(df))
    hl2 = (df['High'] + df['Low']) / 2
    # Gerçek ATR yerine daha hızlı standart sapma bazlı basitleştirilmiş ATR
    atr = (df['High'] - df['Low']).rolling(window=period).mean()
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
        # Timeout ekleyerek donmayı engelliyoruz
        ticker = yf.Ticker(hisse)
        df = ticker.history(period="1y", interval="1d", timeout=10)
        
        if df is None or len(df) < 200: return None
        
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
    except:
        return None

@app.route('/')
def index():
    sonuclar = []
    bist_listesi = hisseleri_getir()
    
    # İşçi sayısını 5'e düşürdük (Render donmasın diye)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(hisse_analiz_et, h): h for h in bist_listesi}
        for f in as_completed(futures):
            res = f.result()
            if res: sonuclar.append(res)
    
    sorted_res = sorted(sonuclar, key=lambda x: (x['oncelik'], x['hisse']))
    return render_template('index.html', hisseler=sorted_res)

if __name__ == '__main__':
    # Render için port ayarı
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
