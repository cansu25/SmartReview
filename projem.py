import streamlit as st
import pandas as pd
import pyodbc
import google.generativeai as genai
import time
import json # Otonom Ajanın beyni için JSON kütüphanesini ekledik
import matplotlib.pyplot as plt

# --- 1. AYARLAR VE YAPAY ZEKA ---
GOOGLE_API_KEY = "BURAYA_KENDİ_GEMINI_API_ANAHTARINIZI_YAZIN"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_sql_connection():
    return pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=.;Database=VeriLing;Trusted_Connection=yes;')

def emniyetli_analiz(prompt):
    time.sleep(2) 
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "HATA"

# 🤖 İŞTE YENİ OTONOM AJAN MOTORUMUZ (AGENTIC ROUTER)
def otonom_ajan_karar_merkezi(metin):
    # Ajanımıza görev tanımını (System Prompt) ve karar ağacını veriyoruz
    prompt = f"""
    Sen Haliç Üniversitesi ve BTK Hackathon için geliştirilmiş otonom bir Siber Güvenlik ve Veri Analizi Ajanısın.
    Görevlerin:
    1. Gelen metni oku: '{metin}'
    2. Eğer metinde SQL Injection (DROP TABLE, SELECT vb.), XSS, HTML etiketleri veya küfür varsa eylemin "karantina" olmalı.
    3. Eğer metin normal bir müşteri yorumuysa eylemin "analiz" olmalı.
    4. Analiz ise Duygu (Pozitif/Negatif/Nötr), Konu ve Risk Skoru (0.0 ile 1.0 arası) belirle.
    
    Cevabını SADECE ve SADECE aşağıdaki JSON formatında ver, dışına tek kelime bile yazma:
    {{
        "aksiyon": "karantina_veya_analiz",
        "tehdit_nedeni": "Eğer karantinaysa buraya nedenini yaz, değilse boş bırak",
        "duygu": "duygu_durumu",
        "konu": "ana_konu",
        "risk_skoru": 0.1
    }}
    """
    
    sonuc = emniyetli_analiz(prompt)
    
    try:
        # Ajanın verdiği JSON cevabını Python sözlüğüne çeviriyoruz (Tool Use mantığı)
        # Markdown kod blokları varsa temizliyoruz
        temiz_sonuc = sonuc.replace("```json", "").replace("```", "").strip()
        ajan_karari = json.loads(temiz_sonuc)
        return ajan_karari
    except Exception as e:
        # API kotası dolarsa veya ajan hata yaparsa sistemi çökertmeyen B Planı
        return {"aksiyon": "analiz", "duygu": "Sistem Mesgul", "konu": "Hata", "risk_skoru": 0.0}

# --- 2. ARAYÜZ VE ROL YÖNETİMİ ---
st.set_page_config(page_title="SmartReview | Otonom Ajan", layout="wide", page_icon="🤖")
# Yöneticinin istatistiklerinde "KARANTİNA" verileri görünmesin diye filtreyi güncelledik
marka_filtresi = "UrunKategorisi NOT IN ('Samsung', 'SAMSUNG', 'Prima', 'PRIMA', 'KARANTİNA')"

with st.sidebar:
    # Başlığımızı da SmartReview olarak perçinliyoruz!
    st.title("🤖 SmartReview Agentic") 
    st.markdown("*Otonom Siber Güvenlik ve Veri Analitiği*")
    
    st.markdown("### 🔐 Giriş Paneli")
    kullanici_rolu = st.radio("Sisteme Kim Olarak Giriyorsunuz?", ["👤 Müşteri (Son Kullanıcı)", "💼 Yönetici (Admin Paneli)"])
    st.markdown("---")
    
    menu = None # Menü başlangıçta kapalı
    
    if kullanici_rolu == "👤 Müşteri (Son Kullanıcı)":
        st.success("Müşteri Arayüzü Aktif")
        menu = st.radio("MENÜ", ["✍️ Ürün Değerlendirme"])
    else:
        # 🔥 İŞTE YENİ ŞİFRE EKRANIMIZ
        st.info("Yönetici Yetkileri İçin Doğrulama Gerekiyor")
        sifre = st.text_input("🔑 Yönetici Şifresi (btk2026):", type="password")
        
        if sifre == "btk2026":
            st.success("✅ Giriş Başarılı!")
            menu = st.radio("MENÜ", ["📊 Genel Kontrol Paneli", "📈 İstatistiksel Analiz", "🚨 Otonom Tehdit Merkezi", "📦 Marka Özetleyici", "🥊 Rakip Kıyaslama"])
            
            st.markdown("---")
            if st.button("🗑️ Veritabanını Temizle"):
                conn = get_sql_connection()
                conn.cursor().execute("TRUNCATE TABLE ETicaret_Yorumlar")
                conn.commit()
                st.rerun()
        elif sifre != "":
            st.error("❌ Hatalı Şifre! Erişim Reddedildi.")

