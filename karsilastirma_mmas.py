"""Ant System ile MAX-MIN Ant System (MMAS) karşılaştırması.

A) 5 şehirli el hesabı kurulumunda (sabit başlangıç şehirleri, ilk iki iterasyonun rassal
   sayıları aynı) 200 tohumla: kaçı 100 iterasyonda optimuma (L = 19) ulaşıyor?
B) 20 şehirli rastgele problemde (aco.py'deki ile aynı) 10 tohumla.

    python karsilastirma_mmas.py        (yaklaşık 1-2 dk sürer)
"""

import numpy as np

from aco import ACO, mesafe_matrisi, test_sehirleri
from aco_el_hesabi import BASLANGIC, D, RASSAL, ant_system, en_iyi_tur_brute_force

if __name__ == "__main__":
    # ---------------------------------------------------------------- A) 5 şehir
    _, opt_L = en_iyi_tur_brute_force(D)
    TOHUM = 200
    print(f"A) 5 şehir, el hesabı kurulumu, 100 iterasyon, {TOHUM} tohum (optimum L = {opt_L:.0f})")
    print("| Yöntem | rho | Optimuma ulaşan tohum |")
    print("|---|---|---|")
    for ad, v in (("Ant System", "as"), ("MMAS", "mmas")):
        for rho in (0.5, 0.1):
            ok = sum(
                ant_system(D, BASLANGIC, RASSAL, rho=rho, n_iter=100, seed=s, variant=v)[1] == opt_L
                for s in range(TOHUM)
            )
            print(f"| {ad} | {rho} | {ok}/{TOHUM} (%{100 * ok / TOHUM:.1f}) |")

    # --------------------------------------------------------------- B) 20 şehir
    mesafe = mesafe_matrisi(test_sehirleri(20, seed=42))
    print("\nB) 20 şehir, 20 karınca, 200 iterasyon, 10 tohum (0-9)")
    print("| Yöntem | rho | Ortalama | En iyi | En kötü | Son değere indiği iterasyon (medyan / en yüksek) |")
    print("|---|---|---|---|---|---|")
    for ad, v, rho in (("Ant System", "as", 0.5), ("MMAS", "mmas", 0.5), ("MMAS", "mmas", 0.1)):
        sonuc, ne_zaman = [], []
        for s in range(10):
            _, L, gecmis = ACO(mesafe, n_iter=200, rho=rho, variant=v, seed=s).optimize()
            sonuc.append(L)
            ne_zaman.append(int(np.argmax(np.array(gecmis) <= L + 1e-9)) + 1)
        print(
            f"| {ad} | {rho} | {np.mean(sonuc):.2f} | {min(sonuc):.2f} | {max(sonuc):.2f} | "
            f"{np.median(ne_zaman):.0f} / {max(ne_zaman)} |"
        )
