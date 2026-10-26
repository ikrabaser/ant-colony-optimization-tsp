"""
Karınca Kolonisi Optimizasyonu (ACO / Ant System) ile 5 şehirli TSP - el hesabının kodu

Problem
-------
5 şehir var. Her şehre tam bir kez uğrayıp başlangıç şehrine dönen EN KISA turu bul
(Gezgin Satıcı Problemi, TSP). Şehirler arası mesafeler simetrik (d[i][j] = d[j][i]).

El hesabındaki ayarlar
----------------------
- 3 karınca; başlangıç şehirleri: 1, 3, 5
- alpha = 1 (feromon ağırlığı), beta = 2 (görünürlük ağırlığı)
- rho = 0.5 (buharlaşma), Q = 10 (feromon miktarı), tau0 = 1 (başlangıç feromonu)
- görünürlük: eta(i,j) = 1 / d(i,j)
- Rulet seçimi için rassal sayılar elle verilir (aşağıdaki RASSAL), böylece
  hesap her çalıştırmada aynı çıkar ve elle takip edilebilir.

Formüller
---------
Seçim olasılığı (karınca k, şehir i'deyken, j gidilmemiş şehir):
    p(i,j) = [tau(i,j)^alpha * eta(i,j)^beta] / toplam_{l gidilmemiş} [tau(i,l)^alpha * eta(i,l)^beta]

Rulet: olasılıklar sırayla toplanır (kümülatif); kümülatif değeri ilk kez r'ye eşit
veya r'den büyük olan aday seçilir.

Feromon güncelleme (iterasyon sonunda, tüm karıncalar turunu bitirdikten sonra):
    tau(i,j) = (1 - rho) * tau(i,j) + toplam_k delta_k(i,j)
    delta_k(i,j) = Q / L_k   (k. karıncanın turu (i,j) kenarını kullandıysa), değilse 0

Not: Ekrana yazılan sayılar 4 ondalığa YUVARLANARAK gösterilir, hesap ise tam
hassasiyetle yapılır. Elle hesapta ara sonuçları yuvarlarsan son hanelerde küçük
farklar çıkabilir.
"""

import itertools

import numpy as np

# Şehirler arası mesafe matrisi (satır/sütun sırası: şehir 1..5)
D = np.array(
    [
        [0, 3, 8, 9, 5],
        [3, 0, 4, 7, 6],
        [8, 4, 0, 3, 7],
        [9, 7, 3, 0, 4],
        [5, 6, 7, 4, 0],
    ],
    dtype=float,
)

BASLANGIC = [0, 2, 4]  # karıncaların başlangıç şehirleri (0 tabanlı: şehir 1, 3, 5)

# RASSAL[iterasyon][karınca] = o karıncanın rulet için kullandığı rassal sayılar.
# Her karınca 3 seçim yapar (4 aday, 3 aday, 2 aday). Son şehirde tek aday kalır,
# o adım zorunludur ve rassal sayı gerektirmez.
RASSAL = [
    [[0.40, 0.75, 0.30], [0.85, 0.20, 0.60], [0.55, 0.90, 0.10]],  # 1. iterasyon
    [[0.15, 0.50, 0.80], [0.70, 0.35, 0.95], [0.25, 0.65, 0.45]],  # 2. iterasyon
]


def tur_uzunlugu(tur, mesafe):
    """Turun toplam uzunluğu (son şehirden başlangıca dönüş dahil)."""
    n = len(tur)
    return float(sum(mesafe[tur[a], tur[(a + 1) % n]] for a in range(n)))


def en_iyi_tur_brute_force(mesafe):
    """Tüm turları deneyerek gerçek optimumu bulur (yalnızca küçük n için)."""
    n = len(mesafe)
    en_iyi_tur, en_iyi_L = None, np.inf
    for sira in itertools.permutations(range(1, n)):
        tur = (0,) + sira
        L = tur_uzunlugu(tur, mesafe)
        if L < en_iyi_L:
            en_iyi_tur, en_iyi_L = list(tur), L
    return en_iyi_tur, en_iyi_L