# --- 3. MODÜLLER ---

if menu == "✍️ Ürün Değerlendirme":
    st.header("🛍️ Müşteri Değerlendirme Formu")
    st.markdown("Alışveriş deneyiminizi paylaşın!")
    
    marka_secimi = st.selectbox("Marka Seçin:", ["Hepsiburada", "LCW", "Apple", "Xiaomi", "Diğer"])
    yorum_input = st.text_area("Yorumunuz:", height=150)
    
    if st.button("Yorumu Gönder"):
        if yorum_input:
            with st.spinner('Otonom Ajan veriyi işliyor...'):
                # Ajan devreye girer ve JSON kararı döner
                ajan_karari = otonom_ajan_karar_merkezi(yorum_input)
                conn = get_sql_connection()
                cursor = conn.cursor()
                
                if ajan_karari.get("aksiyon") == "karantina":
                    # HONEYPOT (BAL KÜPÜ) DEVREDE!
                    # Saldırganı uyarmıyoruz, veriyi "KARANTİNA" kategorisiyle gizlice kaydediyoruz
                    cursor.execute("INSERT INTO ETicaret_Yorumlar (UrunKategorisi, YorumMetni, DuyguDurumu, AnaKonu, RiskSkoru) VALUES (?, ?, ?, ?, ?)",
                                   ("KARANTİNA", yorum_input, "Tehdit", ajan_karari.get("tehdit_nedeni", "Bilinmiyor"), 1.0))
                    conn.commit()
                    # Müşteri (Hacker) başardığını sanıyor!
                    st.success("🎉 Teşekkürler! Yorumunuz başarıyla kaydedildi.") 
                else:
                    # Normal işlem
                    cursor.execute("INSERT INTO ETicaret_Yorumlar (UrunKategorisi, YorumMetni, DuyguDurumu, AnaKonu, RiskSkoru) VALUES (?, ?, ?, ?, ?)",
                                   (marka_secimi, yorum_input, ajan_karari.get("duygu"), ajan_karari.get("konu"), ajan_karari.get("risk_skoru")))
                    conn.commit()
                    st.success("🎉 Teşekkürler! Yorumunuz başarıyla kaydedildi.")

# --- YENİ: YÖNETİCİ OTONOM TEHDİT MERKEZİ ---
elif menu == "🚨 Otonom Tehdit Merkezi":
    st.header("🚨 Karantina ve Bal Küpü (HoneyPot) Kayıtları")
    st.markdown("Otonom ajanımızın saldırganlara hissettirmeden yakalayıp karantinaya aldığı siber tehditler aşağıdadır.")
    try:
        conn = get_sql_connection()
        # Sadece KARANTİNA olanları çekiyoruz
        karantina_df = pd.read_sql("SELECT KayitTarihi, YorumMetni AS [Zararlı Kod/Girdi], AnaKonu AS [Tehdit Nedeni] FROM ETicaret_Yorumlar WHERE UrunKategorisi = 'KARANTİNA' ORDER BY KayitTarihi DESC", conn)
        
        if not karantina_df.empty:
            st.error(f"⚠️ Ajan Tarafından Engellenen Tehdit Sayısı: {len(karantina_df)}")
            st.dataframe(karantina_df, use_container_width=True)
        else:
            st.success("✅ Otonom ajan herhangi bir siber tehdit tespit etmedi. Sistem güvende.")
    except:
        st.error("Veritabanı bağlantı hatası.")

