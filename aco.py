"""
Karınca Kolonisi Optimizasyonu (Ant System) - Gezgin Satıcı Problemi (TSP) için genel sürüm

Her karınca bir şehirden başlar, gitmediği şehirlerden birini olasılıkla seçerek turu kurar:

    p(i,j) ~ tau(i,j)^alpha * eta(i,j)^beta        eta(i,j) = 1 / d(i,j)

Tüm karıncalar turunu bitirince feromon güncellenir:

    tau(i,j) = (1 - rho) * tau(i,j) + toplam_k Q / L_k    (k. karıncanın turu (i,j) kenarını kullandıysa)

Kısa turlar kenarlara daha çok feromon bırakır, sonraki karıncalar bu kenarlara daha çok
yönelir. Buharlaşma (rho) eski ve kötü izlerin zamanla silinmesini sağlar.

İki varyant var (variant parametresi):
    "as"  : Ant System. Her karınca kendi turunun kenarlarına feromon bırakır.
    "mmas": MAX-MIN Ant System. Yalnızca iterasyonun en iyi karıncası feromon bırakır ve
            feromon [tau_alt, tau_ust] aralığına kırpılır (tau_ust = Q / (rho * L_en_iyi),
            tau_alt = tau_ust / (2n)). Feromonun tek bir tura yığılıp diğer kenarları
            tamamen silmesini engeller.

Karşılaştırma için üç yardımcı yöntem de var: rastgele tur, en yakın komşu ve 2-opt.
"""

import numpy as np


def mesafe_matrisi(koordinat):
    """(n, 2) koordinatlardan Öklid mesafe matrisi."""
    k = np.asarray(koordinat, dtype=float)
    fark = k[:, None, :] - k[None, :, :]
    return np.sqrt((fark**2).sum(axis=-1))


def tur_uzunlugu(tur, mesafe):
    """Turun toplam uzunluğu (son şehirden başlangıca dönüş dahil)."""
    tur = np.asarray(tur)
    return float(mesafe[tur, np.roll(tur, -1)].sum())


def rastgele_tur(n, rng):
    return [int(c) for c in rng.permutation(n)]


def en_yakin_komsu(mesafe, baslangic=0):
    """Her adımda en yakın gidilmemiş şehre git (açgözlü)."""
    n = len(mesafe)
    tur = [baslangic]
    kalan = set(range(n)) - {baslangic}
    while kalan:
        i = tur[-1]
        j = min(kalan, key=lambda c: mesafe[i, c])
        tur.append(j)
        kalan.remove(j)
    return tur


def iki_opt(tur, mesafe):
    """2-opt yerel arama: iki kenarı çıkarıp yeniden bağlamak turu kısaltıyorsa yap."""
    tur = list(tur)
    n = len(tur)
    iyilesti = True
    while iyilesti:
        iyilesti = False
        for a in range(n - 1):
            for b in range(a + 2, n):
                if a == 0 and b == n - 1:
                    continue  # bu iki kenar komşu, değiştirmenin anlamı yok
                i, j = tur[a], tur[a + 1]
                k, l = tur[b], tur[(b + 1) % n]
                if mesafe[i, k] + mesafe[j, l] < mesafe[i, j] + mesafe[k, l] - 1e-12:
                    tur[a + 1 : b + 1] = tur[a + 1 : b + 1][::-1]
                    iyilesti = True
    return tur


