import unittest, pdb, pynoid as noid
from random import randint

from nistoar.id import minter

class TestSeqreg(unittest.TestCase):

    def test_seqFor(self):
        mask = "ede"
        reg = minter.NoidMinter.seqreg(0, "ede")

        self.assertEquals(reg.seqFor("000"), 0)
        self.assertEquals(reg.seqFor("001"), 1)
        self.assertEquals(reg.seqFor("008"), 8)
        self.assertEquals(reg.seqFor("00b"), 10)
        self.assertEquals(reg.seqFor("01f"), 42)
        self.assertEquals(reg.seqFor("10z"), 318)
        self.assertEquals(reg.seqFor("34g"), 1000)
        self.assertEquals(reg.seqFor("m79"), 5432)

        for mask in "dddd eeee eded".split():
            reg = minter.NoidMinter.seqreg(0, mask)
            for i in range(5, 6000, 5):
                n = reg.seqFor(noid.mint(mask, i))
                self.assertEquals(n, i,
                             "{0} != {1} for mask={2}".format(n, i, repr(mask)))

    def testseqFor_k(self):
        reg = minter.NoidMinter.seqreg(0, "edek")

        self.assertEquals(reg.seqFor("0000"), 0)
        self.assertEquals(reg.seqFor("0013"), 1)
        self.assertEquals(reg.seqFor("008t"), 8)
        self.assertEquals(reg.seqFor("00b1"), 10)
        self.assertEquals(reg.seqFor("m791"), 5432)
        
    def testseqFor_rs(self):
        reg = minter.NoidMinter.seqreg(0, "rede")

        self.assertEquals(reg.seqFor("000"), 0)
        self.assertEquals(reg.seqFor("001"), 1)
        self.assertEquals(reg.seqFor("008"), 8)
        self.assertEquals(reg.seqFor("00b"), 10)
        self.assertEquals(reg.seqFor("m79"), 5432)
        
        reg = minter.NoidMinter.seqreg(0, "sede")

        self.assertEquals(reg.seqFor("000"), 0)
        self.assertEquals(reg.seqFor("001"), 1)
        self.assertEquals(reg.seqFor("008"), 8)
        self.assertEquals(reg.seqFor("00b"), 10)
        self.assertEquals(reg.seqFor("m79"), 5432)
        
    def testseqFor_pre(self):
        reg = minter.NoidMinter.seqreg(0, "pref.rede")

        self.assertEquals(reg.seqFor("000"), 0)
        self.assertEquals(reg.seqFor("001"), 1)
        self.assertEquals(reg.seqFor("008"), 8)
        self.assertEquals(reg.seqFor("00b"), 10)
        self.assertEquals(reg.seqFor("m79"), 5432)

        self.assertEquals(reg.seqFor("pref000"), 0)
        self.assertEquals(reg.seqFor("pref001"), 1)
        self.assertEquals(reg.seqFor("pref008"), 8)
        self.assertEquals(reg.seqFor("pref00b"), 10)
        self.assertEquals(reg.seqFor("prefm79"), 5432)
        
    def testseqFor_z(self):
        reg = minter.NoidMinter.seqreg(0, "zede")

        self.assertEquals(reg.seqFor("000"), 0)
        self.assertEquals(reg.seqFor("001"), 1)
        self.assertEquals(reg.seqFor("008"), 8)
        self.assertEquals(reg.seqFor("00b"), 10)
        self.assertEquals(reg.seqFor("m79"), 5432)
        self.assertEquals(reg.seqFor("16x768"), 8765432)
        
        reg = minter.NoidMinter.seqreg(0, "zdee")

        self.assertEquals(reg.seqFor("000"), 0)
        self.assertEquals(reg.seqFor("001"), 1)
        self.assertEquals(reg.seqFor("008"), 8)
        self.assertEquals(reg.seqFor("00b"), 10)
        self.assertEquals(reg.seqFor("6f9"), 5432)
        self.assertEquals(reg.seqFor("10422m8"), 8765432)
        
    def testseqFor_pzk(self):
        reg = minter.NoidMinter.seqreg(0, "zedek")

        self.assertEquals(reg.seqFor("0000"), 0)
        self.assertEquals(reg.seqFor("0013"), 1)
        self.assertEquals(reg.seqFor("008t"), 8)
        self.assertEquals(reg.seqFor("00b1"), 10)
        self.assertEquals(reg.seqFor("m791"), 5432)
        self.assertEquals(reg.seqFor("16x768w"), 8765432)
        
        reg = minter.NoidMinter.seqreg(0, "zub0.zdeek")

        self.assertEquals(reg.seqFor("zub00000"), 0)
        self.assertEquals(reg.seqFor("zub00013"), 1)
        self.assertEquals(reg.seqFor("zub0008t"), 8)
        self.assertEquals(reg.seqFor("zub000b1"), 10)
        self.assertEquals(reg.seqFor("zub06f91"), 5432)
        self.assertEquals(reg.seqFor("zub010422m8q"), 8765432)

class TestNoidMinter(unittest.TestCase):

    def setUp(self):
        self.minter = minter.NoidMinter('zede', 0)

    def test_unissued(self):
        self.assertFalse(self.minter.issued("10422m"))
        self.assertFalse(self.minter.issued("6f6"))
        self.assertFalse(self.minter.issued("00b"))
        self.assertFalse(self.minter.issued("001"))
        self.assertFalse(self.minter.issued("000"))

    def test_mint(self):
        self.assertEquals(self.minter.mint(), "000")
        self.assertEquals(self.minter.mint(), "001")
        self.assertEquals(self.minter.mint(), "002")
        self.minter.nextn = 42
        self.assertEquals(self.minter.mint(), "01f")
        self.minter.nextn = 5432
        self.assertEquals(self.minter.mint(), "m79")
        self.minter.nextn = 5420
        self.assertEquals(self.minter.mint(), "m7b")
        self.minter.nextn = 8765432
        self.assertEquals(self.minter.mint(), "16x768")

    def test_mint_k(self):
        self.minter = minter.NoidMinter(self.minter.mask+'k', 0)
        self.assertEquals(self.minter.mint(), "0000")
        self.assertEquals(self.minter.mint(), "0013")
        self.assertEquals(self.minter.mint(), "0026")
        self.minter.nextn = 10
        self.assertEquals(self.minter.mint(), "00b1")
        self.minter.nextn = 5432
        self.assertEquals(self.minter.mint(), "m791")

    def test_masks(self):
        for mask in "dddd eeee eded".split():
            mask = "mc5."+mask
            self.minter = minter.NoidMinter(mask)
            for i in range(5, 6000, 5):
                id = noid.mint(mask, i)
                self.minter.nextn = i
                self.assertFalse(self.minter.issued(id),
                  "id {0} prematurely issued for mask={1}".format(repr(id),
                                                                  repr(mask)))
                mid = self.minter.mint()
                self.assertEquals(mid, id,
                                  "{0} != {1} for mask={2}".format(repr(mid),
                                                                   repr(id),
                                                                   repr(mask)))
                self.assertTrue(self.minter.issued(id), 
                   "id {0} forgotten for mask={1}".format(repr(id), repr(mask)))


    

        
if __name__ == '__main__':
    unittest.main()
