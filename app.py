from flask import Flask, render_template
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import warnings
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

app = Flask(__name__)

# TXT dosyasından hisseleri okuyan fonksiyon
def hisseleri_getir():
    dosya_yolu = "hisseler.txt"
    if os.path.exists(dosya_yolu):
        with open(dosya_yolu, "r", encoding="utf-8") as file:
            # Satır satır oku, boşlukları temizle ve listeye ekle
            hisseler = [line.strip() for line in file if line.strip()]
        return hisseler
    else:
        print(f"⚠️ HATA: {dosya_yolu} bulunamadı!")
        return []

def hisse_analiz_et(hisse):
    try:
        ticker = yf.Ticker(hisse)
        df = ticker.history(period="1y")
        
        if df.empty or len(df) < 200:
            return None
            
        df.ta.ema(length=200, append=True)
        df.ta.supertrend(length=10, multiplier=3, append=True)
        
        st_yon_sutunu = [col for col in df.columns if col.startswith('SUPERTd')][0]
        ema_sutunu = [col for col in df.columns if col.startswith('EMA_200')][0]
        
        son_gun = df.iloc[-1]
        onceki_gun = df.iloc[-2]
        
        fiyat = son_gun['Close']
        ema = son_gun[ema_sutunu]
        
        son_5_gun = df.tail(5)
        gecmis_gorsel = "".join(["🟩" if row[st_yon_sutunu] == 1 else "🟥" for _, row in son_5_gun.iterrows()])
        
        if onceki_gun[st_yon_sutunu] == -1 and son_gun[st_yon_sutunu] == 1 and fiyat > ema:
            durum = "YENİ AL SİNYALİ"
            renk_class = "bg-success"
            oncelik = 1
        elif onceki_gun[st_yon_sutunu] == 1 and son_gun[st_yon_sutunu] == -1 and fiyat < ema:
            durum = "YENİ SAT SİNYALİ"
            renk_class = "bg-danger"
            oncelik = 2
        else:
            durum = "Yükseliş Trendi" if son_gun[st_yon_sutunu] == 1 else "Düşüş Trendi"
            renk_class = "bg-primary" if son_gun[st_yon_sutunu] == 1 else "bg-secondary"
            oncelik = 3 if son_gun[st_yon_sutunu] == 1 else 4
            
        return {
            "hisse": hisse.replace(".IS", ""),
            "fiyat": round(fiyat, 2),
            "durum": durum,
            "renk_class": renk_class,
            "gecmis": gecmis_gorsel,
            "oncelik": oncelik
        }
    except Exception as e:
        print(f"Hata ({hisse}): {e}")
        return None

@app.route('/')
def index():
    sonuclar = []
    # Hisseleri txt dosyasından taze olarak çek
    bist_listesi = hisseleri_getir()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        gelecek_sonuclar = {executor.submit(hisse_analiz_et, hisse): hisse for hisse in bist_listesi}
        
        for gelecek in as_completed(gelecek_sonuclar):
            veri = gelecek.result()
            if veri is not None:
                sonuclar.append(veri)
                
    sonuclar = sorted(sonuclar, key=lambda x: (x['oncelik'], x['hisse']))
                
    return render_template('index.html', hisseler=sonuclar)

if __name__ == '__main__':
    app.run(debug=True)