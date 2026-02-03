import flet as ft
from datetime import datetime

# --- SABİT AYARLAR ---
VARSAYILAN_KATEGORILER = ["Market", "Yemek", "Tekel", "Ulaşım", "Fatura", "Giyim", "Diğer"]
GRAFIK_RENKLERI = [
    "#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#009688", 
    "#E91E63", "#00BCD4", "#3F51B5", "#CDDC39", "#FFC107", "#795548"
]

def main(page: ft.Page):
    # --- SAYFA AYARLARI ---
    page.title = "Harcama Takibi"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = "auto"

    duzenlenecek_eski_veri = None 

    # --- HAFIZA (DATABASE) ---
    def veri_getir(anahtar, varsayilan):
        try: return page.client_storage.get(anahtar) or varsayilan
        except: return varsayilan

    def veri_kaydet(anahtar, veri):
        page.client_storage.set(anahtar, veri)

    def harcamalari_oku(): return veri_getir("harcamalar", [])
    def harcamalari_yaz(liste): veri_kaydet("harcamalar", liste)
    def butce_sozlugu_oku(): return veri_getir("butce_sozlugu", {})
    def butce_sozlugu_yaz(sozluk): veri_kaydet("butce_sozlugu", sozluk)
    def kategorileri_oku(): return veri_getir("kategoriler", VARSAYILAN_KATEGORILER.copy())
    def kategorileri_kaydet(liste): veri_kaydet("kategoriler", liste)

    def butce_getir(ay, yil):
        return butce_sozlugu_oku().get(f"{ay}-{yil}", 0.0)

    def butce_kaydet(ay, yil, tutar):
        d = butce_sozlugu_oku()
        d[f"{ay}-{yil}"] = tutar
        butce_sozlugu_yaz(d)

    # --- ANALİZ FONKSİYONLARI (YENİ EKLENDİ) ---
    def istatistik_hesapla(filtrelenmis_veri):
        if not filtrelenmis_veri:
            return "Veri Yok", "Veri Yok"
        
        # 1. En Çok Harcanan Kategori
        kat_toplam = {}
        for v in filtrelenmis_veri:
            kat = v["kategori"]
            kat_toplam[kat] = kat_toplam.get(kat, 0) + v["tutar"]
        
        sampiyon_kat = max(kat_toplam, key=kat_toplam.get)
        sampiyon_tutar = kat_toplam[sampiyon_kat]
        
        # 2. En Pahalı Tek Harcama
        en_pahali = max(filtrelenmis_veri, key=lambda x: x["tutar"])
        
        metin_kat = f"{sampiyon_kat}\n{sampiyon_tutar:,.0f} TL"
        metin_pahali = f"{en_pahali['urun']}\n{en_pahali['tutar']:,.0f} TL"
        
        return metin_kat, metin_pahali

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
        if container_kat_yonet.visible: panel_kategori_ciz()
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
        if kategori.value not in yeni_liste: kategori.value = None
        page.update()

    # --- HARCAMA İŞLEMLERİ ---
    def harcama_sil(veri_silinecek):
        tum_veriler = harcamalari_oku()
        if veri_silinecek in tum_veriler:
            tum_veriler.remove(veri_silinecek)
            harcamalari_yaz(tum_veriler)
            dashboard_guncelle()
            page.show_snack_bar(ft.SnackBar(ft.Text("Silindi! 🗑️"), bgcolor="#e74c3c"))

    def duzenle_modunu_ac(veri):
        nonlocal duzenlenecek_eski_veri
        tarih_kutusu.value = veri["tarih"]
        kategori.value = veri["kategori"]
        urun_adi.value = veri["urun"]
        txt_adet.value = str(veri.get("adet", "1"))
        txt_birim_fiyat.value = str(veri.get("birim_fiyat", veri["tutar"]))
        txt_toplam_tutar.value = str(veri["tutar"])
        duzenlenecek_eski_veri = veri
        
        btn_kaydet.text = "GÜNCELLE"
        btn_kaydet.icon = "update"
        btn_kaydet.bgcolor = "orange"
        page.update()

    def tutar_hesapla(e):
        try:
            adet = float(txt_adet.value.replace(",", ".") if txt_adet.value else "0")
            birim = float(txt_birim_fiyat.value.replace(",", ".") if txt_birim_fiyat.value else "0")
            txt_toplam_tutar.value = f"{adet * birim:.2f}"
        except: txt_toplam_tutar.value = "0.00"
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
        except: return
        
        if toplam <= 0: return

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
            if duzenlenecek_eski_veri in tum_veriler:
                tum_veriler.remove(duzenlenecek_eski_veri)
            tum_veriler.append(yeni_veri)
            page.show_snack_bar(ft.SnackBar(ft.Text("Güncellendi! ✨"), bgcolor="orange"))
            btn_kaydet.text = "KAYDET"
            btn_kaydet.icon = "save"
            btn_kaydet.bgcolor = "#007acc"
            duzenlenecek_eski_veri = None
        else:
            tum_veriler.append(yeni_veri)
            page.show_snack_bar(ft.SnackBar(ft.Text("Kaydedildi!"), bgcolor="green"))

        harcamalari_yaz(tum_veriler)
        urun_adi.value = ""
        txt_adet.value = "1"
        txt_birim_fiyat.value = ""
        txt_toplam_tutar.value = "0.00"
        urun_adi.focus()
        dashboard_guncelle()

    def grafik_ac_kapa(e):
        kapsayici_grafik.visible = not kapsayici_grafik.visible
        btn_grafik_toggle.text = "Analizi Gizle" if kapsayici_grafik.visible else "Detaylı Analiz"
        btn_grafik_toggle.icon = "expand_less" if kapsayici_grafik.visible else "pie_chart"
        page.update()

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
                    if arama_metni in v["urun"].lower() or arama_metni in v["kategori"].lower():
                        filtrelenmis.append(v)
                else:
                    p = v["tarih"].split(".")
                    if len(p) == 3 and p[1] == secili_ay and p[2] == secili_yil:
                        filtrelenmis.append(v)
            except: pass
            
        filtrelenmis.sort(key=lambda x: datetime.strptime(x['tarih'], "%d.%m.%Y"), reverse=True)
        toplam = sum(x["tutar"] for x in filtrelenmis)
        
        # --- İSTATİSTİK GÜNCELLEME ---
        en_cok_kat_txt, en_pahali_txt = istatistik_hesapla(filtrelenmis)
        txt_stat_kat.value = en_cok_kat_txt
        txt_stat_pahali.value = en_pahali_txt

        if arama_modu:
            txt_toplam.value = f"{toplam:,.2f} TL"
            txt_butce.value = "Arama Sonuçları"
            txt_kalan.value = "..."
            container_stats.visible = False
        else:
            butce = butce_getir(secili_ay, secili_yil)
            kalan = butce - toplam
            txt_toplam.value = f"{toplam:,.2f} TL"
            txt_butce.value = f"Bütçe: {butce:,.0f} TL"
            txt_kalan.value = f"Kalan: {kalan:,.2f} TL"
            txt_kalan.color = "#2ecc71" if kalan >= 0 else "#e74c3c"
            container_stats.visible = True

        liste_kutusu.controls.clear()
        if not filtrelenmis:
            liste_kutusu.controls.append(ft.Text("Kayıt yok...", color="grey", italic=True))
            pasta_grafigi.sections = [] 
        else:
            for v in filtrelenmis:
                liste_kutusu.controls.append(kart_olustur(v))
            
            kat_toplamlari = {}
            for v in filtrelenmis:
                kat_toplamlari[v["kategori"]] = kat_toplamlari.get(v["kategori"], 0) + v["tutar"]
            
            sections = []
            renk_index = 0
            for kat, tut in kat_toplamlari.items():
                sections.append(
                    ft.PieChartSection(
                        value=tut,
                        title=f"{kat}\n%{int((tut/toplam)*100)}", 
                        title_style=ft.TextStyle(size=10, weight="bold", color="white"),
                        color=GRAFIK_RENKLERI[renk_index % len(GRAFIK_RENKLERI)],
                        radius=50
                    )
                )
                renk_index += 1
            pasta_grafigi.sections = sections

        page.update()

    def butce_kaydet_tikla(e):
        if txt_yeni_butce.value:
            butce_kaydet(dd_ay.value, dd_yil.value, float(txt_yeni_butce.value))
            dashboard_guncelle()
            row_butce_edit.visible = False
            page.update()

    def kart_olustur(veri):
        adet = veri.get("adet", 1)
        birim = veri.get("birim_fiyat", veri["tutar"])
        info = f"{veri['urun']} ({adet}x{birim})" if float(adet) > 1 else veri['urun']
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(name="receipt_long", color="grey"),
                    ft.Column([ft.Text(info, weight="bold"), ft.Text(f"{veri['kategori']} | {veri['tarih']}", size=12, color="grey")], spacing=2)
                ]),
                ft.Row([
                    ft.Text(f"-{veri['tutar']} TL", color="#e74c3c", weight="bold"),
                    ft.IconButton(icon="edit", icon_color="#007acc", icon_size=20, on_click=lambda e: duzenle_modunu_ac(veri)),
                    ft.IconButton(icon="delete_outline", icon_color="grey", icon_size=20, on_click=lambda e: harcama_sil(veri))
                ])
            ], alignment="spaceBetween"),
            bgcolor="#252526", padding=10, border_radius=10, margin=2
        )

    # --- ARAYÜZ ELEMANLARI ---
    simdi = datetime.now()
    dd_ay = ft.Dropdown(width=80, options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)], value=f"{simdi.month:02d}", on_change=dashboard_guncelle, content_padding=5, text_size=13)
    dd_yil = ft.Dropdown(width=90, options=[ft.dropdown.Option(str(y)) for y in range(2025, 2030)], value=str(simdi.year), on_change=dashboard_guncelle, content_padding=5, text_size=13)
    txt_toplam = ft.Text("0.00 TL", size=26, weight="bold", color="white")
    txt_kalan = ft.Text("...", size=16)
    txt_butce = ft.Text("...", size=14, color="grey")
    
    txt_yeni_butce = ft.TextField(hint_text="Bütçe", width=100, height=35, content_padding=5, keyboard_type="number", text_size=13)
    row_butce_edit = ft.Row([txt_yeni_butce, ft.IconButton(icon="check", on_click=butce_kaydet_tikla)], visible=False)

    # YENİ: İstatistik Kutuları
    txt_stat_kat = ft.Text("-", size=13, weight="bold", text_align="center")
    txt_stat_pahali = ft.Text("-", size=13, weight="bold", text_align="center")
    
    container_stats = ft.Row([
        ft.Container(content=ft.Column([ft.Text("En Çok Harcanan", size=10, color="grey"), txt_stat_kat], horizontal_alignment="center"), bgcolor="#2d2d2d", padding=10, border_radius=8, expand=True),
        ft.Container(content=ft.Column([ft.Text("En Pahalı Kalem", size=10, color="grey"), txt_stat_pahali], horizontal_alignment="center"), bgcolor="#2d2d2d", padding=10, border_radius=8, expand=True),
    ], spacing=10)

    pasta_grafigi = ft.PieChart(sections=[], sections_space=2, center_space_radius=30, height=150)
    kapsayici_grafik = ft.Container(content=ft.Column([ft.Divider(), ft.Text("Pasta Grafiği", size=12, color="grey"), pasta_grafigi], horizontal_alignment="center"), visible=False)
    btn_grafik_toggle = ft.TextButton("Detaylı Analiz", icon="pie_chart", on_click=grafik_ac_kapa)

    dashboard_kart = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("ÖZET TABLO", weight="bold", color="grey"), ft.Row([dd_ay, dd_yil])], alignment="spaceBetween"),
            ft.Divider(height=10, color="transparent"),
            ft.Column([ft.Text("Toplam Harcama", color="grey", size=12), txt_toplam], spacing=0),
            ft.Row([txt_butce, ft.TextButton("Düzenle", on_click=lambda e: setattr(row_butce_edit, 'visible', not row_butce_edit.visible) or page.update())], alignment="spaceBetween"),
            row_butce_edit,
            txt_kalan,
            ft.Divider(color="grey"),
            container_stats,
            ft.Divider(color="grey"),
            btn_grafik_toggle,
            kapsayici_grafik
        ]),
        bgcolor="#1e1e1e", padding=15, border_radius=15, border=ft.border.all(1, "#333333")
    )

    tarih_kutusu = ft.TextField(label="Tarih", value=simdi.strftime("%d.%m.%Y"), icon="calendar_today")
    baslangic_kat = kategorileri_oku()
    kategori = ft.Dropdown(options=[ft.dropdown.Option(x) for x in baslangic_kat], value=baslangic_kat[0] if baslangic_kat else None, label="Kategori", expand=True)
    
    txt_yeni_kat = ft.TextField(hint_text="Kategori Adı", expand=True, height=40, content_padding=10)
    col_ozel_kategoriler = ft.Column()
    container_kat_yonet = ft.Container(content=ft.Column([ft.Row([txt_yeni_kat, ft.IconButton(icon="add", on_click=kategori_ekle)]), col_ozel_kategoriler]), visible=False, bgcolor="#252526", padding=10, border_radius=10)

    urun_adi = ft.TextField(label="Ürün / Açıklama")
    txt_adet = ft.TextField(label="Adet", value="1", expand=1, keyboard_type="number", on_change=tutar_hesapla)
    txt_birim_fiyat = ft.TextField(label="Fiyat", expand=2, keyboard_type="number", on_change=tutar_hesapla)
    txt_toplam_tutar = ft.TextField(label="Toplam", value="0.00", read_only=True, text_style=ft.TextStyle(weight="bold", color="#2ecc71"))
    btn_kaydet = ft.ElevatedButton("KAYDET", icon="save", bgcolor="#007acc", color="white", height=50, width=400, on_click=kaydet_tikla)

    txt_arama = ft.TextField(hint_text="Harcama Ara...", prefix_icon="search", border_radius=15, height=40, content_padding=10, on_change=dashboard_guncelle)
    liste_kutusu = ft.Column()

    page.add(ft.Column([
        dashboard_kart,
        ft.Container(height=10),
        ft.Text("Harcama Ekle", weight="bold", size=16),
        tarih_kutusu,
        ft.Row([kategori, ft.IconButton(icon="settings", on_click=kategori_yonet_ac)]),
        container_kat_yonet,
        urun_adi,
        ft.Row([txt_adet, ft.Container(width=10), txt_birim_fiyat]),
        txt_toplam_tutar,
        ft.Container(height=5),
        btn_kaydet,
        ft.Divider(),
        txt_arama,
        liste_kutusu
    ]))

    dashboard_guncelle()

ft.app(target=main)

