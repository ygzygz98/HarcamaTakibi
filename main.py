import flet as ft
import google.generativeai as genai
import json
from datetime import datetime

# --- SABİT AYARLAR ---
VARSAYILAN_KATEGORILER = ["Market", "Yemek", "Tekel", "Ulaşım", "Fatura", "Giyim", "Eğitim", "Sağlık", "Diğer"]
GRAFIK_RENKLERI = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#009688", "#E91E63", "#00BCD4"]

def main(page: ft.Page):
    page.title = "Harcama Takibi"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = "auto"
    
    # Dosya secici (FilePicker) tanimlama
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # --- VERİTABANI YARDIMCILARI ---
    def veri_getir(anahtar, varsayilan):
        try: return page.client_storage.get(anahtar) or varsayilan
        except: return varsayilan

    def veri_kaydet(anahtar, veri):
        page.client_storage.set(anahtar, veri)

    # --- YAPAY ZEKA (GEMINI) ---
    def gemini_yapilandir():
        api_key = veri_getir("gemini_api_key", "")
        if api_key:
            genai.configure(api_key=api_key)
            return True
        return False

    def ai_analiz_et(girdi, resim_data=None):
        if not gemini_yapilandir():
            page.show_snack_bar(ft.SnackBar(ft.Text("Lütfen Ayarlar'dan API Key girin!"), bgcolor="red"))
            return None

        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Sen bir muhasebe asistanısın. Gönderilen fiş fotoğrafını veya metni analiz et.
        Şu JSON formatında yanıt ver (Sadece JSON):
        {
            "urun": "Kısa ürün/mekan adı",
            "kategori": "Market, Yemek, Tekel, Ulaşım, Fatura, Giyim, Diğer (Bunlardan en uygununu seç)",
            "tutar": 0.0,
            "tarih": "GG.AA.YYYY" (Eğer metinde/fişte yoksa bugünün tarihi)
        }
        """
        
        try:
            btn_ai_islem.visible = True # Yükleniyor göstergesi
            page.update()
            
            response = None
            if resim_data:
                # Resimli Analiz
                img_part = {"mime_type": "image/jpeg", "data": resim_data}
                response = model.generate_content([prompt, img_part])
            else:
                # Metin Analizi
                response = model.generate_content([prompt, girdi])

            temiz_veri = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(temiz_veri)
            
        except Exception as e:
            page.show_snack_bar(ft.SnackBar(ft.Text(f"AI Hatası: {str(e)}"), bgcolor="red"))
            return None
        finally:
            btn_ai_islem.visible = False
            page.update()

    # --- İŞLEVLER ---
    def fis_yukle(e: ft.FilePickerResultEvent):
        if e.files:
            dosya = e.files[0]
            with open(dosya.path, "rb") as f:
                resim_bytes = f.read()
            
            page.show_snack_bar(ft.SnackBar(ft.Text("Fiş okunuyor, lütfen bekleyin... 🤖"), bgcolor="blue"))
            sonuc = ai_analiz_et("", resim_data=resim_bytes)
            
            if sonuc:
                verileri_doldur(sonuc)

    def metinle_doldur(e):
        if not urun_adi.value: return
        # Eğer metin uzunsa veya sayı içeriyorsa AI'ya sor
        if len(urun_adi.value.split()) > 1 or any(char.isdigit() for char in urun_adi.value):
            page.show_snack_bar(ft.SnackBar(ft.Text("Yazı analiz ediliyor... 🤖"), bgcolor="blue"))
            sonuc = ai_analiz_et(urun_adi.value)
            if sonuc:
                verileri_doldur(sonuc)

    def verileri_doldur(veri):
        urun_adi.value = veri.get("urun", "")
        txt_toplam_tutar.value = str(veri.get("tutar", 0))
        txt_birim_fiyat.value = str(veri.get("tutar", 0))
        txt_adet.value = "1"
        
        gelen_kategori = veri.get("kategori", "Diğer")
        mevcut_kat = veri_getir("kategoriler", VARSAYILAN_KATEGORILER)
        
        if gelen_kategori in mevcut_kat:
            kategori.value = gelen_kategori
        else:
            kategori.value = "Diğer"
            
        tarih_kutusu.value = veri.get("tarih", datetime.now().strftime("%d.%m.%Y"))
        
        page.show_snack_bar(ft.SnackBar(ft.Text("Bilgiler Otomatik Dolduruldu! ✨"), bgcolor="green"))
        page.update()

    # --- STANDART FONKSİYONLAR (KAYDET, SİL VS) ---
    def harcamalari_oku(): return veri_getir("harcamalar", [])
    
    def kaydet_tikla(e):
        try:
            tutar = float(txt_toplam_tutar.value)
        except:
            page.show_snack_bar(ft.SnackBar(ft.Text("Tutar hatalı!"), bgcolor="red"))
            return
            
        yeni_veri = {
            "tarih": tarih_kutusu.value,
            "kategori": kategori.value,
            "urun": urun_adi.value,
            "tutar": tutar
        }
        
        liste = harcamalari_oku()
        liste.append(yeni_veri)
        veri_kaydet("harcamalar", liste)
        
        urun_adi.value = ""
        txt_toplam_tutar.value = "0.00"
        txt_birim_fiyat.value = ""
        liste_guncelle()
        page.show_snack_bar(ft.SnackBar(ft.Text("Kaydedildi!"), bgcolor="green"))

    def liste_guncelle():
        veriler = harcamalari_oku()
        veriler.sort(key=lambda x: datetime.strptime(x['tarih'], "%d.%m.%Y"), reverse=True)
        liste_kutusu.controls.clear()
        
        toplam = sum(x['tutar'] for x in veriler)
        txt_ozet.value = f"Toplam: {toplam:,.2f} TL"

        for v in veriler:
            liste_kutusu.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([ft.Text(v['urun'], weight="bold"), ft.Text(f"{v['kategori']} | {v['tarih']}", size=12, color="grey")]),
                        ft.Text(f"-{v['tutar']} TL", color="#e74c3c", weight="bold")
                    ], alignment="spaceBetween"),
                    bgcolor="#252526", padding=10, border_radius=8, margin=1
                )
            )
        page.update()

    def api_key_kaydet(e):
        veri_kaydet("gemini_api_key", txt_api_key.value)
        bs_ayarlar.open = False
        page.show_snack_bar(ft.SnackBar(ft.Text("Anahtar Kaydedildi!"), bgcolor="green"))
        page.update()

    # --- ARAYÜZ ---
    txt_api_key = ft.TextField(label="Gemini API Key (AIza...)", password=True, can_reveal_password=True)
    bs_ayarlar = ft.BottomSheet(
        ft.Container(
            ft.Column([
                ft.Text("Ayarlar", size=20, weight="bold"),
                ft.Text("Google AI Studio'dan aldığınız API Key'i girin:", size=12, color="grey"),
                txt_api_key,
                ft.ElevatedButton("Kaydet", on_click=api_key_kaydet)
            ], tight=True),
            padding=20, bgcolor="#1f1f1f"
        )
    )

    tarih_kutusu = ft.TextField(label="Tarih", value=datetime.now().strftime("%d.%m.%Y"), expand=True, height=40, text_size=13)
    kategori = ft.Dropdown(options=[ft.dropdown.Option(x) for x in VARSAYILAN_KATEGORILER], value="Diğer", label="Kategori", expand=True, height=40, text_size=13)
    
    urun_adi = ft.TextField(
        label="Ne aldın? (veya Fiş Yükle)", 
        hint_text="Örn: Migros 500 TL",
        expand=True, 
        on_submit=metinle_doldur, # Enter'a basınca AI çalışır
        text_size=14
    )
    
    # AI Yükleniyor ikonu
    btn_ai_islem = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

    txt_adet = ft.TextField(label="Adet", value="1", width=50, text_size=13)
    txt_birim_fiyat = ft.TextField(label="Birim", width=80, text_size=13)
    txt_toplam_tutar = ft.TextField(label="Toplam", value="0.00", width=100, text_size=13, weight="bold")

    file_picker.on_result = fis_yukle
    
    liste_kutusu = ft.Column()
    txt_ozet = ft.Text("Toplam: 0.00 TL", size=16, weight="bold")

    # Üst Bar
    header = ft.Row([
        ft.Text("HarcamaTakibi", size=18, weight="bold", color="blue"),
        ft.IconButton(icon="settings", on_click=lambda e: page.open(bs_ayarlar))
    ], alignment="spaceBetween")

    # Giriş Formu
    form = ft.Column([
        ft.Row([tarih_kutusu, kategori]),
        ft.Row([
            urun_adi, 
            ft.IconButton(icon="attach_file", icon_color="orange", on_click=lambda _: file_picker.pick_files(allow_multiple=False)),
            btn_ai_islem
        ]),
        ft.Row([txt_adet, txt_birim_fiyat, txt_toplam_tutar], alignment="spaceBetween"),
        ft.ElevatedButton("KAYDET", width=400, bgcolor="blue", color="white", on_click=kaydet_tikla)
    ])

    page.add(
        header,
        ft.Divider(),
        form,
        ft.Divider(),
        txt_ozet,
        liste_kutusu
    )
    
    # Başlangıçta key var mı kontrol et
    mevcut_key = veri_getir("gemini_api_key", "")
    txt_api_key.value = mevcut_key
    liste_guncelle()

ft.app(target=main)
