"""README'deki görselleri üretir (gorseller/ klasörüne PNG yazar).

    python gorseller_uret.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from aco import ACO, en_yakin_komsu, iki_opt, mesafe_matrisi, rastgele_tur, test_sehirleri, tur_uzunlugu
from aco_el_hesabi import BASLANGIC, D, RASSAL, ant_system

KLASOR = "gorseller"
YUZEY, METIN, SOLUK, IZGARA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
MAVI, TURUNCU = "#2a78d6", "#eb6834"

plt.rcParams.update(
    {
        "figure.facecolor": YUZEY,
        "axes.facecolor": YUZEY,
        "axes.edgecolor": IZGARA,
        "axes.labelcolor": SOLUK,
        "xtick.color": SOLUK,
        "ytick.color": SOLUK,
        "text.color": METIN,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def feromon_el_hesabi(dosya):
    """5 şehirli örnekte feromon matrisinin 0., 1. ve 2. iterasyon sonundaki hâli."""
    _, _, _, _, log = ant_system(D, BASLANGIC, RASSAL, n_iter=2, kayit=True)
    matrisler = [log[0]["tau_basi"], log[0]["tau_sonu"], log[1]["tau_sonu"]]
    basliklar = ["başlangıç (tau = 1)", "1. iterasyon sonu", "2. iterasyon sonu"]

    n = len(D)
    aci = np.pi / 2 + 2 * np.pi * np.arange(n) / n
    konum = np.c_[np.cos(aci), np.sin(aci)]
    tmax = max(m.max() for m in matrisler)

    fig, eksenler = plt.subplots(1, 3, figsize=(13, 4.6))
    for ax, tau, baslik in zip(eksenler, matrisler, basliklar):
        for i in range(n):
            for j in range(i + 1, n):
                ax.plot(
                    [konum[i, 0], konum[j, 0]],
                    [konum[i, 1], konum[j, 1]],
                    color=MAVI,
                    lw=0.4 + 7.0 * tau[i, j] / tmax,
                    solid_capstyle="round",
                    zorder=1,
                )
                orta = (konum[i] + konum[j]) / 2
                # etiketleri kenarın ortasından biraz merkeze doğru it: kesişimlerde üst üste binmesin
                ax.text(
                    orta[0] * 0.92, orta[1] * 0.92, f"{tau[i, j]:.2f}",
                    ha="center", va="center", fontsize=7.5, color=METIN,
                    bbox=dict(boxstyle="round,pad=0.15", fc=YUZEY, ec="none", alpha=0.9),
                    zorder=3,
                )
        ax.scatter(konum[:, 0], konum[:, 1], s=420, color=YUZEY, edgecolor=METIN, lw=1.2, zorder=4)
        for i in range(n):
            ax.text(konum[i, 0], konum[i, 1], str(i + 1), ha="center", va="center", fontsize=11, zorder=5)
        ax.set_title(baslik, fontsize=11)
        ax.set_xlim(-1.25, 1.25)
        ax.set_ylim(-1.25, 1.25)
        ax.set_aspect("equal")
        ax.axis("off")

    fig.suptitle(
        "Feromon izi: kenar kalınlığı ve etiketi tau değerini gösterir (şema, mesafeler ölçekli değil)",
        fontsize=11,
        color=SOLUK,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(dosya, dpi=150)
    plt.close(fig)


def yakinsama(dosya, mesafe, nn_en_iyi, iki_opt_en_iyi, tohumlar=range(10)):
    """20 şehirde, 10 tohum için 'şimdiye kadarki en iyi' tur uzunluğu."""
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for ad, alpha, renk in (("ACO (alpha = 1)", 1.0, MAVI), ("feromonsuz (alpha = 0)", 0.0, TURUNCU)):
        gecmisler = np.array(
            [ACO(mesafe, n_iter=200, alpha=alpha, seed=s).optimize()[2] for s in tohumlar]
        )
        x = np.arange(1, gecmisler.shape[1] + 1)
        for g in gecmisler:
            ax.plot(x, g, color=renk, lw=0.8, alpha=0.25)
        ax.plot(x, gecmisler.mean(axis=0), color=renk, lw=2.2, label=f"{ad}: 10 tohumun ortalaması")

    ax.axhline(nn_en_iyi, color=SOLUK, lw=1, ls=(0, (4, 3)))
    ax.text(200, nn_en_iyi + 1.2, f"en yakın komşu (en iyi başlangıç): {nn_en_iyi:.1f}", ha="right", va="bottom",
            fontsize=8.5, color=SOLUK)
    ax.axhline(iki_opt_en_iyi, color=SOLUK, lw=1, ls=(0, (1, 2)))
    ax.text(200, iki_opt_en_iyi - 1.2, f"2-opt (200 başlangıç): {iki_opt_en_iyi:.1f}", ha="right", va="top",
            fontsize=8.5, color=SOLUK)

    ax.set_xlabel("iterasyon")
    ax.set_ylabel("şimdiye kadarki en iyi tur uzunluğu")
    ax.set_title("20 şehirli TSP: ACO yakınsaması (ince çizgiler tek tohumlar)", fontsize=11, loc="left")
    ax.set_ylim(330, 450)
    ax.grid(axis="y", color=IZGARA, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(dosya, dpi=150)
    plt.close(fig)


def tur_ciz(dosya, koord, tur, L):
    fig, ax = plt.subplots(figsize=(6, 6))
    yol = np.array(list(tur) + [tur[0]])
    ax.plot(koord[yol, 0], koord[yol, 1], color=MAVI, lw=2, zorder=1)
    ax.scatter(koord[:, 0], koord[:, 1], s=260, color=YUZEY, edgecolor=METIN, lw=1.1, zorder=2)
    for i, (x, y) in enumerate(koord):
        ax.text(x, y, str(i + 1), ha="center", va="center", fontsize=8.5, zorder=3)
    ax.set_title(f"ACO'nun bulduğu tur (tohum 0), uzunluk = {L:.2f}", fontsize=11, loc="left")
    ax.set_aspect("equal")
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.grid(color=IZGARA, lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(dosya, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(KLASOR, exist_ok=True)

    koord = test_sehirleri(20, seed=42)  # aco.py'deki test ile aynı şehirler
    mesafe = mesafe_matrisi(koord)
    n = len(koord)
    rng = np.random.default_rng(0)  # aco.py'deki referans hesapla aynı rastgele akış
    for _ in range(1000):
        rastgele_tur(n, rng)  # aco.py'de önce 1000 rastgele tur çekiliyor
    nn_en_iyi = min(tur_uzunlugu(en_yakin_komsu(mesafe, s), mesafe) for s in range(n))
    iki_opt_en_iyi = min(tur_uzunlugu(iki_opt(rastgele_tur(n, rng), mesafe), mesafe) for _ in range(200))

    feromon_el_hesabi(f"{KLASOR}/feromon_el_hesabi.png")
    yakinsama(f"{KLASOR}/yakinsama_aco.png", mesafe, nn_en_iyi, iki_opt_en_iyi)
    tur, L, _ = ACO(mesafe, n_iter=200, seed=0).optimize()
    tur_ciz(f"{KLASOR}/tur_20_sehir.png", koord, tur, L)
    print(f"2-opt referansı = {iki_opt_en_iyi:.2f}, en yakın komşu = {nn_en_iyi:.2f}, ACO (tohum 0) = {L:.2f}")
    print(f"görseller '{KLASOR}/' klasörüne yazıldı")
