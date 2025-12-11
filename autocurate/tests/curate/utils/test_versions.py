import os, sys, pdb, shutil, logging, json
import unittest as test

import curate.utils.versions as util

class TestVersion(test.TestCase):

    def test_ctor(self):
        ver = util.Version("3.3.5.0")
        self.assertEqual(ver._vs, "3.3.5.0")
        self.assertEqual(ver.fields, [3,3,5,0])

    def testEQ(self):
        ver = util.Version("3.3.0")
        self.assertEqual(ver, util.Version("3.3.0"))
        self.assertTrue(ver == "3.3.0")
        self.assertFalse(ver == "3.3.1")
        self.assertFalse(ver == "1.3")

    def testNE(self):
        ver = util.Version("3.3.0")
        self.assertNotEqual(ver, util.Version("3.3.2"))
        self.assertFalse(ver != "3.3.0")
        self.assertTrue(ver != "3.3.1")
        self.assertTrue(ver != "1.3")

    def testGE(self):
        ver = util.Version("3.3.0")
        self.assertTrue(ver >= "3.2.0")
        self.assertTrue(ver >= "3.3.0")
        self.assertTrue(ver >= "1.3")

        self.assertFalse(ver >= "5.3")
        self.assertFalse(ver >= util.Version("5.3"))

    def testGT(self):
        ver = util.Version("3.3.0")
        self.assertTrue(ver > "3.2.0")
        self.assertTrue(ver > "1.3")

        self.assertFalse(ver > "3.3.0")
        self.assertFalse(ver >= "5.3")
        self.assertFalse(ver >= util.Version("5.3"))

    def testLE(self):
        ver = util.Version("3.3.0")
        self.assertTrue(ver <= "3.5.0")
        self.assertTrue(ver <= "3.3.1")
        self.assertTrue(ver <= "3.3.0")
        self.assertTrue(ver <= "5.3")

        self.assertFalse(ver <= "1.3")
        self.assertFalse(ver <= util.Version("2.3"))

    def testLT(self):
        ver = util.Version("3.3.0")
        self.assertTrue(ver < "3.5.0")
        self.assertTrue(ver < "3.3.1")
        self.assertTrue(ver < "5.3")

        self.assertFalse(ver < "3.3.0")
        self.assertFalse(ver < "1.3")
        self.assertFalse(ver < util.Version("2.3"))

    def testIsProper(self):
        self.assertTrue(util.Version.is_proper_version("33"))
        self.assertTrue(util.Version.is_proper_version("3.3"))
        self.assertTrue(util.Version.is_proper_version("13_3_0"))
        self.assertTrue(util.Version.is_proper_version("1.23_400.10"))

        self.assertFalse(util.Version.is_proper_version("-33"))
        self.assertFalse(util.Version.is_proper_version("3.3r23"))
        self.assertFalse(util.Version.is_proper_version("13.3.0-1"))
        self.assertFalse(util.Version.is_proper_version("dev"))

    def test_sorted(self):
        vers = "2.0.1 3.0 0.1.1 0 12.3 2.0.1.0".split()
        expect = "0 0.1.1 2.0.1 2.0.1.0 3.0 12.3".split()
        self.assertEqual(sorted(vers, key=util.Version), expect)

    def test_cmp_versions(self):
        self.assertEqual(util.cmp_versions("1.0.0", "1.0.2"), -1)
        self.assertEqual(util.cmp_versions("1.0.1", "1.0.1"),  0)
        self.assertEqual(util.cmp_versions("1.0.2", "1.0.1"),  1)
        self.assertEqual(util.cmp_versions("1.0", "1.0.2"), -1)
        self.assertEqual(util.cmp_versions("1.0.0", "1.0"),  1)
        self.assertEqual(util.cmp_versions("1", "1.0"),  -1)
        self.assertEqual(util.cmp_versions("1.0.2", "1.1.0"), -1)
        self.assertEqual(util.cmp_versions("1.2.1", "1.0.1"),  1)
        self.assertEqual(util.cmp_versions("1.0.2", "4.0.1"), -1)
        self.assertEqual(util.cmp_versions("12.0.2", "4.0.1"), 1)
    