# DİĞER MODÜLLER (Aynı şekilde çalışıyor, filtrelenmiş veriyi alıyor)
elif menu == "📊 Genel Kontrol Paneli":
    st.header("📊 Mağaza Genel Durum Analizi")
    try:
        df = pd.read_sql(f"SELECT * FROM ETicaret_Yorumlar WHERE {marka_filtresi}", get_sql_connection())
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Temiz Veri", len(df))
            c2.metric("Pozitif Oranı", f"%{int((len(df[df['DuyguDurumu'] == 'Pozitif']) / len(df)) * 100)}")
            c3.metric("Risk Ortalaması", round(df['RiskSkoru'].mean(), 2))
            st.dataframe(df.head(20), use_container_width=True)
        else:
            st.info("Veritabanı boş.")
    except:
        st.error("Veritabanı bağlantısı hatası.")

elif menu == "📈 İstatistiksel Analiz":
    st.header("📈 Gelişmiş İstatistiksel Göstergeler")
    try:
        df = pd.read_sql(f"SELECT * FROM ETicaret_Yorumlar WHERE {marka_filtresi}", get_sql_connection())
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Duygu Dağılımı")
                fig1, ax1 = plt.subplots()
                df['DuyguDurumu'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax1, colors=['#00C49F', '#FF8042', '#FFBB28'])
                st.pyplot(fig1)
            with col2:
                st.subheader("Risk Yoğunluğu")
                fig2, ax2 = plt.subplots()
                ax2.hist(df['RiskSkoru'], bins=10, color='#3498db')
                st.pyplot(fig2)
            st.subheader("Marka/Risk Saçılımı")
            st.scatter_chart(df, x='UrunKategorisi', y='RiskSkoru', color='DuyguDurumu')
        else:
            st.info("Veritabanı boş.")
    except:
        st.warning("Veri bekleniyor...")

elif menu == "📦 Marka Özetleyici":
    st.header("📦 Yapay Zeka Strateji Raporu")
    try:
        conn = get_sql_connection()
        m_df = pd.read_sql(f"SELECT DISTINCT UrunKategorisi FROM ETicaret_Yorumlar WHERE {marka_filtresi}", conn)
        if not m_df.empty:
            secilen = st.selectbox("Marka Seç:", m_df['UrunKategorisi'].tolist())
            if st.button("Raporu Hazırla"):
                y_df = pd.read_sql(f"SELECT YorumMetni FROM ETicaret_Yorumlar WHERE UrunKategorisi='{secilen}'", conn)
                st.write(emniyetli_analiz(f"{secilen} markası için özet çıkar: {' | '.join(y_df['YorumMetni'].tolist()[:10])}"))
        else:
            st.info("Veritabanı boş.")
    except:
        st.info("Veri bulunamadı.")

elif menu == "🥊 Rakip Kıyaslama":
    st.header("🥊 Sektörel Arena")
    try:
        conn = get_sql_connection()
        m_df = pd.read_sql(f"SELECT DISTINCT UrunKategorisi FROM ETicaret_Yorumlar WHERE {marka_filtresi}", conn)
        m_list = m_df['UrunKategorisi'].tolist()
        if len(m_list) >= 2:
            with st.form("arena_form"):
                c1, c2 = st.columns(2)
                ma = c1.selectbox("Senin Markan:", m_list)
                mb = c2.selectbox("Rakip Marka:", [x for x in m_list if x != ma])
                if st.form_submit_button("Kapıştır!"):
                    y_a = pd.read_sql(f"SELECT YorumMetni FROM ETicaret_Yorumlar WHERE UrunKategorisi='{ma}'", conn)
                    y_b = pd.read_sql(f"SELECT YorumMetni FROM ETicaret_Yorumlar WHERE UrunKategorisi='{mb}'", conn)
                    p = f"{ma} ve {mb} yorumlarını kıyasla: A: {' '.join(y_a['YorumMetni'].tolist()[:5])} | B: {' '.join(y_b['YorumMetni'].tolist()[:5])}"
                    st.write(emniyetli_analiz(p))
        else:
            st.warning("En az 2 farklı marka lazım.")
    except:
        st.error("Bir hata oluştu.")