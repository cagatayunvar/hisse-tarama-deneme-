import os
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template

app = Flask(__name__)

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
        # 1. Hisseleri dosyadan oku
        if not os.path.exists("hisseler.txt"):
            return "Hata: hisseler.txt dosyası bulunamadı!"
            
        with open("hisseler.txt", "r") as f:
            hisseler = [line.strip() for line in f if line.strip()]
        
        # 2. TÜM HİSSELERİ TEK SEFERDE ÇEK (Hız için kritik)
        # Sadece 10 hisse ile test edelim (Hata alırsak sorunu daraltmak için)
        data = yf.download(hisseler, period="1y", interval="1d", group_by='ticker', progress=False)
        
        for hisse in hisseler:
            try:
                # Çoklu indirmede veri yapısı hisse bazlı döner
                df = data[hisse].dropna() if len(hisseler) > 1 else data.dropna()
                if len(df) < 200: continue
                
                df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
                df['ST_YON'] = hesapla_supertrend(df)
                
                son, once = df.iloc[-1], df.iloc[-2]
                fiyat = float(son['Close'])
                ema = float(son['EMA200'])
                gecmis = "".join(["🟩" if x == 1 else "🟥" for x in df['ST_YON'].tail(5).tolist()])
                
                if once['ST_YON'] == -1 and son['ST_YON'] == 1 and fiyat > ema:
                    d, r, o = "YENİ AL SİNYALİ", "bg-success", 1
                elif once['ST_YON'] == 1 and son['ST_YON'] == -1 and fiyat < ema:
                    d, r, o = "YENİ SAT SİNYALİ", "bg-danger", 2
                else:
                    d = "Yükseliş" if son['ST_YON'] == 1 else "Düşüş"
                    r = "bg-primary" if son['ST_YON'] == 1 else "bg-secondary"
                    o = 3 if son['ST_YON'] == 1 else 4
                
                sonuclar.append({"hisse": hisse.replace(".IS",""), "fiyat": round(fiyat,2), "durum": d, "renk_class": r, "gecmis": gecmis, "oncelik": o})
            except: continue
    except Exception as e:
        return f"Sistem Hatası: {str(e)}"

    return render_template('index.html', hisseler=sorted(sonuclar, key=lambda x: (x['oncelik'], x['hisse'])))

if __name__ == '__main__':
    # Render'ın portunu otomatik al, bulamazsa 5000 kullan
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
