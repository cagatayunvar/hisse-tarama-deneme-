import os
import yfinance as yf
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    sonuclar = []
    try:
        # 1. TEST LİSTESİ (Hata payını azaltmak için sadece 3 tane)
        hisseler = ["THYAO.IS", "AKBNK.IS", "EREGL.IS"]
        
        # 2. VERİ ÇEKME (En güvenli yöntem)
        for hisse in hisseler:
            try:
                # Veriyi indir ve sütunları temizle (Multi-index hatasını önler)
                df = yf.download(hisse, period="1y", interval="1d", progress=False)
                if df.empty: continue
                
                # Sütunları düzelt (Bazı sürümlerde 'Close' yerine ('Close', 'THYAO.IS') gelebiliyor)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                fiyat = float(df['Close'].iloc[-1])
                ema200 = float(df['Close'].ewm(span=200, adjust=False).mean().iloc[-1])
                
                durum = "Yükseliş (EMA Üstü)" if fiyat > ema200 else "Düşüş (EMA Altı)"
                renk = "bg-success" if fiyat > ema200 else "bg-danger"
                
                sonuclar.append({
                    "hisse": hisse.replace(".IS",""),
                    "fiyat": round(fiyat, 2),
                    "durum": durum,
                    "renk_class": renk,
                    "gecmis": "---",
                    "oncelik": 1 if fiyat > ema200 else 2
                })
            except Exception as e:
                print(f"{hisse} hatası: {e}")
                continue

        # 3. SAYFAYI GÖSTER
        return render_template('index.html', hisseler=sonuclar)

    except Exception as e:
        # Hata olursa beyaz ekran yerine burası çalışır
        return f"Sistem hatası detaylı mesaj: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
