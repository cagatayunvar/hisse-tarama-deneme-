import os
import yfinance as yf
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    sonuclar = []
    try:
        # Sadece 5 ana hisse ile test ediyoruz (Hata payını yok etmek için)
        test_hisseler = ["THYAO.IS", "AKBNK.IS", "TUPRS.IS", "ASELS.IS", "EREGL.IS"]
        
        # Tek tek ve hızlıca çekiyoruz
        for hisse in test_hisseler:
            try:
                t = yf.Ticker(hisse)
                hist = t.history(period="1d")
                if not hist.empty:
                    fiyat = hist['Close'].iloc[-1]
                    sonuclar.append({
                        "hisse": hisse.replace(".IS",""),
                        "fiyat": round(fiyat, 2),
                        "durum": "Sistem Aktif",
                        "renk_class": "bg-primary",
                        "gecmis": "---",
                        "oncelik": 1
                    })
            except:
                continue
    except Exception as e:
        return f"Sunucu Hatası: {str(e)}"

    return render_template('index.html', hisseler=sonuclar)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
