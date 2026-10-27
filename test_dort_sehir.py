"""aco_dort_sehir.py'nin el hesabıyla uyumunu doğrular.

    python -m unittest -v test_dort_sehir
"""

import unittest

import aco_dort_sehir as aco

TURLAR_1 = [["A", "B", "D", "C"], ["A", "D", "B", "C"]]


class DortSehirTesti(unittest.TestCase):
    def setUp(self):
        tau0 = {k: 1.0 for k in aco.MESAFE}
        # iterasyon 1 sonrası, el hesabındaki gibi 2 basamağa yuvarlanmış
        self.tau1 = aco.feromon_guncelle(tau0, TURLAR_1, aco.RHO, yuvarla=2, yazdir=False)

    def test_tur_uzunluklari(self):
        self.assertEqual(aco.tur_uzunlugu(TURLAR_1[0]), 14)
        self.assertEqual(aco.tur_uzunlugu(TURLAR_1[1]), 31)

    def test_iterasyon1_feromon(self):
        beklenen = {("A", "B"): 0.57, ("A", "C"): 0.60, ("A", "D"): 0.53,
                    ("B", "C"): 0.53, ("B", "D"): 0.60, ("C", "D"): 0.57}
        for k, deger in beklenen.items():
            self.assertAlmostEqual(self.tau1[k], deger, places=4, msg=k)

    def test_a_dan_olasiliklar(self):
        _, olasilik, payda = aco.gecis_olasiliklari("A", ["B", "C", "D"], self.tau1, aco.ALPHA, aco.BETA)
        self.assertAlmostEqual(payda, 0.7553, places=4)
        self.assertAlmostEqual(olasilik["B"], 0.7546, places=4)
        self.assertAlmostEqual(olasilik["C"], 0.1986, places=4)
        self.assertAlmostEqual(olasilik["D"], 0.0468, places=4)
        self.assertAlmostEqual(sum(olasilik.values()), 1.0, places=9)

    def test_a_dan_kumulatif_araliklar(self):
        _, olasilik, _ = aco.gecis_olasiliklari("A", ["B", "C", "D"], self.tau1, aco.ALPHA, aco.BETA)
        araliklar = aco.kumulatif_araliklar(olasilik)
        self.assertEqual([s for s, _, _ in araliklar], ["D", "C", "B"])  # küçükten büyüğe
        self.assertAlmostEqual(araliklar[0][2], 0.0468, places=4)
        self.assertAlmostEqual(araliklar[1][2], 0.2454, places=4)
        self.assertAlmostEqual(araliklar[2][2], 1.0, places=9)

    def test_b_den_olasiliklar(self):
        _, olasilik, payda = aco.gecis_olasiliklari("B", ["C", "D"], self.tau1, aco.ALPHA, aco.BETA)
        self.assertAlmostEqual(payda, 0.21625, places=5)
        self.assertAlmostEqual(olasilik["C"], 0.3064, places=4)
        self.assertAlmostEqual(olasilik["D"], 0.6936, places=4)

    def test_rulet_secimi(self):
        _, olasilik, _ = aco.gecis_olasiliklari("A", ["B", "C", "D"], self.tau1, aco.ALPHA, aco.BETA)
        araliklar = aco.kumulatif_araliklar(olasilik)
        self.assertEqual(aco.rulet(araliklar, 0.03), "D")
        self.assertEqual(aco.rulet(araliklar, 0.10), "C")
        self.assertEqual(aco.rulet(araliklar, 0.47), "B")

    def test_iterasyon2_tur(self):
        tur = aco.tur_olustur("A", self.tau1, aco.ALPHA, aco.BETA, [0.47, 0.82], yazdir=False)
        self.assertEqual(tur, ["A", "B", "D", "C"])  # r1=0.47 → B, r2=0.82 → D, kalan tek şehir C
        self.assertEqual(aco.tur_uzunlugu(tur), 14)

    def test_iterasyon2_feromon(self):
        tur = ["A", "B", "D", "C"]
        tau2 = aco.feromon_guncelle(self.tau1, [tur], aco.RHO, yazdir=False)
        beklenen = {("A", "B"): 0.3564, ("A", "C"): 0.3714, ("A", "D"): 0.2650,
                    ("B", "C"): 0.2650, ("B", "D"): 0.3714, ("C", "D"): 0.3564}
        for k, deger in beklenen.items():
            self.assertAlmostEqual(tau2[k], deger, places=4, msg=k)

    def test_kullanilmayan_yol_sadece_buharlasir(self):
        tur = ["A", "B", "D", "C"]  # A-D ve B-C kullanılmıyor
        tau2 = aco.feromon_guncelle(self.tau1, [tur], aco.RHO, yazdir=False)
        for k in (("A", "D"), ("B", "C")):
            self.assertAlmostEqual(tau2[k], (1 - aco.RHO) * self.tau1[k], places=9)


if __name__ == "__main__":
    unittest.main()