def ant_system(
    mesafe,
    baslangic,
    rassal=(),
    alpha=1.0,
    beta=2.0,
    rho=0.5,
    Q=10.0,
    tau0=1.0,
    n_iter=2,
    seed=0,
    kayit=False,
    variant="as",
):
    """Ant System ile TSP çözer.

    baslangic : her karıncanın başlangıç şehri (0 tabanlı); karınca sayısı = len(baslangic)
    rassal    : rassal[t][k] = t. iterasyonda k. karıncanın rulet sayıları. Verilmeyen
                iterasyonlarda rassal sayılar `seed` ile rastgele üretilir.
    kayit     : True ise her adımın ara değerleri `log` içinde döndürülür.
    variant   : "as" -> yukarıdaki Ant System (el hesabı bu). "mmas" -> MAX-MIN Ant System:
                yalnızca iterasyonun en iyi karıncası feromon bırakır ve feromon
                [tau_alt, tau_ust] aralığına kırpılır (tau_ust = Q / (rho * L_en_iyi),
                tau_alt = tau_ust / (2n)). Yalnızca karşılaştırma içindir, el hesabında kullanılmaz.
    """
    rng = np.random.default_rng(seed)
    n = len(mesafe)

    # Görünürlük: eta = 1 / d (köşegen 0 kalır, zaten hiç kullanılmaz)
    eta = np.zeros_like(mesafe)
    maske = mesafe > 0
    eta[maske] = 1.0 / mesafe[maske]

    tau = np.full((n, n), float(tau0))
    np.fill_diagonal(tau, 0.0)

    en_iyi_tur, en_iyi_L = None, np.inf
    gecmis = []  # her iterasyon sonunda "şimdiye kadarki en iyi" tur uzunluğu
    log = []

    for t in range(n_iter):
        tau_basi = tau.copy()
        karinca_log, turlar, uzunluklar = [], [], []

        for k, s in enumerate(baslangic):
            tur = [s]
            gidilmemis = [c for c in range(n) if c != s]
            adimlar = []
            secim_no = 0

            while gidilmemis:
                i = tur[-1]
                tau_i = tau[i, gidilmemis]
                eta_i = eta[i, gidilmemis]
                agirlik = tau_i**alpha * eta_i**beta
                p = agirlik / agirlik.sum()
                kum = np.cumsum(p)

                if len(gidilmemis) == 1:
                    r = None  # tek aday kaldı: zorunlu adım
                    sec = 0
                else:
                    if t < len(rassal):
                        r = float(rassal[t][k][secim_no])
                    else:
                        r = float(rng.random())
                    secim_no += 1
                    # kümülatif değeri ilk kez r'ye eşit/büyük olan aday
                    sec = min(int(np.searchsorted(kum, r)), len(gidilmemis) - 1)

                j = gidilmemis[sec]
                if kayit:
                    adimlar.append(
                        {
                            "sehir": i,
                            "adaylar": list(gidilmemis),
                            "tau": tau_i.tolist(),
                            "eta": eta_i.tolist(),
                            "agirlik": agirlik.tolist(),
                            "p": p.tolist(),
                            "kum": kum.tolist(),
                            "r": r,
                            "secilen": j,
                        }
                    )
                tur.append(j)
                gidilmemis.remove(j)

            L = tur_uzunlugu(tur, mesafe)
            turlar.append(tur)
            uzunluklar.append(L)
            if kayit:
                karinca_log.append({"baslangic": s, "adimlar": adimlar, "tur": tur, "L": L})
            if L < en_iyi_L:
                en_iyi_tur, en_iyi_L = list(tur), L

        # --- Feromon güncelleme: önce buharlaşma, sonra her karıncanın bıraktığı feromon ---
        tau = (1.0 - rho) * tau
        tau_buharlasmis = tau.copy()
        delta = np.zeros((n, n))
        if variant == "mmas":
            k_en = int(np.argmin(uzunluklar))  # yalnızca bu iterasyonun en iyi karıncası
            yatirimcilar = [(turlar[k_en], uzunluklar[k_en])]
        else:
            yatirimcilar = list(zip(turlar, uzunluklar))
        for tur, L in yatirimcilar:
            for a in range(n):
                i, j = tur[a], tur[(a + 1) % n]
                delta[i, j] += Q / L
                delta[j, i] += Q / L  # simetrik problem: kenar iki yönde de pekişir
        tau = tau + delta
        if variant == "mmas":
            tau_ust = Q / (rho * en_iyi_L)
            tau = np.clip(tau, tau_ust / (2 * n), tau_ust)
            np.fill_diagonal(tau, 0.0)
        gecmis.append(en_iyi_L)

        if kayit:
            log.append(
                {
                    "tau_basi": tau_basi,
                    "karincalar": karinca_log,
                    "tau_buharlasmis": tau_buharlasmis,
                    "delta": delta,
                    "tau_sonu": tau.copy(),
                    "iter_en_iyi_L": min(uzunluklar),
                    "en_iyi_tur": list(en_iyi_tur),
                    "en_iyi_L": en_iyi_L,
                }
            )

    return en_iyi_tur, en_iyi_L, gecmis, tau, log