class TestOARVersion(test.TestCase):

    def test_ctor(self):
        ver = util.OARVersion("3.3.5.0")
        self.assertEqual(ver._vs, "3.3.5.0")
        self.assertEqual(ver.fields, [3,3,5,0])
        self.assertEqual(ver.suffix, '')

        ver = util.OARVersion("3.3.5.0.1goob30")
        self.assertEqual(ver._vs, "3.3.5.0.1")
        self.assertEqual(ver.fields, [3,3,5,0,1])
        self.assertEqual(ver.suffix, 'goob30')

        ver = util.OARVersion("3.3+what")
        self.assertEqual(ver._vs, "3.3")
        self.assertEqual(ver.fields, [3,3])
        self.assertEqual(ver.suffix, '+what')

    def testEQ(self):
        ver = util.OARVersion("3.3.0rc1")
        self.assertEqual(ver, util.Version("3.3.0rc1"))
        self.assertTrue(ver == "3.3.0rc1")
        self.assertFalse(ver == "3.3.0")
        self.assertFalse(ver == "3.3.1")
        self.assertFalse(ver == "1.3")

        ver = util.OARVersion("3.3.0")
        self.assertEqual(ver, util.Version("3.3.0"))
        self.assertTrue(ver == "3.3.0")
        self.assertFalse(ver == "3.3.1")
        self.assertFalse(ver == "1.3")

    def testLT(self):
        ver = util.OARVersion("3.3.0")
        self.assertTrue(ver < "3.5.0")
        self.assertTrue(ver < "3.3.1")
        self.assertTrue(ver < "3.3.1+")
        self.assertTrue(ver < "5.3")

        self.assertFalse(ver < "3.3.0")
        self.assertFalse(ver < "1.3")
        self.assertFalse(ver < util.Version("2.3"))

        ver = util.OARVersion("3.3.0+ (in edit)")
        self.assertFalse(ver < "3.3.0")
        self.assertTrue(ver < "3.3.0#rc1")
        self.assertTrue(ver < "3.3.0rc1")
        
        self.assertFalse(ver < "3.3.0+")
        self.assertFalse(ver < "3.3.0+ (in Edit)")

        ver = util.OARVersion("3.3.0rc3")
        self.assertFalse(ver < "3.3.0alpha3")
        

    def test_cmp_oar_versions(self):
        self.assertEqual(util.cmp_oar_versions("1.0.0", "1.0.2"), -1)
        self.assertEqual(util.cmp_oar_versions("1.0.1", "1.0.1"),  0)
        self.assertEqual(util.cmp_oar_versions("1.0.2", "1.0.1"),  1)
        self.assertEqual(util.cmp_oar_versions("1.0", "1.0.2"), -1)
        self.assertEqual(util.cmp_oar_versions("1.0.0", "1.0"),  1)
        self.assertEqual(util.cmp_oar_versions("1", "1.0"),  -1)
        self.assertEqual(util.cmp_oar_versions("1.0.2", "1.1.0"), -1)
        self.assertEqual(util.cmp_oar_versions("1.2.1", "1.0.1"),  1)
        self.assertEqual(util.cmp_oar_versions("1.0.2", "4.0.1"), -1)
        self.assertEqual(util.cmp_oar_versions("12.0.2", "4.0.1"), 1)
    
        self.assertEqual(util.cmp_oar_versions("1.0.1", "1.0.1+draft"), -1)
        self.assertEqual(util.cmp_oar_versions("1.0.1+", "1.0.1"),  1)
        self.assertEqual(util.cmp_oar_versions("1.0.1+", "1.0.1+"), 0)
        self.assertEqual(util.cmp_oar_versions("1.0.12alpha", "1.0.12beta"), -1)
        self.assertEqual(util.cmp_oar_versions("1.0.12beta", "1.0.12alpha"),  1)
        self.assertEqual(util.cmp_oar_versions("1.0.12beta", "1.0.12beta"),   0)
        self.assertEqual(util.cmp_oar_versions("1.0.1beta", "1.0.12beta"),   -1)
        self.assertEqual(util.cmp_oar_versions("1.0.12+", "1.0.12beta"),     -1)

    def test_increment_field(self):
        ver = util.OARVersion("3.3.5.9")
        self.assertEqual(str(ver), "3.3.5.9")
        ver.increment_field(3)
        self.assertEqual(str(ver), "3.3.5.10")
        ver.increment_field(-1)
        self.assertEqual(str(ver), "3.3.5.11")
        ver.increment_field(2)
        self.assertEqual(str(ver), "3.3.6.0")
        ver.increment_field(0)
        self.assertEqual(str(ver), "4.0.0.0")
        ver.increment_field(-1)
        self.assertEqual(str(ver), "4.0.0.1")
        ver.increment_field(-4)
        self.assertEqual(str(ver), "5.0.0.0")

        with self.assertRaises(IndexError):
            ver.increment_field(-10)
        
    def test_trivial_incr(self):
        ver = util.OARVersion("1.0")
        ver.trivial_incr()
        self.assertEqual(str(ver), "1.0.1")
        ver.trivial_incr()
        self.assertEqual(str(ver), "1.0.2")
        
        ver = util.OARVersion("1.0.9")
        ver.trivial_incr()
        self.assertEqual(str(ver), "1.0.10")

        ver = util.OARVersion("1.0.3.5")
        ver.trivial_incr()
        self.assertEqual(str(ver), "1.0.4.0")

        ver = util.OARVersion("1.0.3rc5")
        ver.trivial_incr()
        self.assertEqual(str(ver), "1.0.4rc5")
        ver.trivial_incr().drop_suffix()
        self.assertEqual(str(ver), "1.0.5")

    def test_minor_incr(self):
        ver = util.OARVersion("1.0")
        ver.minor_incr()
        self.assertEqual(str(ver), "1.1")

        ver = util.OARVersion("1.0.1")
        ver.minor_incr()
        self.assertEqual(str(ver), "1.1.0")

    def test_major_incr(self):
        ver = util.OARVersion("13")
        ver.major_incr()
        self.assertEqual(str(ver), "14")

        ver = util.OARVersion("2.3")
        ver.major_incr()
        self.assertEqual(str(ver), "3.0")

        ver = util.OARVersion("1.0.1")
        ver.major_incr()
        self.assertEqual(str(ver), "2.0.0")
        
        
                    
                         
if __name__ == '__main__':
    test.main()
