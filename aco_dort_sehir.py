"""
Karınca Kolonisi Optimizasyonu (Ant System) - 4 şehirli örnek

4 şehirli örneğin kodudur: A, B, C, D şehirleri, başlangıç feromonu 1,
alpha = beta = 1, rho = 0.5. Her adımı (olasılık, kümülatif aralık, rassal sayı,
seçilen şehir, tur uzunluğu, feromon güncellemesi) ekrana yazar; böylece çıktı
el hesabıyla yan yana karşılaştırılabilir.

Kullanım:
    python aco_dort_sehir.py                      # el hesabı (r1=0.47, r2=0.82)
    python aco_dort_sehir.py --r 0.30 0.90        # kendi rassal sayılarınla
    python aco_dort_sehir.py --tam                # iterasyon 1 sonrası yuvarlama yapma
    python aco_dort_sehir.py --mod calistir       # gerçek ACO (rastgele sayılarla)
    python aco_dort_sehir.py --mod calistir --karinca 5 --iterasyon 30 --tohum 1

Formüller:
    eta_ij        = 1 / d_ij
    p_ij          = (tau_ij^alpha * eta_ij^beta) / SUM_l (tau_il^alpha * eta_il^beta)
    delta_tau_ij  = 1 / L_k        (k. karınca i-j yolunu kullandıysa, yoksa 0)
    tau_ij(yeni)  = (1 - rho) * tau_ij + SUM_k delta_tau_ij^k
"""

import argparse
import itertools
import random
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEHIRLER = ["A", "B", "C", "D"]
MESAFE = {
    ("A", "B"): 1,
    ("A", "C"): 4,
    ("A", "D"): 15,
    ("B", "C"): 8,
    ("B", "D"): 4,
    ("C", "D"): 5,
}

ALPHA = 1
BETA = 1
RHO = 0.5


# --------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# --------------------------------------------------------------------------
def kenar(a, b):
    """Yön fark etmez: A-B ile B-A aynı yoldur."""
    return tuple(sorted((a, b)))


def yol_adi(k):
    return f"{k[0]}-{k[1]}"


def tur_kenarlari(tur):
    """Turdaki yollar (son şehirden başlangıca dönüş dahil)."""
    return [kenar(tur[i], tur[(i + 1) % len(tur)]) for i in range(len(tur))]


def tur_uzunlugu(tur):
    return sum(MESAFE[k] for k in tur_kenarlari(tur))


def tur_yaz(tur):
    return " → ".join(tur + [tur[0]])


# --------------------------------------------------------------------------
# Geçiş olasılığı ve rulet çarkı
# --------------------------------------------------------------------------
def gecis_olasiliklari(simdiki, adaylar, tau, alpha, beta):
    """Her aday için puan = tau^alpha * eta^beta, payda = puanların toplamı."""
    puan = {}
    for j in adaylar:
        k = kenar(simdiki, j)
        eta = 1 / MESAFE[k]
        puan[j] = (tau[k] ** alpha) * (eta ** beta)
    payda = sum(puan.values())
    olasilik = {j: p / payda for j, p in puan.items()}
    return puan, olasilik, payda


def kumulatif_araliklar(olasilik):
    """Olasılığı küçükten büyüğe sıralayıp aralıkları arka arkaya dizer."""
    sirali = sorted(olasilik.items(), key=lambda x: (x[1], x[0]))
    araliklar = []
    baslangic = 0.0
    for sehir, p in sirali:
        bitis = baslangic + p
        araliklar.append((sehir, baslangic, bitis))
        baslangic = bitis
    return araliklar


def rulet(araliklar, r):
    """r hangi aralığa düşüyorsa o şehri seçer."""
    for sehir, _, bitis in araliklar:
        if r < bitis:
            return sehir
    return araliklar[-1][0]  # yuvarlama payı: r ~ 1.0 ise son şehir


