import os
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template

app = Flask(__name__)

# Kendi SuperTrend Fonksiyonumuz (pandas_ta kütüphanesine gerek kalmadı!)
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
        # Şimdilik sadece 3 hisse ile test edelim, site açılınca hisseler.txt'ye bağlarız
        hisseler = ["THYAO.IS", "AKBNK.IS", "EREGL.IS"]
        
        for hisse in hisseler:
            try:
                df = yf.download(hisse, period="1y", interval="1d", progress=False)
                if df.empty: continue
                
                # Multi-index hatasını engelle
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
                df['ST_YON'] = hesapla_supertrend(df)
                
                fiyat = float(df['Close'].iloc[-1])
                ema200 = float(df['EMA200'].iloc[-1])
                
                sonuclar.append({
                    "hisse": hisse.replace(".IS",""),
                    "fiyat": round(fiyat, 2),
                    "durum": "Sistem Başarıyla Çalışıyor!",
                    "renk_class": "bg-success" if fiyat > ema200 else "bg-danger",
                    "gecmis": "---",
                    "oncelik": 1
                })
            except Exception as e:
                print(f"Hata: {e}")
                continue

        return render_template('index.html', hisseler=sonuclar)
    
    except Exception as e:
        return f"Kod içi hata oluştu: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
