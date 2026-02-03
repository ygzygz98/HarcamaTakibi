import flet as ft
import requests
import json
import base64
from datetime import datetime

# --- SABİT AYARLAR ---
VARSAYILAN_KATEGORILER = ["Market", "Yemek", "Tekel", "Ulaşım", "Fatura", "Giyim", "Eğitim", "Sağlık", "Diğer"]

def main(page: ft.Page):
    page.title = "Harcama Takibi"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = "auto"
    
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # --- VERİTABANI YARDIMCILARI ---
    def veri_getir(anahtar, varsayilan):
        try: return page.client_storage.get(anahtar) or varsayilan
        except: return varsayilan

    def veri_kaydet(anahtar, veri):
        page.client_storage.set(anahtar, veri)

    # --- HAFİF YAPAY ZEKA (REST API) ---
    def ai_analiz_et(metin_girdisi, resim_bytes=None):
        api_key = veri_getir("gemini_api_key", "")
        if not api_key:
            page.show_snack_bar(ft.SnackBar(ft.Text("Lütfen Ayarlar'dan API Key girin!"), bgcolor="red"))
            return None

        # Google'ın kapı adresi (URL)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        # İstek Paketi Hazırlama
        parts = []
        
        # 1. Metin Ekle
        prompt_text = """
        Sen bir muhasebe asistanısın. Gelen veriyi analiz et.
        Yanıtı SADECE şu JSON formatında ver, başka hiçbir şey yazma:
        {
            "urun": "Kısa ürün adı",
            "kategori": "Market, Yemek, Tekel, Ulaşım, Fatura, Giyim, Diğer (En uygunu)",
            "tutar": 0.0,
            "tarih": "GG.AA.YYYY" (Yoksa bugün)
        }
        """
        parts.append({"text": prompt_text})
        
        if metin_girdisi:
             parts.append({"text": f"Kullanıcı notu: {metin_girdisi}"})

        # 2. Resim Varsa Ekle (Base64'e çevirip yolluyoruz)
        if resim_bytes:
            b64_data = base64.b64encode(resim_bytes).decode('utf-8')
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_data
                }
            })

        payload = {
            "contents": [{"parts": parts}]
        }

        try:
            btn_ai_islem.visible = True
            page.update()
            
            # Postacı yola çıkıyor (Ağır kütüphane yok, sadece istek var)
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            
            if response.status_code != 200:
                hata_mesaji = f"Hata: {response.status_code} - {response.text}"
                print(hata_mesaji)
                page.show_snack_bar(ft.SnackBar(ft.Text("Google yanıt vermedi, API Key doğru mu?"), bgcolor="red"))
                return None

            # Yanıtı çözümle
            sonuc_json = response.json()
            # Google'ın karmaşık yanıtından metni cımbızla çekiyoruz
            text_yanit = sonuc_json['candidates'][0]['content']['parts'][0]['text']
            
            # JSON temizliği (Bazen ```json etiketiyle yolluyor)
            temiz_veri = text_yanit.replace("```json", "").replace("```", "").strip()
            return json.loads(temiz_veri)
            
        except Exception as e:
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Bağlantı Hatası: {str(e)}"), bgcolor="red"))
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
            
            page.show_snack_bar(ft.SnackBar(ft.Text("Fiş okunuyor... 📸"), bgcolor="blue"))
            sonuc = ai_analiz_et("", resim_bytes)
            if sonuc: verileri_doldur(sonuc)

    def metinle_doldur(e):
        if not urun_adi.value: return
        if len(urun_adi.value.split()) > 1 or any(char.isdigit() for char in urun_adi.value):
            page.show_snack_bar(ft.SnackBar(ft.Text("Yazı analiz ediliyor... 🤖"), bgcolor="blue"))
            sonuc = ai_analiz_et(urun_adi.value)
            if sonuc: verileri_doldur(sonuc)

    def verileri_doldur(veri):
        urun_adi.value = veri.get("urun", "")
        txt_toplam_tutar.value = str(veri.get("tutar", 0))
        txt_birim_fiyat.value = str(veri.get("tutar", 0))
        txt_adet.value = "1"
        
        gelen_kategori = veri.get("kategori", "Diğer")
        mevcut_kat = veri_getir("kategoriler", VARSAYILAN_KATEGORILER)
        kategori.value = gelen_kategori if gelen_kategori in mevcut_kat else "Diğer"
            
        tarih_kutusu.value = veri.get("tarih", datetime.now().strftime("%d.%m.%Y"))
        page.show_snack_bar(ft.SnackBar(ft.Text("Otomatik Dolduruldu! ✨"), bgcolor="green"))
        page.update()

    # --- STANDART FONKSİYONLAR ---
    def harcamalari_oku(): return veri_getir("harcamalar", [])
    
    def kaydet_tikla(e):
        try: tutar = float(txt_toplam_tutar.value)
        except: return
            
        yeni_veri = {
            "tarih": tarih_kutusu.value, "kategori": kategori.value,
            "urun": urun_adi.value, "tutar": tutar
        }
        liste = harcamalari_oku()
        liste.append(yeni_veri)
        veri_kaydet("harcamalar", liste)
        
        urun_adi.value = ""
        txt_toplam_tutar.value = "0.00"
        liste_guncelle()

    def liste_guncelle():
        veriler = harcamalari_oku()
        veriler.sort(key=lambda x: datetime.strptime(x['tarih'], "%d.%m.%Y"), reverse=True)
        liste_kutusu.controls.clear()
        txt_ozet.value = f"Toplam: {sum(x['tutar'] for x in veriler):,.2f} TL"

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
    txt_api_key = ft.TextField(label="Gemini API Key", password=True, can_reveal_password=True)
    bs_ayarlar = ft.BottomSheet(
        ft.Container(
            ft.Column([ft.Text("Ayarlar", size=20, weight="bold"), txt_api_key, ft.ElevatedButton("Kaydet", on_click=api_key_kaydet)], tight=True),
            padding=20, bgcolor="#1f1f1f"
        )
    )

    tarih_kutusu = ft.TextField(label="Tarih", value=datetime.now().strftime("%d.%m.%Y"), expand=True, height=40, text_size=13)
    kategori = ft.Dropdown(options=[ft.dropdown.Option(x) for x in VARSAYILAN_KATEGORILER], value="Diğer", label="Kategori", expand=True, height=40, text_size=13)
    urun_adi = ft.TextField(label="Ne aldın? (veya Fiş Yükle)", hint_text="Örn: Migros 500", expand=True, on_submit=metinle_doldur, text_size=14)
    btn_ai_islem = ft.ProgressRing(width=20, height=20, visible=False)
    
    txt_adet = ft.TextField(label="Adet", value="1", width=50, text_size=13)
    txt_birim_fiyat = ft.TextField(label="Birim", width=80, text_size=13)
    txt_toplam_tutar = ft.TextField(label="Toplam", value="0.00", width=100, text_size=13, weight="bold")
    file_picker.on_result = fis_yukle
    liste_kutusu = ft.Column()
    txt_ozet = ft.Text("Toplam: 0.00 TL", size=16, weight="bold")

    page.add(
        ft.Row([ft.Text("HarcamaTakibi", size=18, weight="bold", color="blue"), ft.IconButton(icon="settings", on_click=lambda e: page.open(bs_ayarlar))], alignment="spaceBetween"),
        ft.Divider(),
        ft.Column([
            ft.Row([tarih_kutusu, kategori]),
            ft.Row([urun_adi, ft.IconButton(icon="attach_file", icon_color="orange", on_click=lambda _: file_picker.pick_files(allow_multiple=False)), btn_ai_islem]),
            ft.Row([txt_adet, txt_birim_fiyat, txt_toplam_tutar], alignment="spaceBetween"),
            ft.ElevatedButton("KAYDET", width=400, bgcolor="blue", color="white", on_click=kaydet_tikla)
        ]),
        ft.Divider(), txt_ozet, liste_kutusu
    )
    
    txt_api_key.value = veri_getir("gemini_api_key", "")
    liste_guncelle()

ft.app(target=main)
