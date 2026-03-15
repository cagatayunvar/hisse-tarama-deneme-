import os
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask, render_template
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# 1. Hisseleri dosyadan okuyan güvenli fonksiyon
def hisseleri_getir():
    hisseler = []
    if os.path.exists("hisseler.txt"):
        with open("hisseler.txt", "r", encoding="utf-8") as f:
            hisseler = [line.strip() for line in f if line.strip()]
    return hisseler

# 2. Dış kütüphane gerektirmeyen SuperTrend fonksiyonu
def hesapla_supertrend(df, period=10, multiplier=3):
    if len(df) < period:
        return np.zeros(len(df))
    
    hl2 = (df['High'] + df['Low']) / 2
    # Basit bir ATR hesaplaması
    atr = (df['High'] - df['Low']).abs().rolling(window=period).mean()
    
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

# 3. Her bir hisse için analiz motoru
def hisse_analiz_et(hisse):
    try:
        # Veri çekme (hata payını azaltmak için timeout ekledik)
        df = yf.download(hisse, period="1y", interval="1d", progress=False, timeout=15)
        
        if df.empty or len(df) < 200:
            return None
        
        # EMA 200 hesaplama
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        # SuperTrend hesaplama
        df['ST_YON'] = hesapla_supertrend(df)
        
        son = df.iloc[-1]
        once = df.iloc[-2]
        
        fiyat = float(son['Close'])
        ema = float(son['EMA200'])
        
        # Son 5 günün geçmişi (Görsel kutucuklar)
        gecmis_liste = df['ST_YON'].tail(5).tolist()
        gecmis_gorsel = "".join(["🟩" if x == 1 else "🟥" for x in gecmis_liste])
        
        # Strateji: Fiyat EMA200 üzerindeyken SuperTrend AL verirse
        if once['ST_YON'] == -1 and son['ST_YON'] == 1 and fiyat > ema:
            durum, renk, oncelik = "YENİ AL SİNYALİ", "bg-success", 1
        elif once['ST_YON'] == 1 and son['ST_YON'] == -1 and fiyat < ema:
            durum, renk, oncelik = "YENİ SAT SİNYALİ", "bg-danger", 2
        else:
            durum = "Yükseliş Trendi" if son['ST_YON'] == 1 else "Düşüş Trendi"
            renk = "bg-primary" if son['ST_YON'] == 1 else "bg-secondary"
            oncelik = 3 if son['ST_YON'] == 1 else 4
            
        return {
            "hisse": hisse.replace(".IS", ""),
            "fiyat": round(fiyat, 2),
            "durum": durum,
            "renk_class": renk,
            "gecmis": gecmis_gorsel,
            "oncelik": oncelik
        }
    except Exception as e:
        print(f"Hata ({hisse}): {e}")
        return None

# 4. Ana Sayfa (Web Arayüzü)
@app.route('/')
def index():
    sonuclar = []
    bist_listesi = hisseleri_getir()
    
    # Render donmasın diye eşzamanlı işçi sayısını 5 yaptık
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(hisse_analiz_et, h) for h in bist_listesi]
        for f in as_completed(futures):
            res = f.result()
            if res:
                sonuclar.append(res)
    
    # Sinyal önceliğine göre sırala
    sirali_sonuclar = sorted(sonuclar, key=lambda x: (x['oncelik'], x['hisse']))
    return render_template('index.html', hisseler=sirali_sonuclar)

# 5. Sunucu Başlatma (Render Uyumlu)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
