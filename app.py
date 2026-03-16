import os
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template

app = Flask(__name__)

# Dış kütüphanesiz, ölümsüz SuperTrend formülümüz
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

@app.route('/')
def index():
    sonuclar = []
    try:
        # 1. Kendi listenizi okuyun (hisseler.txt'den)
        if os.path.exists("hisseler.txt"):
            with open("hisseler.txt", "r") as f:
                hisseler = [line.strip() for line in f if line.strip()]
        else:
            hisseler = ["THYAO.IS", "AKBNK.IS", "EREGL.IS", "TUPRS.IS"]
        
        # Ücretsiz sunucu boğulmasın diye şimdilik ilk 30 hisseyi çekiyoruz (Sonra artırabilirsiniz)
        islem_listesi = hisseler[:30]

        # 2. Gerçek Analiz Motoru
        for hisse in islem_listesi:
            try:
                df = yf.download(hisse, period="1y", interval="1d", progress=False)
                if df.empty or len(df) < 200: continue
                
                # Sütun kayma hatalarını engelle
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
                df['ST_YON'] = hesapla_supertrend(df)
                
                son = df.iloc[-1]
                once = df.iloc[-2]
                fiyat = float(son['Close'])
                ema = float(son['EMA200'])
                gecmis = "".join(["🟩" if x == 1 else "🟥" for x in df['ST_YON'].tail(5).tolist()])
                
                # Asıl Sinyal Stratejisi
                if once['ST_YON'] == -1 and son['ST_YON'] == 1 and fiyat > ema:
                    d, r, o = "YENİ AL SİNYALİ", "bg-success", 1
                elif once['ST_YON'] == 1 and son['ST_YON'] == -1 and fiyat < ema:
                    d, r, o = "YENİ SAT SİNYALİ", "bg-danger", 2
                else:
                    d = "Yükseliş Trendi" if son['ST_YON'] == 1 else "Düşüş Trendi"
                    r = "bg-primary" if son['ST_YON'] == 1 else "bg-secondary"
                    o = 3 if son['ST_YON'] == 1 else 4
                
                sonuclar.append({"hisse": hisse.replace(".IS",""), "fiyat": round(fiyat,2), "durum": d, "renk_class": r, "gecmis": gecmis, "oncelik": o})
            except: continue

        # Sinyal verenleri en üste diz
        return render_template('index.html', hisseler=sorted(sonuclar, key=lambda x: (x['oncelik'], x['hisse'])))
    
    except Exception as e:
        return f"Sistem Hatası: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
