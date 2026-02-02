import flet as ft
from datetime import datetime

# Not: JSON kütüphanesine artık ihtiyacımız yok, 
# çünkü Flet'in kendi hafızasını kullanacağız.

# Varsayılan Kategoriler
VARSAYILAN_KATEGORILER = ["Market", "Yemek", "Tekel", "Ulaşım", "Fatura", "Giyim", "Diğer"]

# Renk Paleti
GRAFIK_RENKLERI = [
    "#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#009688", 
    "#E91E63", "#00BCD4", "#3F51B5", "#CDDC39", "#FFC107", "#795548"
]

def main(page: ft.Page):
    # --- AYARLAR ---
    page.title = "Mekanik Bütçe"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.window_width = 390
    page.window_height = 844
    page.scroll = "auto" # Sayfa kaydırma açık

    # Düzenleme için geçici değişken
    duzenlenecek_eski_veri = None 

    # --- HAFIZA (STORAGE) İŞLERİ (YENİLENDİ) ---
    # Artık dosya yerine page.client_storage kullanıyoruz.
    # Bu yöntem telefonda %100 güvenli çalışır.

    def veri_getir(anahtar, varsayilan):
        # Hafızadan veri çeker, yoksa varsayılanı döndürür
        try:
            return page.client_storage.get(anahtar) or varsayilan
        except:
            return varsayilan

    def veri_kaydet(anahtar, veri):
        # Hafızaya kaydeder
        page.client_storage.set(anahtar, veri)

    # --- OKUMA/YAZMA SARMALAYICILARI ---
    def harcamalari_oku():
        return veri_getir("harcamalar", [])

    def harcamalari_yaz(liste):
        veri_kaydet("harcamalar", liste)

    def butce_sozlugu_oku():
        return veri_getir("butce_sozlugu", {})

    def butce_sozlugu_yaz(sozluk):
        veri_kaydet("butce_sozlugu", sozluk)

    def kategorileri_oku():
        return veri_getir("kategoriler", VARSAYILAN_KATEGORILER.copy())

    def kategorileri_kaydet(liste):
        veri_kaydet("kategoriler", liste)

    # --- BÜTÇE İŞLEMLERİ ---
    def butce_getir(ay, yil):
        d = butce_sozlugu_oku()
        return d.get(f"{ay}-{yil}", 0.0)

    def butce_kaydet(ay, yil, tutar):
        d = butce_sozlugu_oku()
        d[f"{ay}-{yil}"] = tutar
        butce_sozlugu_yaz(d)

    # --- KATEGORİ YÖNETİMİ ---
    def panel_kategori_ciz():
        col_ozel_kategoriler.controls.clear()
        mevcut = kategorileri_oku()
        for k in mevcut:
            col_ozel_kategoriler.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(k, color="white"),
                        ft.IconButton(icon="delete_outline", icon_color="red", icon_size=20, on_click=lambda e, x=k: kategori_sil(x))
                    ], alignment="spaceBetween"),
                    bgcolor="#333333", padding=5, border_radius=5, margin=2
                )
            )
        page.update()

    def kategori_yonet_ac(e):
        container_kat_yonet.visible = not container_kat_yonet.visible
        if container_kat_yonet.visible:
            panel_kategori_ciz()
        page.update()

    def kategori_ekle(e):
        if not txt_yeni_kat.value: return
        mevcut = kategorileri_oku()
        if txt_yeni_kat.value not in mevcut:
            mevcut.append(txt_yeni_kat.value)
            kategorileri_kaydet(mevcut)
            txt_yeni_kat.value = ""
            panel_kategori_ciz()
            dropdown_guncelle()
            page.show_snack_bar(ft.SnackBar(ft.Text("Kategori Eklendi!"), bgcolor="green"))
            page.update()

    def kategori_sil(isim):
        mevcut = kategorileri_oku()
        if isim in mevcut:
            mevcut.remove(isim)
            kategorileri_kaydet(mevcut)
            panel_kategori_ciz()
            dropdown_guncelle()
            page.update()

    def dropdown_guncelle():
        yeni_liste = kategorileri_oku()
        kategori.options = [ft.dropdown.Option(x) for x in yeni_liste]
        # Eğer seçili kategori silindiyse boşalt
        if kategori.value not in yeni_liste: 
            kategori.value = None
        page.update()

    # --- HARCAMA İŞLEMLERİ ---
    def harcama_sil(veri_silinecek):
        tum_veriler = harcamalari_oku()
        # Listeden silme işlemi (Birebir eşleşen veriyi bulur)
        if veri_silinecek in tum_veriler:
            tum_veriler.remove(veri_silinecek)
            harcamalari_yaz(tum_veriler)
            dashboard_guncelle()
            page.show_snack_bar(ft.SnackBar(ft.Text("Harcama Silindi! 🗑️"), bgcolor="#e74c3c"))
            page.update()

    def duzenle_modunu_ac(veri):
        nonlocal duzenlenecek_eski_veri
        tarih_kutusu.value = veri["tarih"]
        kategori.value = veri["kategori"]
        urun_adi.value = veri["urun"]
        
        # Adet ve Birim Fiyatı Güvenli Çek
        adet_degeri = str(veri.get("adet", "1"))
        birim_degeri = str(veri.get("birim_fiyat", veri["tutar"]))
        
        txt_adet.value = adet_degeri
        txt_birim_fiyat.value = birim_degeri
        txt_toplam_tutar.value = str(veri["tutar"])
        
        duzenlenecek_eski_veri = veri
        
        # Butonu Güncelleme Moduna Al
        btn_kaydet.text = "GÜNCELLE"
        btn_kaydet.icon = "update"
        btn_kaydet.bgcolor = "orange"
        
        urun_adi.focus()
        page.update()

    def tutar_hesapla(e):
        try:
            adet_text = txt_adet.value.replace(",", ".") if txt_adet.value else "0"
            birim_text = txt_birim_fiyat.value.replace(",", ".") if txt_birim_fiyat.value else "0"
            adet = float(adet_text)
            birim = float(birim_text)
            toplam = adet * birim
            txt_toplam_tutar.value = f"{toplam:.2f}"
        except:
            txt_toplam_tutar.value = "0.00"
        page.update()

    def kaydet_tikla(e):
        nonlocal duzenlenecek_eski_veri
        
        if not urun_adi.value:
            page.show_snack_bar(ft.SnackBar(ft.Text("Ürün adı giriniz!"), bgcolor="red"))
            return

        try:
            adet = float(txt_adet.value.replace(",", ".")) if txt_adet.value else 1.0
            birim = float(txt_birim_fiyat.value.replace(",", ".")) if txt_birim_fiyat.value else 0.0
            toplam = adet * birim
        except:
            page.show_snack_bar(ft.SnackBar(ft.Text("Lütfen geçerli sayılar girin!"), bgcolor="red"))
            return
        
        if toplam <= 0:
            page.show_snack_bar(ft.SnackBar(ft.Text("Tutar 0 olamaz!"), bgcolor="red"))
            return

        yeni_veri = {
            "tarih": tarih_kutusu.value,
            "kategori": kategori.value,
            "urun": urun_adi.value,
            "adet": adet,
            "birim_fiyat": birim,
            "tutar": toplam
        }
        
        tum_veriler = harcamalari_oku()

        if btn_kaydet.text == "GÜNCELLE":
            # Eski veriyi sil, yeniyi ekle
            # Not: Listeler arası karşılaştırma referans değil içerik bazlıdır
            if duzenlenecek_eski_veri in tum_veriler:
                tum_veriler.remove(duzenlenecek_eski_veri)
            
            tum_veriler.append(yeni_veri)
            harcamalari_yaz(tum_veriler)
            page.show_snack_bar(ft.SnackBar(ft.Text("Güncellendi! ✨"), bgcolor="orange"))
            
            # Modu Normale Döndür
            btn_kaydet.text = "KAYDET"
            btn_kaydet.icon = "save"
            btn_kaydet.bgcolor = "#007acc"
            duzenlenecek_eski_veri = None
        else:
            tum_veriler.append(yeni_veri)
            harcamalari_yaz(tum_veriler)
            page.show_snack_bar(ft.SnackBar(ft.Text("Kaydedildi!"), bgcolor="green"))

        # Formu Temizle
        urun_adi.value = ""
        txt_adet.value = "1"
        txt_birim_fiyat.value = ""
        txt_toplam_tutar.value = "0.00"
        urun_adi.focus()
        
        dashboard_guncelle()
        page.update()

    def grafik_ac_kapa(e):
        kapsayici_grafik.visible = not kapsayici_grafik.visible
        if kapsayici_grafik.visible:
            btn_grafik_toggle.icon = "expand_less"
            btn_grafik_toggle.text = "Analizi Gizle"
        else:
            btn_grafik_toggle.icon = "pie_chart"
            btn_grafik_toggle.text = "Analizi Göster"
        page.update()

    def arama_yap(e):
        dashboard_guncelle()

    def dashboard_guncelle(e=None):
        secili_ay = dd_ay.value
        secili_yil = dd_yil.value
        arama_metni = txt_arama.value.lower() if txt_arama.value else ""
        arama_modu = len(arama_metni) > 0 

        tum_veriler = harcamalari_oku()
        filtrelenmis = []
        
        for v in tum_veriler:
            try:
                if arama_modu:
                    # Arama Modu: Tarihe bakma, her yerde ara
                    if arama_metni in v["urun"].lower() or arama_metni in v["kategori"].lower():
                        filtrelenmis.append(v)
                else:
                    # Normal Mod: Tarihe ve aya bak
                    p = v["tarih"].split(".")
                    if len(p) == 3 and p[1] == secili_ay and p[2] == secili_yil:
                        filtrelenmis.append(v)
            except: pass
            
        # Tarihe göre sırala (En yeni en üstte)
        filtrelenmis.sort(key=lambda x: datetime.strptime(x['tarih'], "%d.%m.%Y"), reverse=True)

        toplam = sum(x["tutar"] for x in filtrelenmis)
        
        if arama_modu:
            txt_toplam.value = f"{toplam:,.2f} TL"
            txt_butce.value = "Genel Arama Modu"
            txt_kalan.value = "Tüm Kayıtlar"
            txt_kalan.color = "white"
        else:
            butce = butce_getir(secili_ay, secili_yil)
            kalan = butce - toplam
            txt_toplam.value = f"{toplam:,.2f} TL"
            txt_butce.value = f"Bütçe ({secili_ay}/{secili_yil}): {butce:,.0f} TL"
            txt_kalan.value = f"Kalan: {kalan:,.2f} TL"
            txt_kalan.color = "#2ecc71" if kalan >= 0 else "#e74c3c"
        
        # Liste Oluşturma
        liste_kutusu.controls.clear()
        if not filtrelenmis:
            mesaj = "Sonuç bulunamadı..." if arama_modu else "Bu ay harcama yok..."
            liste_kutusu.controls.append(ft.Text(mesaj, color="grey", italic=True))
            pasta_grafigi.sections = [] 
            if not arama_modu: kapsayici_grafik.visible = False
        else:
            for v in filtrelenmis:
                liste_kutusu.controls.append(kart_olustur(v))
            
            # Grafik Verilerini Hazırla
            kat_toplamlari = {}
            for v in filtrelenmis:
                kat = v["kategori"]
                tutar = v["tutar"]
                kat_toplamlari[kat] = kat_toplamlari.get(kat, 0) + tutar
            
            sections = []
            renk_index = 0
            # Grafiği oluştur ama görünürlüğü değiştirme (Kullanıcı butona basarsa açılır)
            for kat, tut in kat_toplamlari.items():
                sections.append(
                    ft.PieChartSection(
                        value=tut,
                        title=f"{kat}\n%{int((tut/toplam)*100)}", 
                        title_style=ft.TextStyle(size=12, weight="bold", color="white"),
                        color=GRAFIK_RENKLERI[renk_index % len(GRAFIK_RENKLERI)],
                        radius=60
                    )
                )
                renk_index += 1
            pasta_grafigi.sections = sections

        page.update()

    def butce_duzenle_ac(e):
        row_butce_edit.visible = not row_butce_edit.visible
        if row_butce_edit.visible:
            mevcut = butce_getir(dd_ay.value, dd_yil.value)
            txt_yeni_butce.value = str(int(mevcut))
            txt_yeni_butce.focus()
        page.update()

    def butce_yeni_kaydet(e):
        if txt_yeni_butce.value:
            butce_kaydet(dd_ay.value, dd_yil.value, float(txt_yeni_butce.value))
            dashboard_guncelle()
            row_butce_edit.visible = False
            page.show_snack_bar(ft.SnackBar(ft.Text("Bütçe Güncellendi!"), bgcolor="#007acc"))
            page.update()

    def kart_olustur(veri):
        def sil_basildi(e): harcama_sil(veri)
        def duzenle_basildi(e): duzenle_modunu_ac(veri)
        
        adet = veri.get("adet", 1)
        birim = veri.get("birim_fiyat", veri["tutar"])
        
        if float(adet) > 1:
            urun_bilgisi = f"{veri['urun']} ({adet} x {birim} TL)"
        else:
            urun_bilgisi = veri['urun']

        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(name="receipt_long", color="grey"),
                    ft.Column([
                        ft.Text(urun_bilgisi, weight="bold"),
                        ft.Text(f"{veri['kategori']} | {veri['tarih']}", size=12, color="grey")
                    ], spacing=2)
                ]),
                ft.Row([
                    ft.Text(f"-{veri['tutar']} TL", color="#e74c3c", weight="bold", size=13),
                    ft.IconButton(icon="edit", icon_color="#007acc", icon_size=20, on_click=duzenle_basildi),
                    ft.IconButton(icon="delete_outline", icon_color="grey", icon_size=20, on_click=sil_basildi)
                ])
            ], alignment="spaceBetween"),
            bgcolor="#252526", padding=10, border_radius=10, margin=2
        )

    # --- ARAYÜZ (UI) ---
    simdi = datetime.now()
    dd_ay = ft.Dropdown(width=100, options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)], value=f"{simdi.month:02d}", label="Ay", border_color="#333333", text_size=14, on_change=dashboard_guncelle)
    dd_yil = ft.Dropdown(width=100, options=[ft.dropdown.Option(str(y)) for y in range(2025, 2030)], value=str(simdi.year), label="Yıl", border_color="#333333", text_size=14, on_change=dashboard_guncelle)

    txt_toplam = ft.Text("0.00 TL", size=24, weight="bold", color="white")
    txt_kalan = ft.Text("Kalan: 0.00 TL", size=16, color="#2ecc71")
    txt_butce = ft.Text("Bütçe: 0 TL", size=14, color="grey")
    
    txt_yeni_butce = ft.TextField(hint_text="Bütçe Gir", width=150, height=40, content_padding=10, text_size=14, keyboard_type="number", border_color="#007acc")
    btn_butce_ok = ft.IconButton(icon="check_circle", icon_color="#007acc", on_click=butce_yeni_kaydet)
    row_butce_edit = ft.Row([txt_yeni_butce, btn_butce_ok], visible=False, alignment="center")

    pasta_grafigi = ft.PieChart(sections=[], sections_space=2, center_space_radius=30, height=150)
    kapsayici_grafik = ft.Container(content=ft.Column([ft.Divider(color="grey"), ft.Text("Harcama Dağılımı", size=14, color="grey", weight="bold"), pasta_grafigi], horizontal_alignment="center"), visible=False)
    btn_grafik_toggle = ft.TextButton("Analizi Göster", icon="pie_chart", icon_color="#007acc", on_click=grafik_ac_kapa)

    dashboard_kart = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("Dönem:", color="grey"), dd_ay, dd_yil], alignment="center"),
            ft.Divider(color="grey"),
            ft.Row([ft.Text("Toplam Harcama", color="grey"), ft.Icon(name="credit_card", color="#007acc")], alignment="spaceBetween"),
            txt_toplam,
            ft.Divider(color="grey"),
            ft.Row([txt_butce, txt_kalan], alignment="spaceBetween"),
            ft.Container(height=10),
            ft.Row([ft.ElevatedButton("Bütçeyi Düzenle", icon="edit", bgcolor="#333333", color="white", height=35, on_click=butce_duzenle_ac)], alignment="center"),
            ft.Container(height=5),
            row_butce_edit,
            ft.Divider(color="grey"),
            ft.Row([btn_grafik_toggle], alignment="center"),
            kapsayici_grafik
        ]),
        bgcolor="#1e1e1e", padding=20, border=ft.border.all(1, "#333333"), border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color="#1A000000")
    )

    tarih_kutusu = ft.TextField(label="Tarih", value=simdi.strftime("%d.%m.%Y"), border_color="#007acc", icon="calendar_today")
    
    baslangic_kat = kategorileri_oku()
    kategori = ft.Dropdown(options=[ft.dropdown.Option(x) for x in baslangic_kat], value=baslangic_kat[0] if baslangic_kat else None, label="Kategori", border_color="#007acc", expand=True)
    btn_kat_yonet = ft.IconButton(icon="settings", icon_color="grey", on_click=kategori_yonet_ac)
    
    txt_yeni_kat = ft.TextField(hint_text="Yeni Kategori Ekle", expand=True, height=40, content_padding=10)
    btn_ekle_kat = ft.IconButton(icon="add_circle", icon_color="green", on_click=kategori_ekle)
    col_ozel_kategoriler = ft.Column() 
    container_kat_yonet = ft.Container(content=ft.Column([ft.Text("Kategori Yönetimi", weight="bold"), ft.Row([txt_yeni_kat, btn_ekle_kat]), ft.Divider(color="grey"), col_ozel_kategoriler]), bgcolor="#252526", padding=15, border_radius=10, visible=False, border=ft.border.all(1, "grey"))
    row_kategori = ft.Row([kategori, btn_kat_yonet], alignment="center")

    urun_adi = ft.TextField(label="Ürün Adı", border_color="#007acc")
    
    txt_adet = ft.TextField(label="Adet", value="1", expand=1, border_color="#007acc", keyboard_type="number", on_change=tutar_hesapla)
    txt_birim_fiyat = ft.TextField(label="Birim Fiyat", expand=2, suffix_text="TL", border_color="#007acc", keyboard_type="number", on_change=tutar_hesapla)
    row_fiyat_detay = ft.Row([txt_adet, ft.Container(width=10), txt_birim_fiyat])
    
    txt_toplam_tutar = ft.TextField(label="Toplam Tutar", value="0.00", suffix_text="TL", read_only=True, border_color="#2ecc71", text_style=ft.TextStyle(weight="bold", color="#2ecc71"))

    btn_kaydet = ft.ElevatedButton("KAYDET", icon="save", bgcolor="#007acc", color="white", height=50, width=400, on_click=kaydet_tikla)
    txt_arama = ft.TextField(hint_text="Harcama Ara (Tüm Zamanlar)...", prefix_icon="search", border_radius=20, height=40, content_padding=10, on_change=arama_yap)
    liste_kutusu = ft.Column()

    page.add(ft.Column([
        ft.Container(height=5), dashboard_kart, ft.Divider(),
        ft.Text("Harcama Ekle", size=18, weight="bold"),
        tarih_kutusu, row_kategori, container_kat_yonet, 
        urun_adi, 
        row_fiyat_detay, 
        txt_toplam_tutar, 
        ft.Container(height=10), btn_kaydet, ft.Divider(),
        ft.Row([ft.Text("Dönem Hareketleri", size=14, color="grey"), ft.Container(width=10), ft.Container(content=txt_arama, width=200)], alignment="spaceBetween"),
        liste_kutusu
    ]))
    
    dashboard_guncelle()

ft.app(target=main)