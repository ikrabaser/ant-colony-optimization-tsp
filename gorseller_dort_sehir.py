"""4 şehirli örneğin görsellerini üretir (gorseller/ klasörüne PNG yazar).

    python gorseller_dort_sehir.py

Sayıların hepsi aco_dort_sehir.py'deki fonksiyonlardan gelir, elle yazılmamıştır.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from aco_dort_sehir import (
    ALPHA,
    BETA,
    MESAFE,
    RHO,
    SEHIRLER,
    feromon_guncelle,
    gecis_olasiliklari,
    kumulatif_araliklar,
    rulet,
    tur_kenarlari,
    tur_olustur,
    tur_uzunlugu,
    yol_adi,
)

KLASOR = "gorseller"
YUZEY, METIN, SOLUK, IZGARA = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
MAVI, TURUNCU = "#2a78d6", "#eb6834"

TURLAR_1 = [["A", "B", "D", "C"], ["A", "D", "B", "C"]]  # iterasyon 1'in iki karıncası
RASSAL = [0.47, 0.82]  # iterasyon 2'deki karıncanın rassal sayıları
KONUM = {"A": (-1.0, 0.0), "B": (0.0, 0.75), "C": (0.0, -0.75), "D": (1.0, 0.0)}

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


def hesapla():
    """Örneğin tüm ara değerlerini kod fonksiyonlarıyla üretir."""
    tau0 = {k: 1.0 for k in MESAFE}
    tau1 = feromon_guncelle(tau0, TURLAR_1, RHO, yuvarla=2, yazdir=False)

    tur, adimlar, rassal = ["A"], [], list(RASSAL)
    while len(tur) < len(SEHIRLER):
        simdiki = tur[-1]
        adaylar = [s for s in SEHIRLER if s not in tur]
        _, olasilik, _ = gecis_olasiliklari(simdiki, adaylar, tau1, ALPHA, BETA)
        araliklar = kumulatif_araliklar(olasilik)
        if len(adaylar) == 1:
            secilen, r = adaylar[0], None
        else:
            r = rassal.pop(0)
            secilen = rulet(araliklar, r)
        adimlar.append(
            {"simdiki": simdiki, "araliklar": araliklar, "r": r, "secilen": secilen, "p": olasilik[secilen]}
        )
        tur.append(secilen)

    assert tur == tur_olustur("A", tau1, ALPHA, BETA, RASSAL, yazdir=False)  # kodla aynı sonuç
    tau2 = feromon_guncelle(tau1, [tur], RHO, yazdir=False)
    return tau0, tau1, tau2, tur, adimlar


# --------------------------------------------------------------------------
def dugumler_ciz(ax):
    for s, (x, y) in KONUM.items():
        ax.scatter([x], [y], s=520, color=YUZEY, edgecolor=METIN, lw=1.2, zorder=4)
        ax.text(x, y, s, ha="center", va="center", fontsize=11, zorder=5)


def kenar_etiketi(ax, k, metin, renk=METIN):
    (x1, y1), (x2, y2) = KONUM[k[0]], KONUM[k[1]]
    x, y = (x1 + x2) / 2, (y1 + y2) / 2
    if k == ("A", "D"):  # merkezdeki kesişimde üst üste binmesin
        x = 0.5
    if k == ("B", "C"):
        y = 0.38
    ax.text(x, y, metin, ha="center", va="center", fontsize=9, color=renk, zorder=3,
            bbox=dict(boxstyle="round,pad=0.15", fc=YUZEY, ec="none", alpha=0.95))


def eksen_hazirla(ax, baslik):
    ax.set_title(baslik, fontsize=11, loc="left")
    ax.set_xlim(-1.75, 1.75)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal")
    ax.axis("off")


def graf(dosya, tau1, tur, adimlar):
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(14.5, 4.4))

    # 1) mesafeler
    for k, d in MESAFE.items():
        (x1, y1), (x2, y2) = KONUM[k[0]], KONUM[k[1]]
        a1.plot([x1, x2], [y1, y2], color=SOLUK, lw=1.4, zorder=1)
        kenar_etiketi(a1, k, str(d))
    dugumler_ciz(a1)
    eksen_hazirla(a1, "Mesafeler")

    # 2) iterasyon 1 sonrası feromon
    tmax = max(tau1.values())
    for k, t in tau1.items():
        (x1, y1), (x2, y2) = KONUM[k[0]], KONUM[k[1]]
        a2.plot([x1, x2], [y1, y2], color=MAVI, lw=9.0 * t / tmax, solid_capstyle="round", zorder=1)
        kenar_etiketi(a2, k, f"{t:.2f}")
    dugumler_ciz(a2)
    eksen_hazirla(a2, "İterasyon 1 sonrası feromon (kalınlık = tau)")

    # 3) iterasyon 2: karıncanın turu
    for k in MESAFE:
        (x1, y1), (x2, y2) = KONUM[k[0]], KONUM[k[1]]
        a3.plot([x1, x2], [y1, y2], color=IZGARA, lw=1.6, zorder=1)
    kayit = ["1) p = {:.4f}".format(adimlar[0]["p"]), "2) p = {:.4f}".format(adimlar[1]["p"]),
             "3) tek aday, rulet yok", "4) başlangıca dönüş"]
    konumlar = [(-0.6, 0.47, "right"), (0.6, 0.47, "left"), (0.6, -0.47, "left"), (-0.6, -0.47, "right")]
    kapali = tur + [tur[0]]
    for i in range(len(tur)):
        bas, son = KONUM[kapali[i]], KONUM[kapali[i + 1]]
        a3.annotate("", xy=son, xytext=bas, zorder=2,
                    arrowprops=dict(arrowstyle="-|>", color=TURUNCU, lw=2.2, shrinkA=15, shrinkB=15))
        x, y, ha = konumlar[i]
        a3.text(x, y, kayit[i], ha=ha, va="center", fontsize=9, color=METIN)
    dugumler_ciz(a3)
    toplam = " + ".join(str(MESAFE[k]) for k in tur_kenarlari(tur))
    a3.text(0, -1.08, f"L = {toplam} = {tur_uzunlugu(tur)}", ha="center", va="center", fontsize=10, color=SOLUK)
    eksen_hazirla(a3, "İterasyon 2: karıncanın turu")

    fig.tight_layout()
    fig.savefig(dosya, dpi=150)
    plt.close(fig)


def rulet_cubugu(dosya, adimlar):
    rulet_adimlari = [a for a in adimlar if a["r"] is not None]
    fig, eksenler = plt.subplots(len(rulet_adimlari), 1, figsize=(9, 2.3 * len(rulet_adimlari) + 0.7))
    for sira, (ax, a) in enumerate(zip(eksenler, rulet_adimlari), 1):
        sinirlar = [0.0]
        for sehir, bas, bit in a["araliklar"]:
            secili = sehir == a["secilen"]
            ax.barh(0, bit - bas, left=bas, height=0.5, color=TURUNCU if secili else MAVI,
                    edgecolor=YUZEY, linewidth=2.5)
            ax.text((bas + bit) / 2, 0.32, f"{a['simdiki']}→{sehir}\n{bit - bas:.4f}",
                    ha="center", va="bottom", fontsize=8.5, color=METIN)
            sinirlar.append(bit)
        r = a["r"]
        ax.plot([r, r], [-0.30, 0.25], color=METIN, lw=1.6, zorder=5)
        ax.text(r, -0.62, f"r = {r}", ha="center", va="top", fontsize=9.5, color=METIN)
        ax.set_xticks(sinirlar)
        ax.set_xticklabels(["0"] + [f"{b:.4f}" for b in sinirlar[1:-1]] + ["1"], fontsize=8.5)
        ax.set_xlim(-0.01, 1.01)
        ax.set_ylim(-1.0, 1.05)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(f"Adım {sira}: karınca {a['simdiki']} şehrinde, kümülatif aralıklar (olasılık küçükten büyüğe)",
                     fontsize=10.5, loc="left")
    fig.legend(handles=[Patch(color=TURUNCU, label="rassal sayının düştüğü aralık (seçilen şehir)"),
                        Patch(color=MAVI, label="diğer aralıklar")],
               loc="lower center", ncol=2, frameon=False, fontsize=9)
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    fig.savefig(dosya, dpi=150)
    plt.close(fig)


def feromon_degisimi(dosya, tau1, tau2, tur):
    kenarlar = sorted(MESAFE)
    kullanilan = set(tur_kenarlari(tur))
    x = list(range(len(kenarlar)))
    w = 0.36
    L = tur_uzunlugu(tur)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    onceki = [tau1[k] for k in kenarlar]
    sonraki = [tau2[k] for k in kenarlar]
    ax.bar([i - w / 2 for i in x], onceki, w, color=MAVI, alpha=0.4, edgecolor=YUZEY, linewidth=2,
           label="güncelleme öncesi (iterasyon 1 sonu)")
    ax.bar([i + w / 2 for i in x], sonraki, w, color=MAVI, edgecolor=YUZEY, linewidth=2,
           label="güncelleme sonrası (iterasyon 2 sonu)")
    for i, (o, s) in enumerate(zip(onceki, sonraki)):
        ax.text(i - w / 2, o + 0.012, f"{o:.2f}", ha="center", va="bottom", fontsize=8.5, color=SOLUK)
        ax.text(i + w / 2, s + 0.012, f"{s:.4f}", ha="center", va="bottom", fontsize=8.5, color=METIN)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{yol_adi(k)}\n{'tur içinde' if k in kullanilan else 'kullanılmadı'}" for k in kenarlar],
                       fontsize=9)
    ax.set_ylabel("feromon (tau)")
    ax.set_ylim(0, max(onceki) * 1.4)
    ax.grid(axis="y", color=IZGARA, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    ax.set_title(f"Feromon güncellemesi (rho = {RHO}): her yol buharlaşır, tur içindeki yollara 1/{L} = {1 / L:.4f} eklenir",
                 fontsize=10.5, loc="left")
    fig.tight_layout()
    fig.savefig(dosya, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(KLASOR, exist_ok=True)
    tau0, tau1, tau2, tur, adimlar = hesapla()
    graf(f"{KLASOR}/dort_sehir_graf.png", tau1, tur, adimlar)
    rulet_cubugu(f"{KLASOR}/dort_sehir_rulet.png", adimlar)
    feromon_degisimi(f"{KLASOR}/dort_sehir_feromon_degisimi.png", tau1, tau2, tur)
    print(f"görseller '{KLASOR}/' klasörüne yazıldı")