# --------------------------------------------------------------------------
# Tur oluşturma
# --------------------------------------------------------------------------
def tur_olustur(baslangic, tau, alpha, beta, rassal_sayilar=None, yazdir=True):
    tur = [baslangic]
    rassal = list(rassal_sayilar) if rassal_sayilar else []

    while len(tur) < len(SEHIRLER):
        simdiki = tur[-1]
        adaylar = [s for s in SEHIRLER if s not in tur]
        puan, olasilik, payda = gecis_olasiliklari(simdiki, adaylar, tau, alpha, beta)
        araliklar = kumulatif_araliklar(olasilik)

        if len(adaylar) == 1:
            secilen, r = adaylar[0], None
        else:
            r = rassal.pop(0) if rassal else random.random()
            secilen = rulet(araliklar, r)

        if yazdir:
            print(f"\nAdım {len(tur)}: karınca {simdiki} şehrinde, aday şehirler: {', '.join(adaylar)}")
            print("  Yol    tau      eta=1/d  tau^a*eta^b  Olasılık")
            for j in adaylar:
                k = kenar(simdiki, j)
                print(f"  {yol_adi(k)}    {tau[k]:.4f}   {1 / MESAFE[k]:.4f}   "
                      f"{puan[j]:.5f}      {olasilik[j]:.4f}")
            print(f"  Payda = {payda:.5f}")
            if r is None:
                print(f"  Tek aday kaldı → olasılık 1, rulet atılmaz → {secilen}")
            else:
                print("  Kümülatif aralıklar (olasılık küçükten büyüğe):")
                for sehir, bas, bit in araliklar:
                    print(f"    {simdiki}→{sehir}: {bas:.4f} - {bit:.4f}")
                print(f"  Rassal sayı r = {r} → karınca {secilen} şehrine gider")

        tur.append(secilen)
    return tur


# --------------------------------------------------------------------------
# Feromon güncelleme
# --------------------------------------------------------------------------
def feromon_guncelle(tau, turlar, rho, yuvarla=None, yazdir=True):
    """tau(yeni) = (1 - rho) * tau + toplam delta_tau.  Tüm yollar buharlaşır."""
    delta = {k: 0.0 for k in tau}
    for tur in turlar:
        L = tur_uzunlugu(tur)
        for k in tur_kenarlari(tur):
            delta[k] += 1 / L

    yeni = {}
    if yazdir:
        print("\n  Yol    eski tau   buharlaşma   delta_tau   yeni tau")
    for k in sorted(tau):
        buhar = (1 - rho) * tau[k]
        deger = buhar + delta[k]
        if yuvarla is not None:
            deger = round(deger, yuvarla)
        yeni[k] = deger
        if yazdir:
            print(f"  {yol_adi(k)}    {tau[k]:.4f}     {buhar:.4f}       "
                  f"{delta[k]:.4f}      {deger:.4f}")
    return yeni


# --------------------------------------------------------------------------
# Mod 1: el hesabı
# --------------------------------------------------------------------------
def ornek(r_listesi, rho, alpha, beta, yuvarla):
    tau = {k: 1.0 for k in MESAFE}

    print("=" * 64)
    print("KARINCA KOLONİSİ - 4 ŞEHİRLİ EL HESABI")
    print("=" * 64)
    print(f"alpha = {alpha}, beta = {beta}, rho = {rho}, başlangıç tau = 1")
    print("Mesafeler: " + ", ".join(f"{yol_adi(k)}={d}" for k, d in sorted(MESAFE.items())))

    print("\n" + "-" * 64)
    print("İTERASYON 1: iki karıncanın turu (verilen)")
    print("-" * 64)
    turlar1 = [["A", "B", "D", "C"], ["A", "D", "B", "C"]]
    for i, t in enumerate(turlar1, 1):
        L = tur_uzunlugu(t)
        print(f"{i}. karınca: {tur_yaz(t)}   L = {L}   → kullandığı yollara 1/{L} = {1 / L:.4f}")
    tau = feromon_guncelle(tau, turlar1, rho, yuvarla)
    if yuvarla is not None:
        print(f"\n  (tau değerleri {yuvarla} basamağa yuvarlandı)")

    print("\n" + "-" * 64)
    print("İTERASYON 2: karınca A'dan çıkar")
    print("-" * 64)
    tur = tur_olustur("A", tau, alpha, beta, r_listesi)
    L = tur_uzunlugu(tur)
    print(f"\nTur: {tur_yaz(tur)}   L = {L}")
    print(f"Bu karıncanın bıraktığı: 1/{L} = {1 / L:.4f} (kullandığı yollara)")
    tau = feromon_guncelle(tau, [tur], rho)
    return tau


