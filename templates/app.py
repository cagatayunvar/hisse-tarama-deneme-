import os
import yfinance as yf
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    sonuclar = []
    try:
        # 1. TEST İÇİN SABİT LİSTE (Dosya hatasını önlemek için)
        test_hisseler = ["THYAO.IS", "AKBNK.IS", "TUPRS.IS", "ASELS.IS", "EREGL.IS"]
        
        # 2. VERİ ÇEKME (En sade haliyle)
        for hisse in test_hisseler:
            try:
                # Ticker objesi ile hızlı çekim
                df = yf.download(hisse, period="5d", interval="1d", progress=False)
                if not df.empty:
                    # En son kapanış fiyatını al
                    fiyat = float(df['Close'].iloc[-1])
                    sonuclar.append({
                        "hisse": hisse.replace(".IS",""),
                        "fiyat": round(fiyat, 2),
                        "durum": "Sistem Aktif",
                        "renk_class": "bg-primary",
                        "gecmis": "---",
                        "oncelik": 1
                    })
            except Exception as e:
                print(f"Hisse hatası ({hisse}): {e}")
                continue
                
    except Exception as e:
        # Eğer hala hata varsa ekrana hatayı yazdır ki görelim
        return f"Uygulama Hatası Detayı: {str(e)}"

    # Render_template'in çalışması için 'templates/index.html' MUTLAKA olmalı
    try:
        return render_template('index.html', hisseler=sonuclar)
    except Exception:
        return "Hata: 'templates/index.html' dosyası GitHub'da bulunamadı!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
