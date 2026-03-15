import os
import yfinance as yf
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    sonuclar = []
    try:
        # 1. Hisseleri oku
        with open("hisseler.txt", "r") as f:
            hisseler = [line.strip() for line in f if line.strip()][:10] # Sadece ilk 10 hisse
        
        # 2. Verileri TEK TEK ama hızlıca çek (Render çökmesin diye)
        for hisse in hisseler:
            try:
                df = yf.download(hisse, period="1y", interval="1d", progress=False)
                if df.empty or len(df) < 50: continue
                
                # En temel hesaplama (Hata payı yok)
                fiyat = float(df['Close'].iloc[-1])
                ema200 = float(df['Close'].ewm(span=200, adjust=False).mean().iloc[-1])
                
                durum = "EMA Üstünde (Pozitif)" if fiyat > ema200 else "EMA Altında (Negatif)"
                renk = "bg-success" if fiyat > ema200 else "bg-danger"
                
                sonuclar.append({
                    "hisse": hisse.replace(".IS",""),
                    "fiyat": round(fiyat, 2),
                    "durum": durum,
                    "renk_class": renk,
                    "gecmis": "Analiz Hazır",
                    "oncelik": 1 if fiyat > ema200 else 2
                })
            except: continue
            
    except Exception as e:
        return f"Sistem Hatası: {str(e)}"

    return render_template('index.html', hisseler=sorted(sonuclar, key=lambda x: x['oncelik']))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