# --------------------------------------------------------------------------
# Mod 2: gerçek ACO (rastgele sayılarla)
# --------------------------------------------------------------------------
def kaba_kuvvet():
    """4 şehir için tüm turları dener, gerçek optimumu bulur."""
    en_iyi = None
    for perm in itertools.permutations(SEHIRLER[1:]):
        tur = [SEHIRLER[0], *perm]
        L = tur_uzunlugu(tur)
        if en_iyi is None or L < en_iyi[0]:
            en_iyi = (L, tur)
    return en_iyi


def calistir(karinca, iterasyon, rho, alpha, beta, tohum):
    random.seed(tohum)
    tau = {k: 1.0 for k in MESAFE}
    en_iyi_L, en_iyi_tur = None, None

    print(f"Gerçek ACO: {karinca} karınca, {iterasyon} iterasyon, "
          f"alpha={alpha}, beta={beta}, rho={rho}, tohum={tohum}")
    for it in range(1, iterasyon + 1):
        turlar = [tur_olustur(random.choice(SEHIRLER), tau, alpha, beta, yazdir=False)
                  for _ in range(karinca)]
        it_en_iyi = min(tur_uzunlugu(t) for t in turlar)
        for t in turlar:
            L = tur_uzunlugu(t)
            if en_iyi_L is None or L < en_iyi_L:
                en_iyi_L, en_iyi_tur = L, t
        tau = feromon_guncelle(tau, turlar, rho, yazdir=False)
        print(f"  iterasyon {it:3d}: bu iterasyonun en iyisi L = {it_en_iyi:2d}, "
              f"şimdiye kadarki en iyi L = {en_iyi_L}")

    print(f"\nBulunan en iyi tur: {tur_yaz(en_iyi_tur)}   L = {en_iyi_L}")
    opt_L, opt_tur = kaba_kuvvet()
    print(f"Kaba kuvvetle gerçek optimum: {tur_yaz(opt_tur)}   L = {opt_L}")
    print("Sonuç: " + ("optimumu buldu." if en_iyi_L == opt_L else "optimumu bulamadı."))


# --------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="4 şehirli ACO (Ant System) örneği")
    p.add_argument("--mod", choices=["ornek", "calistir"], default="ornek")
    p.add_argument("--r", type=float, nargs="+", default=[0.47, 0.82],
                   help="örnek modunda kullanılacak rassal sayılar (varsayılan: 0.47 0.82)")
    p.add_argument("--rho", type=float, default=RHO)
    p.add_argument("--alpha", type=float, default=ALPHA)
    p.add_argument("--beta", type=float, default=BETA)
    p.add_argument("--tam", action="store_true",
                   help="iterasyon 1 sonrası tau değerlerini yuvarlama")
    p.add_argument("--karinca", type=int, default=5)
    p.add_argument("--iterasyon", type=int, default=30)
    p.add_argument("--tohum", type=int, default=1)
    a = p.parse_args()

    if a.mod == "ornek":
        ornek(a.r, a.rho, a.alpha, a.beta, None if a.tam else 2)
    else:
        calistir(a.karinca, a.iterasyon, a.rho, a.alpha, a.beta, a.tohum)


if __name__ == "__main__":
    main()