class ACO:
    def __init__(
        self,
        mesafe,
        n_ants=None,      # karınca sayısı (None -> şehir sayısı kadar)
        n_iter=200,       # iterasyon sayısı
        alpha=1.0,        # feromon ağırlığı (0 -> feromon hiç kullanılmaz)
        beta=3.0,         # görünürlük (1/mesafe) ağırlığı
        rho=0.5,          # buharlaşma oranı
        Q=1.0,            # feromon miktarı (kenara Q / tur uzunluğu kadar bırakılır)
        tau_min=1e-10,    # sayısal güvenlik: feromon bunun altına inmez ("as" varyantında)
        patience=None,    # kaç iterasyon iyileşme olmazsa dur (None -> hiç durma)
        variant="as",     # "as": Ant System, "mmas": MAX-MIN Ant System
        seed=None,
    ):
        if variant not in ("as", "mmas"):
            raise ValueError("variant 'as' veya 'mmas' olmalı")
        self.variant = variant
        self.mesafe = np.asarray(mesafe, dtype=float)
        self.n = len(self.mesafe)
        self.n_ants = n_ants or self.n
        self.n_iter = n_iter
        self.alpha, self.beta, self.rho, self.Q = alpha, beta, rho, Q
        self.tau_min = tau_min
        self.patience = patience
        self.rng = np.random.default_rng(seed)

        self.eta = np.zeros_like(self.mesafe)
        maske = self.mesafe > 0
        self.eta[maske] = 1.0 / self.mesafe[maske]
        self.tau = None  # optimize() sonunda son feromon matrisi burada durur

    def _tur_kur(self, tau, baslangic):
        """Bir karıncanın turunu rulet seçimiyle kurar."""
        n = self.n
        gidildi = np.zeros(n, dtype=bool)
        gidildi[baslangic] = True
        tur = [baslangic]
        for _ in range(n - 1):
            i = tur[-1]
            w = (tau[i] ** self.alpha) * (self.eta[i] ** self.beta)
            w[gidildi] = 0.0  # gidilmiş şehirlerin seçilme şansı yok
            kum = np.cumsum(w)
            if kum[-1] <= 0:  # sayısal güvenlik: tüm ağırlıklar 0 ise eşit olasılıkla seç
                j = int(self.rng.choice(np.flatnonzero(~gidildi)))
            else:
                r = self.rng.random() * kum[-1]
                j = int(np.searchsorted(kum, r, side="right"))
                if j >= n or gidildi[j]:  # yuvarlama hatasına karşı
                    j = int(np.flatnonzero(~gidildi)[-1])
            tur.append(j)
            gidildi[j] = True
        return tur

    def optimize(self):
        """En kısa turu arar. (en_iyi_tur, en_iyi_uzunluk, gecmis) döndürür.

        gecmis: her iterasyon sonunda "şimdiye kadarki en iyi" tur uzunluğu.
        """
        mesafe, n = self.mesafe, self.n

        mmas = self.variant == "mmas"

        # Başlangıç feromonu. Ant System: m / L_nn (Dorigo ve Stützle'nin önerisi), L_nn en yakın
        # komşu turunun uzunluğu. MMAS: üst sınırın tahmini Q / (rho * L_nn).
        L_nn = tur_uzunlugu(en_yakin_komsu(mesafe), mesafe)
        if mmas:
            tau_ust = self.Q / (self.rho * L_nn)
            tau_alt = tau_ust / (2 * n)
            tau = np.full((n, n), tau_ust)
        else:
            tau = np.full((n, n), self.n_ants / L_nn)
        np.fill_diagonal(tau, 0.0)

        en_iyi_tur, en_iyi_L = None, np.inf
        gecmis = []
        durgun = 0

        for _ in range(self.n_iter):
            turlar, uzunluklar = [], []
            for _k in range(self.n_ants):
                tur = self._tur_kur(tau, int(self.rng.integers(n)))
                turlar.append(tur)
                uzunluklar.append(tur_uzunlugu(tur, mesafe))

            en_iyi_k = int(np.argmin(uzunluklar))
            if uzunluklar[en_iyi_k] < en_iyi_L - 1e-12:
                en_iyi_L = uzunluklar[en_iyi_k]
                en_iyi_tur = list(turlar[en_iyi_k])
                durgun = 0
            else:
                durgun += 1
            gecmis.append(en_iyi_L)

            # Buharlaşma, sonra feromon ekleme
            tau *= 1.0 - self.rho
            if mmas:
                # MMAS: yalnızca bu iterasyonun en iyi karıncası feromon bırakır
                yatirimcilar = [(turlar[en_iyi_k], uzunluklar[en_iyi_k])]
            else:
                # Ant System: her karınca kendi turunun kenarlarına bırakır
                yatirimcilar = list(zip(turlar, uzunluklar))
            for tur, L in yatirimcilar:
                a = np.array(tur)
                b = np.roll(a, -1)
                np.add.at(tau, (a, b), self.Q / L)
                np.add.at(tau, (b, a), self.Q / L)  # simetrik problem

            if mmas:
                # Sınırlar şimdiye kadarki en iyi tura göre güncellenir; feromon bu aralığa kırpılır.
                # Böylece hiçbir kenarın seçilme şansı tamamen sıfıra inmez.
                tau_ust = self.Q / (self.rho * en_iyi_L)
                tau_alt = tau_ust / (2 * n)
                np.clip(tau, tau_alt, tau_ust, out=tau)
            else:
                np.maximum(tau, self.tau_min, out=tau)
            np.fill_diagonal(tau, 0.0)

            if self.patience is not None and durgun >= self.patience:
                break

        self.tau = tau
        return en_iyi_tur, en_iyi_L, gecmis


def test_sehirleri(n=20, seed=42):
    """[0, 100] x [0, 100] karesinde n rastgele şehir."""
    return np.random.default_rng(seed).uniform(0, 100, size=(n, 2))


if __name__ == "__main__":
    koord = test_sehirleri(20, seed=42)
    mesafe = mesafe_matrisi(koord)
    n = len(koord)
    rng = np.random.default_rng(0)

    print(f"{n} rastgele şehir, [0, 100] karesinde (seed = 42)\n")

    # --- Karşılaştırma yöntemleri ---
    rastgele = [tur_uzunlugu(rastgele_tur(n, rng), mesafe) for _ in range(1000)]
    nn = [tur_uzunlugu(en_yakin_komsu(mesafe, s), mesafe) for s in range(n)]
    # 2-opt: 200 rastgele başlangıç turundan yerel arama, en iyisi
    iki = min(tur_uzunlugu(iki_opt(rastgele_tur(n, rng), mesafe), mesafe) for _ in range(200))

    print("Referans yöntemler:")
    print(f"  rastgele tur (1000 deneme)      ortalama {np.mean(rastgele):7.2f}")
    print(f"  en yakın komşu (20 başlangıç)   en iyi   {min(nn):7.2f}   ortalama {np.mean(nn):7.2f}")
    print(f"  2-opt (200 rastgele başlangıç)  en iyi   {iki:7.2f}")

    # --- ACO: 10 farklı tohum ---
    print("\nACO (20 karınca, 200 iterasyon, 10 farklı tohum):")
    ayarlar = {
        "ACO (alpha=1, beta=3)": dict(alpha=1.0, beta=3.0),
        "feromonsuz (alpha=0, beta=3)": dict(alpha=0.0, beta=3.0),
    }
    for ad, kw in ayarlar.items():
        sonuc = [ACO(mesafe, n_iter=200, seed=s, **kw).optimize()[1] for s in range(10)]
        print(
            f"  {ad:30s} ortalama {np.mean(sonuc):7.2f}   en iyi {min(sonuc):7.2f}   en kötü {max(sonuc):7.2f}"
        )

    tur, L, _ = ACO(mesafe, n_iter=200, seed=0).optimize()
    print(f"\ntohum 0 en iyi tur (şehirler 1 tabanlı): {' -> '.join(str(c + 1) for c in tur + [tur[0]])}")
    print(f"uzunluk = {L:.2f}")