# ----------------------------------------------------------------------------
# Yazdırma yardımcıları (şehirler ekranda 1 tabanlı yazılır)
# ----------------------------------------------------------------------------
def tur_yazi(tur):
    """[0, 1, 2] -> '1 -> 2 -> 3 -> 1'"""
    return " -> ".join(str(c + 1) for c in list(tur) + [tur[0]])


def matris_yazdir(baslik, M):
    n = len(M)
    print(baslik)
    print("      " + " ".join(f"{j + 1:>8d}" for j in range(n)))
    for i in range(n):
        print(f"{i + 1:>4d}  " + " ".join(f"{M[i, j]:8.4f}" for j in range(n)))


def iterasyon_yazdir(t, kayit_t):
    print(f"--- {t}. iterasyon ---")
    matris_yazdir("Başlangıçtaki feromon matrisi tau:", kayit_t["tau_basi"])
    print()
    for k, ant in enumerate(kayit_t["karincalar"], start=1):
        print(f"Karınca {k} (başlangıç şehri {ant['baslangic'] + 1})")
        for no, a in enumerate(ant["adimlar"], start=1):
            adaylar = ", ".join(str(c + 1) for c in a["adaylar"])
            print(f"  Adım {no}: şehir {a['sehir'] + 1}'deyken, aday şehirler: {adaylar}")
            print("    aday |     tau |     eta | tau^a*eta^b |       p |   küm.")
            for q, c in enumerate(a["adaylar"]):
                print(
                    f"    {c + 1:>4d} | {a['tau'][q]:7.4f} | {a['eta'][q]:7.4f} | "
                    f"{a['agirlik'][q]:11.6f} | {a['p'][q]:7.4f} | {a['kum'][q]:6.4f}"
                )
            if a["r"] is None:
                print(f"    tek aday kaldı -> şehir {a['secilen'] + 1} (zorunlu adım)")
            else:
                print(f"    r = {a['r']:.2f} -> seçilen şehir {a['secilen'] + 1}")
        print(f"  Tur: {tur_yazi(ant['tur'])}   uzunluk L = {ant['L']:.0f}\n")

    matris_yazdir("Buharlaşma sonrası (1 - rho) * tau:", kayit_t["tau_buharlasmis"])
    print()
    matris_yazdir("Karıncaların bıraktığı toplam feromon (delta):", kayit_t["delta"])
    print()
    matris_yazdir("Yeni feromon matrisi tau = buharlaşmış + delta:", kayit_t["tau_sonu"])
    print(
        f"\nBu iterasyonun en iyisi: L = {kayit_t['iter_en_iyi_L']:.0f}   |   "
        f"şimdiye kadarki en iyi: {tur_yazi(kayit_t['en_iyi_tur'])}  (L = {kayit_t['en_iyi_L']:.0f})\n"
    )


if __name__ == "__main__":
    opt_tur, opt_L = en_iyi_tur_brute_force(D)

    print("=" * 66)
    print("A) EL HESABININ TEKRARI  (3 karınca, 2 iterasyon, alpha=1, beta=2, rho=0.5, Q=10)")
    print("=" * 66)
    matris_yazdir("Mesafe matrisi d:", D)
    print()
    eta0 = np.zeros_like(D)
    eta0[D > 0] = 1.0 / D[D > 0]
    matris_yazdir("Görünürlük eta = 1/d:", eta0)
    print("\nBaşlangıç feromonu: tau0 = 1 (tüm kenarlarda)\n")

    _, _, _, _, log = ant_system(D, BASLANGIC, RASSAL, n_iter=2, kayit=True)
    for t, kayit_t in enumerate(log, start=1):
        iterasyon_yazdir(t, kayit_t)

    print("=" * 66)
    print("B) Daha uzun çalıştırma: aynı kurulum, 100 iterasyon (3. iterasyondan sonra r rastgele)")
    print("=" * 66)
    print(f"Gerçek optimum (tüm turlar denendi): {tur_yazi(opt_tur)}  L = {opt_L:.0f}")
    bulan = 0
    for tohum in range(10):
        tur, L, gecmis, _, _ = ant_system(D, BASLANGIC, RASSAL, n_iter=100, seed=tohum)
        ilk = next(i + 1 for i, g in enumerate(gecmis) if g == L)
        bulan += L == opt_L
        print(f"tohum {tohum}: en iyi L = {L:.0f}, tur {tur_yazi(tur)}  ({ilk}. iterasyonda bulundu)")
    print(f"Optimuma ulaşan: {bulan}/10 tohum")
