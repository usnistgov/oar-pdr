import os, sys, pdb, shutil, logging, json
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.preserv.bagger import utils as bagut
from nistoar.nerdm.constants import CORE_SCHEMA_URI, PUB_SCHEMA_URI

class TestVersion(test.TestCase):

    def test_ctor(self):
        ver = bagut.Version("3.3.5.0")
        self.assertEqual(ver._vs, "3.3.5.0")
        self.assertEqual(ver.fields, [3,3,5,0])

    def testEQ(self):
        ver = bagut.Version("3.3.0")
        self.assertEqual(ver, bagut.Version("3.3.0"))
        self.assertTrue(ver == "3.3.0")
        self.assertFalse(ver == "3.3.1")
        self.assertFalse(ver == "1.3")

    def testNE(self):
        ver = bagut.Version("3.3.0")
        self.assertNotEqual(ver, bagut.Version("3.3.2"))
        self.assertFalse(ver != "3.3.0")
        self.assertTrue(ver != "3.3.1")
        self.assertTrue(ver != "1.3")

    def testGE(self):
        ver = bagut.Version("3.3.0")
        self.assertTrue(ver >= "3.2.0")
        self.assertTrue(ver >= "3.3.0")
        self.assertTrue(ver >= "1.3")

        self.assertFalse(ver >= "5.3")
        self.assertFalse(ver >= bagut.Version("5.3"))

    def testGT(self):
        ver = bagut.Version("3.3.0")
        self.assertTrue(ver > "3.2.0")
        self.assertTrue(ver > "1.3")

        self.assertFalse(ver > "3.3.0")
        self.assertFalse(ver >= "5.3")
        self.assertFalse(ver >= bagut.Version("5.3"))

    def testLE(self):
        ver = bagut.Version("3.3.0")
        self.assertTrue(ver <= "3.5.0")
        self.assertTrue(ver <= "3.3.1")
        self.assertTrue(ver <= "3.3.0")
        self.assertTrue(ver <= "5.3")

        self.assertFalse(ver <= "1.3")
        self.assertFalse(ver <= bagut.Version("2.3"))

    def testLT(self):
        ver = bagut.Version("3.3.0")
        self.assertTrue(ver < "3.5.0")
        self.assertTrue(ver < "3.3.1")
        self.assertTrue(ver < "5.3")

        self.assertFalse(ver < "3.3.0")
        self.assertFalse(ver < "1.3")
        self.assertFalse(ver < bagut.Version("2.3"))

    def testIsProper(self):
        self.assertTrue(bagut.Version.is_proper_version("33"))
        self.assertTrue(bagut.Version.is_proper_version("3.3"))
        self.assertTrue(bagut.Version.is_proper_version("13_3_0"))
        self.assertTrue(bagut.Version.is_proper_version("1.23_400.10"))

        self.assertFalse(bagut.Version.is_proper_version("-33"))
        self.assertFalse(bagut.Version.is_proper_version("3.3r23"))
        self.assertFalse(bagut.Version.is_proper_version("13.3.0-1"))
        self.assertFalse(bagut.Version.is_proper_version("dev"))

    def test_sorted(self):
        vers = "2.0.1 3.0 0.1.1 0 12.3 2.0.1.0".split()
        expect = "0 0.1.1 2.0.1 2.0.1.0 3.0 12.3".split()
        self.assertEqual(sorted(vers, key=bagut.Version), expect)


class TestBagName(test.TestCase):

    def test_ctor(self):
        bagname = "mds3812.1_3.mbag0_4-14.tgz"
        bn = bagut.BagName(bagname)
        self.assertEqual(str(bn), bagname)
        self.assertEqual(bn.fields, ["mds3812", "1_3", "0_4", "14", "tgz"])
        self.assertEqual(bn.aipid, "mds3812")
        self.assertEqual(bn.version, "1.3")
        self.assertEqual(bn.multibag_profile, "0_4")
        self.assertEqual(bn.sequence, "14")
        self.assertEqual(bn.serialization, "tgz")

        bagname = "mds3812.mbag0_2-3.tar.gz"
        bn = bagut.BagName(bagname)
        self.assertEqual(str(bn), bagname)
        self.assertEqual(bn.fields, ["mds3812", "", "0_2", "3", "tar.gz"])
        self.assertEqual(bn.aipid, "mds3812")
        self.assertEqual(bn.version, "")
        self.assertEqual(bn.multibag_profile, "0_2")
        self.assertEqual(bn.sequence, "3")
        self.assertEqual(bn.serialization, "tar.gz")

        with self.assertRaises(ValueError):
            bn = bagut.BagName("goober.zip")

    def testEQ(self):
        bagname = "mds3812.1_3.mbag0_4-14.tgz"
        bn = bagut.BagName(bagname)
        self.assertTrue(bn == "mds3812.1_3.mbag0_4-14.tgz")
        self.assertTrue(bn != "mds3812.mbag0_4-14.tgz")
        self.assertTrue(bn != "mds3812.1_3.mbag0_4-14.zip")

    def testLT(self):
        bagname = "mds3812.1_3.mbag0_4-14.tgz"
        bn = bagut.BagName(bagname)

        self.assertTrue(bn < "mds3812.1_3.mbag0_4-20.tgz")
        self.assertTrue(bn < "nist3812.1_3.mbag0_4-14.tgz")
        self.assertTrue(bn < "mds3812.2_0.mbag0_4-14.tgz")
        self.assertTrue(bn < "mds3812.1_3.mbag1_0-14.tgz")
        self.assertTrue(bn < "mds3812.1_3.mbag0_4-14.zip")

        self.assertFalse(bn < "mds3812.1_3.mbag0_4-14.tgz")
        self.assertFalse(bn < "mds3812.1_3.mbag0_4-10.tgz")
        self.assertFalse(bn < "abc3812.1_3.mbag0_4-14.tgz")
        self.assertFalse(bn < "mds3812.1_3.mbag0_2-14.tgz")
        self.assertFalse(bn < "mds3812.1_3.mbag0_4-14.7z")
        self.assertFalse(bn < "mds3812.mbag0_4-14.tgz")

    def testLE(self):
        bagname = "mds3812.1_3.mbag0_4-14.tgz"
        bn = bagut.BagName(bagname)

        self.assertTrue(bn <= "mds3812.1_3.mbag0_4-20.tgz")
        self.assertTrue(bn <= "nist3812.1_3.mbag0_4-14.tgz")
        self.assertTrue(bn <= "mds3812.2_0.mbag0_4-14.tgz")
        self.assertTrue(bn <= "mds3812.1_3.mbag1_0-14.tgz")
        self.assertTrue(bn <= "mds3812.1_3.mbag0_4-14.zip")
        self.assertTrue(bn <= "mds3812.1_3.mbag0_4-14.tgz")

        self.assertFalse(bn <= "mds3812.1_3.mbag0_4-10.tgz")
        self.assertFalse(bn <= "abc3812.1_3.mbag0_4-14.tgz")
        self.assertFalse(bn <= "mds3812.1_3.mbag0_2-14.tgz")
        self.assertFalse(bn <= "mds3812.1_3.mbag0_4-14.7z")
        self.assertFalse(bn <= "mds3812.mbag0_4-14.tgz")

    def testGT(self):
        bagname = "mds3812.1_3.mbag0_4-14.tgz"
        bn = bagut.BagName(bagname)

        self.assertTrue(bn > "mds3812.1_3.mbag0_4-10.tgz")
        self.assertTrue(bn > "abc3812.1_3.mbag0_4-14.tgz")
        self.assertTrue(bn > "mds3812.1_3.mbag0_2-14.tgz")
        self.assertTrue(bn > "mds3812.1_3.mbag0_4-14.7z")
        self.assertTrue(bn > "mds3812.mbag0_4-14.tgz")

        self.assertFalse(bn > "mds3812.1_3.mbag0_4-14.tgz")
        self.assertFalse(bn > "mds3812.1_3.mbag0_4-20.tgz")
        self.assertFalse(bn > "nist3812.1_3.mbag0_4-14.tgz")
        self.assertFalse(bn > "mds3812.2_0.mbag0_4-14.tgz")
        self.assertFalse(bn > "mds3812.1_3.mbag1_0-14.tgz")
        self.assertFalse(bn > "mds3812.1_3.mbag0_4-14.zip")

    def testGE(self):
        bagname = "mds3812.1_3.mbag0_4-14.tgz"
        bn = bagut.BagName(bagname)

        self.assertTrue(bn >= "mds3812.1_3.mbag0_4-10.tgz")
        self.assertTrue(bn >= "abc3812.1_3.mbag0_4-14.tgz")
        self.assertTrue(bn >= "mds3812.1_3.mbag0_2-14.tgz")
        self.assertTrue(bn >= "mds3812.1_3.mbag0_4-14.7z")
        self.assertTrue(bn >= "mds3812.mbag0_4-14.tgz")
        self.assertTrue(bn >= "mds3812.1_3.mbag0_4-14.tgz")

        self.assertFalse(bn >= "mds3812.1_3.mbag0_4-20.tgz")
        self.assertFalse(bn >= "nist3812.1_3.mbag0_4-14.tgz")
        self.assertFalse(bn >= "mds3812.2_0.mbag0_4-14.tgz")
        self.assertFalse(bn >= "mds3812.1_3.mbag1_0-14.tgz")
        self.assertFalse(bn >= "mds3812.1_3.mbag0_4-14.zip") 

    def test_sorted(self):
        names = [
            "mds3812.1_3.mbag0_4-10.tgz",
            "abc3812.1_3.mbag0_4-14.tgz", 
            "mds3812.1_3.mbag0_2-14.tgz", 
            "mds3812.2_0.mbag0_4-14.tgz",
            "nist3812.1_3.mbag0_4-14.tgz",
            "mds3812.1_3.mbag0_4-14.7z", 
            "mds3812.mbag0_4-14.tgz",  
            "mds3812.1_3.mbag1_0-14.tgz",
            "mds3812.1_3.mbag0_4-14.zip",
            "mds3812.1_3.mbag0_4-14.tgz", 
            "mds3812.1_3.mbag0_4-20.tgz" 
        ];
        expect = [
            "abc3812.1_3.mbag0_4-14.tgz", 
            "mds3812.1_3.mbag0_4-10.tgz",
            "mds3812.mbag0_4-14.tgz",  
            "mds3812.1_3.mbag0_2-14.tgz", 
            "mds3812.1_3.mbag0_4-14.7z", 
            "mds3812.1_3.mbag0_4-14.tgz", 
            "mds3812.1_3.mbag0_4-14.zip",
            "mds3812.1_3.mbag1_0-14.tgz",
            "mds3812.2_0.mbag0_4-14.tgz",
            "mds3812.1_3.mbag0_4-20.tgz", 
            "nist3812.1_3.mbag0_4-14.tgz"
        ];
        self.assertEqual(sorted(names, key=bagut.BagName), expect)


class TestBagUtils(test.TestCase):

    def test_form_bag_name(self):
        dsid = "YYZredbarchetta"
        ver = "3.4.1"
        mb = "1.0"
        seq = 3

        self.assertEqual(bagut.form_bag_name(dsid, seq, ver, mb),
                         "YYZredbarchetta.3_4_1.mbag1_0-3")
        self.assertEqual(bagut.form_bag_name(dsid, seq, ver),
                         "YYZredbarchetta.3_4_1.mbag0_4-3")
        self.assertEqual(bagut.form_bag_name(dsid, seq),
                         "YYZredbarchetta.1_0.mbag0_4-3")
        self.assertEqual(bagut.form_bag_name(dsid),
                         "YYZredbarchetta.1_0.mbag0_4-0")

        self.assertEqual(bagut.form_bag_name(dsid, seq, ver, mb,
                               "{bagseq}. {aipid} v{dsver} (MB-Prof: {mbver})"),
                         "3. YYZredbarchetta v3_4_1 (MB-Prof: 1_0)")

        # MB version 0.3
        self.assertEqual(bagut.form_bag_name03(dsid, seq, "0.2"),
                         "YYZredbarchetta.mbag0_2-3")

    def test_cmp_versions(self):
        self.assertEqual(bagut.cmp_versions("1.0.0", "1.0.2"), -1)
        self.assertEqual(bagut.cmp_versions("1.0.1", "1.0.1"),  0)
        self.assertEqual(bagut.cmp_versions("1.0.2", "1.0.1"),  1)
        self.assertEqual(bagut.cmp_versions("1.0", "1.0.2"), -1)
        self.assertEqual(bagut.cmp_versions("1.0.0", "1.0"),  1)
        self.assertEqual(bagut.cmp_versions("1", "1.0"),  -1)
        self.assertEqual(bagut.cmp_versions("1.0.2", "1.1.0"), -1)
        self.assertEqual(bagut.cmp_versions("1.2.1", "1.0.1"),  1)
        self.assertEqual(bagut.cmp_versions("1.0.2", "4.0.1"), -1)
        self.assertEqual(bagut.cmp_versions("12.0.2", "4.0.1"), 1)
    
    def test_parse_bag_name_02(self):
        parts = bagut.parse_bag_name_02("mds3812.mbag0_2-14.tgz")
        self.assertEqual(parts, ["mds3812", "", "0_2", "14", "tgz"])
        parts = bagut.parse_bag_name_02("mds3812.mbag0_2-14.tar.gz")
        self.assertEqual(parts, ["mds3812", "", "0_2", "14", "tar.gz"])
        parts = bagut.parse_bag_name_02("3812EF103.mbag2_12-100")
        self.assertEqual(parts, ["3812EF103", "", "2_12", "100", ""])

        try:
            parts = bagut.parse_bag_name_02("3812EF103.1_3_4.mbag2_12-100")
            self.fail("Thinks this is an okay 0.2 name: "+name)
        except ValueError as ex:
            self.assertIn("0.2", str(ex))

        try:
            parts = bagut.parse_bag_name_02("3812EF103.zip", "0.3")
            self.fail("Thinks this is an okay 0.3 name: "+name)
        except ValueError as ex:
            self.assertIn("0.3", str(ex))


    def test_parse_bag_name_04(self):
        parts = bagut.parse_bag_name_04("mds3812.1_3.mbag0_4-14.tgz")
        self.assertEqual(parts, ["mds3812", "1_3", "0_4", "14", "tgz"])
        parts = bagut.parse_bag_name_04("mds3812.12_3_1_0.mbag0_2-14.tar.gz")
        self.assertEqual(parts, ["mds3812", "12_3_1_0", "0_2", "14", "tar.gz"])
        parts = bagut.parse_bag_name_04("3812EF103.1.mbag2_12-100")
        self.assertEqual(parts, ["3812EF103", "1", "2_12", "100", ""])

        try:
            parts = bagut.parse_bag_name_04("3812EF103.mbag2_12-100")
            self.fail("Thinks this is an okay 0.4 name: "+name)
        except ValueError as ex:
            self.assertIn("0.4", str(ex))

        try:
            parts = bagut.parse_bag_name_04("3812EF103.zip", "1.0")
            self.fail("Thinks this is an okay 1.0 name: "+name)
        except ValueError as ex:
            self.assertIn("1.0", str(ex))

        with self.assertRaises(ValueError):
            bagut.parse_bag_name_04("3812EF103.1.2.3.mbag0_3-1.zip")
        with self.assertRaises(ValueError):
            bagut.parse_bag_name_04("3812EF103.1_2.3.mbag0_3-1.zip")
        with self.assertRaises(ValueError):
            bagut.parse_bag_name_04("3812EF103.1_2_3.mbag0.3-1.zip")
        with self.assertRaises(ValueError):
            bagut.parse_bag_name_04("3812EF103.1_2_3.mbag.0_3-1.zip")

    def test_parse_bag_name(self):
        parts = bagut.parse_bag_name("mds3812.1_3.mbag0_4-14.tgz")
        self.assertEqual(parts, ["mds3812", "1_3", "0_4", "14", "tgz"])
        parts = bagut.parse_bag_name("mds3812.12_3_1_0.mbag0_2-14.tar.gz")
        self.assertEqual(parts, ["mds3812", "12_3_1_0", "0_2", "14", "tar.gz"])
        parts = bagut.parse_bag_name("3812EF103.1.mbag2_12-100")
        self.assertEqual(parts, ["3812EF103", "1", "2_12", "100", ""])        
        
        parts = bagut.parse_bag_name("mds3812.mbag0_2-14.tgz")
        self.assertEqual(parts, ["mds3812", "", "0_2", "14", "tgz"])
        parts = bagut.parse_bag_name("mds3812.mbag0_2-14.tar.gz")
        self.assertEqual(parts, ["mds3812", "", "0_2", "14", "tar.gz"])
        parts = bagut.parse_bag_name("3812EF103.mbag2_12-100")
        self.assertEqual(parts, ["3812EF103", "", "2_12", "100", ""])
        
        with self.assertRaises(ValueError):
            bagut.parse_bag_name("3812EF103.1.2.3.mbag0_3-1.zip")
        with self.assertRaises(ValueError):
            bagut.parse_bag_name("3812EF103.1_2.3.mbag0_3-1.zip")
        with self.assertRaises(ValueError):
            bagut.parse_bag_name("3812EF103.1_2_3.mbag0.3-1.zip")
        with self.assertRaises(ValueError):
            bagut.parse_bag_name("3812EF103.1_2_3.mbag.0_3-1.zip")
        with self.assertRaises(ValueError):
            bagut.parse_bag_name("3812EF103.zip")


    def test_is_legal_bag_name(self):
        self.assertTrue(bagut.is_legal_bag_name("mds3812.1_3.mbag0_4-14.tgz"))
        self.assertTrue(bagut.is_legal_bag_name("mds3812.12_3_1_0.mbag0_2-14.tar.gz"))
        self.assertTrue(bagut.is_legal_bag_name("3812EF103.1.mbag2_12-100"))
        
        self.assertTrue(bagut.is_legal_bag_name("mds3812.mbag0_2-14.tgz"))
        self.assertTrue(bagut.is_legal_bag_name("mds3812.mbag0_2-14.tar.gz"))
        self.assertTrue(bagut.is_legal_bag_name("3812EF103.mbag2_12-100"))

        self.assertFalse(bagut.is_legal_bag_name("3812EF103.1.2.3.mbag0_3-1.zip"))
        self.assertFalse(bagut.is_legal_bag_name("3812EF103.1_2.3.mbag0_3-1.zip"))
        self.assertFalse(bagut.is_legal_bag_name("3812EF103.1_2_3.mbag0.3-1.zip"))
        self.assertFalse(bagut.is_legal_bag_name("3812EF103.1_2_3.mbag.0_3-1.zip"))
        self.assertFalse(bagut.is_legal_bag_name("3812EF103.zip"))

        # ark-id based
        self.assertTrue(bagut.is_legal_bag_name("mds3-812.1_3.mbag0_4-14"))

    def test_multibag_version_of(self):
        self.assertEqual(bagut.multibag_version_of("mds3812.1_3.mbag0_4-14.tgz"), "0.4")
        self.assertEqual(bagut.multibag_version_of("mds3812.12_3_1_0.mbag0_2-14.tar.gz"),
                         "0.2")
        self.assertEqual(bagut.multibag_version_of("3812EF103.1.mbag2_12-100"), "2.12")

        self.assertEqual(bagut.multibag_version_of("mds3812.mbag0_2-14.tgz"), "0.2")
        self.assertEqual(bagut.multibag_version_of("mds3812.mbag0_3-16.tar.gz"), "0.3")
        self.assertEqual(bagut.multibag_version_of("3812EF103.mbag2_12-100"), "2.12")

        self.assertEqual(bagut.multibag_version_of("3812EF103.1.2.3.mbag0_3-3"), "")
        self.assertEqual(bagut.multibag_version_of("3812EF103.zip"), "")


    def test_find_latest_head_bag(self):
        
        names = [
            "mds3812.1_3.mbag0_4-10.tgz",
            "mds3812.1_3.mbag0_2-8.tgz", 
            "mds3812.2_0.mbag0_4-18.tgz",
            "mds3812.1_3.mbag0_4-14.7z", 
            "mds3812.mbag0_4-4.tgz",  
            "mds3812.1_3.mbag1_0-16.tgz",
            "mds3812.1_3.mbag0_4-14.zip",
            "mds3812.1_3.mbag0_4-14.tgz", 
            "mds3812.1_4.mbag0_4-20.tgz" 
        ];
        self.assertEqual(bagut.find_latest_head_bag(names),
                         "mds3812.1_4.mbag0_4-20.tgz")
        self.assertEqual(bagut.find_latest_head_bag(names[:-1]),
                         "mds3812.2_0.mbag0_4-18.tgz")
        with self.assertRaises(ValueError):
            bagut.find_latest_head_bag([])
        with self.assertRaises(ValueError):
            bagut.find_latest_head_bag(tuple())
        with self.assertRaises(TypeError):
            bagut.find_latest_head_bag(None)

    def test_select_version(self):
        names = [
            "mds3812.1_3.mbag0_4-10.tgz",
            "mds3812.1_3.mbag0_2-8.tgz", 
            "mds3812.2_0.mbag0_4-18.tgz",
            "mds3812.1_3.mbag0_4-14.7z", 
            "mds3812.mbag0_4-4.tgz",  
            "mds3812.1_3.mbag1_0-16.tgz",
            "mds3812.1_3.mbag0_4-14.zip",
            "mds3812.1_3.mbag0_4-14.tgz", 
            "mds3812.1_4.mbag0_4-20.tgz" 
        ];

        self.assertEqual(bagut.select_version(names, "2.0"),
                         ["mds3812.2_0.mbag0_4-18.tgz"])
        self.assertEqual(bagut.select_version(names, "1.4"),
                         ["mds3812.1_4.mbag0_4-20.tgz"])
        self.assertEqual(bagut.select_version(names, "1.3"),
                         names[0:2]+names[3:4]+names[5:8])
        self.assertEqual(bagut.select_version(names, ""),
                         ["mds3812.mbag0_4-4.tgz"])
        self.assertEqual(bagut.select_version(names, "0"),
                         ["mds3812.mbag0_4-4.tgz"])
        self.assertEqual(bagut.select_version(names, "1"),
                         ["mds3812.mbag0_4-4.tgz"])

    def test_select_version_newpat(self):
        names = [
            "mds2-3812.1_3.mbag0_4-10.tgz",
            "mds2-3812.1_3.mbag0_2-8.tgz", 
            "mds2-3812.2_0.mbag0_4-18.tgz",
            "mds2-3812.1_3.mbag0_4-14.7z", 
            "mds2-3812.mbag0_4-4.tgz",  
            "mds2-3812.1_3.mbag1_0-16.tgz",
            "mds2-3812.1_3.mbag0_4-14.zip",
            "mds2-3812.1_3.mbag0_4-14.tgz", 
            "mds2-3812.1_4.mbag0_4-20.tgz" 
        ];

        self.assertEqual(bagut.select_version(names, "2.0"),
                         ["mds2-3812.2_0.mbag0_4-18.tgz"])
        self.assertEqual(bagut.select_version(names, "1.4"),
                         ["mds2-3812.1_4.mbag0_4-20.tgz"])
        self.assertEqual(bagut.select_version(names, "1.3"),
                         names[0:2]+names[3:4]+names[5:8])
        self.assertEqual(bagut.select_version(names, ""),
                         ["mds2-3812.mbag0_4-4.tgz"])
        self.assertEqual(bagut.select_version(names, "0"),
                         ["mds2-3812.mbag0_4-4.tgz"])
        self.assertEqual(bagut.select_version(names, "1"),
                         ["mds2-3812.mbag0_4-4.tgz"])

class TestNerdmUtils(test.TestCase):

    def test_schuripat(self):
        self.assertTrue(
   bagut._nrdpat.match("https://data.nist.gov/od/dm/nerdm-schema/pub/v1.0#Res") )
        self.assertTrue(
   bagut._nrdpat.match("https://data.nist.gov/od/dm/nerdm-schema/goob/v0.3") )
        self.assertTrue(
   bagut._nrdpat.match("https://data.nist.gov/od/dm/nerdm-schema/foo/bar/v0.3#"))

        self.assertFalse(
   bagut._nrdpat.match("https://www.nist.gov/od/id/nerdm-schema/blue/v0.3#"))
        self.assertFalse(
   bagut._nrdpat.match("https://data.nist.gov/od/dm/nerdm-schema/v0.3#Res"))

        pat = bagut._schuripatfor(bagut.NERDM_SCH_ID_BASE)
        self.assertTrue(
            pat.match("https://data.nist.gov/od/dm/nerdm-schema/v0.3#pub"))
        pat = bagut._schuripatfor(bagut.NERDM_SCH_ID_BASE+"pub/")
        self.assertTrue(
            pat.match("https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#pub"))
        self.assertFalse(
            pat.match("https://data.nist.gov/od/dm/nerdm-schema/goob/v0.3#pub"))
        
    def test_upd_schema_ver(self):
        defver = "1.0"
        byext = {}
        self.assertEqual(
            bagut._upd_schema_ver(
                "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#Res",
                byext, defver),
            "https://data.nist.gov/od/dm/nerdm-schema/pub/1.0#Res"
        )
        
        byext = {
            bagut._schuripatfor("http://example.com/anext/"): "v0.1",
            bagut._schuripatfor(bagut.NERDM_SCH_ID_BASE+"pub/"):   "v1.2",
            bagut._schuripatfor(bagut.NERDM_SCH_ID_BASE):          "v2.2"
        }

        self.assertEqual(
            bagut._upd_schema_ver(
                "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#Res",
                byext, defver),
            "https://data.nist.gov/od/dm/nerdm-schema/pub/v1.2#Res"
        )
        self.assertEqual(
            bagut._upd_schema_ver(
                "https://data.nist.gov/od/dm/nerdm-schema/v0.3",
                byext, defver),
            "https://data.nist.gov/od/dm/nerdm-schema/v2.2"
        )
        self.assertEqual(
            bagut._upd_schema_ver("http://example.com/anext/v88#goob",
                                  byext, defver),
            "http://example.com/anext/v0.1#goob"
        )
        self.assertEqual(
            bagut._upd_schema_ver(
                "https://data.nist.gov/od/dm/nerdm-schema/blue/v0.3#Res",
                byext, defver),
            "https://data.nist.gov/od/dm/nerdm-schema/blue/1.0#Res"
        )

    def test_upd_schema_ver_on_node(self):
        defver = "1.0"
        byext = {
            bagut._schuripatfor("http://example.com/anext/"): "v0.1",
            bagut._schuripatfor(bagut.NERDM_SCH_ID_BASE+"pub/"):   "v1.2",
            bagut._schuripatfor(bagut.NERDM_SCH_ID_BASE):          "v2.2"
        }

        data = {
            "goob": "https://data.nist.gov/od/dm/nerdm-schema/v0.3",
            "foo": [{
                "goob": [ "http://example.com/anext/v88#goob",
                          "http://goober.com/foop/v99#big" ],
                "blah": "snooze"
            }],
            "bar": {
                "hank": "aaron",
                "tex": {
                    "goob": "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#Contact",
                    "blah": "blah"
                },
                "goob": []
            }
        }

        bagut._upd_schema_ver_on_node(data, "goob", byext, "1.0")
        self.assertEqual(data['goob'], 
                         "https://data.nist.gov/od/dm/nerdm-schema/v2.2")
        self.assertEqual(data['foo'][0]['goob'], 
                         [ "http://example.com/anext/v0.1#goob",
                           "http://goober.com/foop/v99#big" ])
        self.assertEqual(data['bar']['tex']['goob'], 
                     "https://data.nist.gov/od/dm/nerdm-schema/pub/v1.2#Contact")
        self.assertEqual(data['bar']['goob'], [])

        bagut._upd_schema_ver_on_node(data, "goob", {}, "1.0")
        self.assertEqual(data['goob'], 
                         "https://data.nist.gov/od/dm/nerdm-schema/v2.2")
        self.assertEqual(data['foo'][0]['goob'], 
                         [ "http://example.com/anext/v0.1#goob",
                           "http://goober.com/foop/v99#big" ])
        self.assertEqual(data['bar']['tex']['goob'], 
                     "https://data.nist.gov/od/dm/nerdm-schema/pub/1.0#Contact")
        self.assertEqual(data['bar']['goob'], [])

    def test_update_nerdm_schema(self):
        defver = "1.0"
        byext = {
            "http://example.com/anext/": "v0.1",
            "pub":  "v1.2",
            "bib":  "v0.8",
            "":     "v2.2"
        }

        data = {
            "@id": "ark:/88888/goober.v12_3_177",
            "$schema": "https://data.nist.gov/od/dm/nerdm-schema/v0.3",
            "foo": {
                "$extensionSchemas": [ "http://example.com/anext/v88#goob",
                          "http://goober.com/foop/v99#big" ],
                "blah": "snooze"
            },
            "bar": {
                "hank": "aaron",
                "tex": {
                    "$extensionSchemas": "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#Contact",
                    "blah": "blah"
                },
                "$extensionSchemas": []
            },
            "references": [
                {
                    'location': 'https://tinyurl.com/asdf',
                    "$extensionSchemas": [
                        "https://data.nist.gov/od/dm/nerdm-schema/v0.3#/definitions/BibliographicReference",
                        "https://data.nist.gov/od/dm/nerdm-schema/v0.3#/definitions/DCiteReference"
                    ]
                }
            ]
        }

        bagut.update_nerdm_schema(data, "1.0", byext)
        self.assertEqual(data['$schema'], 
                         "https://data.nist.gov/od/dm/nerdm-schema/v2.2")
        self.assertEqual(data['@id'], "ark:/88888/goober")
        self.assertEqual(data['foo']['$extensionSchemas'], 
                         [ "http://example.com/anext/v0.1#goob",
                           "http://goober.com/foop/v99#big" ])
        self.assertEqual(data['bar']['tex']['$extensionSchemas'], 
                     "https://data.nist.gov/od/dm/nerdm-schema/pub/v1.2#Contact")
        self.assertEqual(data['bar']['$extensionSchemas'], [])
        self.assertEqual(data['references'][0]['$extensionSchemas'][0],
                         "https://data.nist.gov/od/dm/nerdm-schema/v2.2#/definitions/BibliographicReference")
        self.assertEqual(data['references'][0]['$extensionSchemas'][1],
                         "https://data.nist.gov/od/dm/nerdm-schema/bib/v0.8#/definitions/DCiteReference")
        
        data = {
            "@id": "ark:/88888/goober",
            "_schema": "https://data.nist.gov/od/dm/nerdm-schema/v0.3",
            "foo": {
                "_extensionSchemas": [ "http://example.com/anext/v88#goob",
                          "http://goober.com/foop/v99#big" ],
                "blah": "snooze"
            },
            "bar": {
                "hank": "aaron",
                "tex": {
                    "_extensionSchemas": "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#Contact",
                    "blah": "blah"
                },
                "_extensionSchemas": []
            }
        }
        bagut.update_nerdm_schema(data)
        self.assertEqual(data['_schema'], CORE_SCHEMA_URI)
        self.assertEqual(data['@id'], "ark:/88888/goober")
        self.assertEqual(data['foo']['_extensionSchemas'], 
                         [ "http://example.com/anext/v88#goob",
                           "http://goober.com/foop/v99#big" ])
        self.assertEqual(data['bar']['tex']['_extensionSchemas'], PUB_SCHEMA_URI+"#Contact")
        self.assertEqual(data['bar']['_extensionSchemas'], [])
        
    def test_update_nerdm_schema_version_history(self):
        defver = "1.0"
        data = {
            "@id": "ark:/88888/goober",
            "_schema": "https://data.nist.gov/od/dm/nerdm-schema/v0.3",
            "foo": {
                "_extensionSchemas": [ "http://example.com/anext/v88#goob",
                          "http://goober.com/foop/v99#big" ],
                "blah": "snooze"
            },
            "bar": {
                "hank": "aaron",
                "tex": {
                    "_extensionSchemas": "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.3#Contact",
                    "blah": "blah"
                },
                "_extensionSchemas": []
            },
            "versionHistory": [
                {
                    "version": "1.0",
                    "issued": "2020-10-20",
                    "location": "https://pdr.nist.gov/od/id/ark:/88888/goober",
                    "hank": "aaron"
                }
            ]
        }

        bagut.update_nerdm_schema(data)
        self.assertEqual(data['_schema'], CORE_SCHEMA_URI)
        self.assertEqual(data['@id'], "ark:/88888/goober")
        self.assertEqual(data['foo']['_extensionSchemas'], 
                         [ "http://example.com/anext/v88#goob",
                           "http://goober.com/foop/v99#big" ])
        self.assertEqual(data['bar']['tex']['_extensionSchemas'], PUB_SCHEMA_URI+"#Contact")
        self.assertEqual(data['bar']['_extensionSchemas'], [])

        self.assertIn('releaseHistory', data)
        self.assertNotIn('versionHistory', data)
        self.assertEqual(data['releaseHistory']['@id'], "ark:/88888/goober/pdr:v")
        self.assertEqual(data['releaseHistory']['@type'], ["nrdr:ReleaseHistory"])
        self.assertEqual(len(data['releaseHistory']['hasRelease']), 1)
        self.assertEqual(data['releaseHistory']['hasRelease'][0]['hank'], 'aaron')
        self.assertEqual(data['releaseHistory']['hasRelease'][0]['version'], '1.0')
        self.assertEqual(data['releaseHistory']['hasRelease'][0]['location'],
                         "https://pdr.nist.gov/od/id/ark:/88888/goober/pdr:v/1.0")
        self.assertEqual(data['releaseHistory']['hasRelease'][0]['@id'],
                         "ark:/88888/goober/pdr:v/1.0")

        data['versionHistory'] = [{
            "version": "2.0",
            "issued": "2020-10-20",
            "goob": "gurn"
        }]
        data['releaseHistory']['hasRelease'][0]['location'] = \
                         "https://pdr.nist.gov/od/id/ark:/88888/goober.v2_0"
        bagut.update_nerdm_schema(data)
        self.assertEqual(data['_schema'], CORE_SCHEMA_URI)
        self.assertEqual(data['@id'], "ark:/88888/goober")
        self.assertEqual(data['foo']['_extensionSchemas'], 
                         [ "http://example.com/anext/v88#goob",
                           "http://goober.com/foop/v99#big" ])
        self.assertEqual(data['bar']['tex']['_extensionSchemas'], PUB_SCHEMA_URI+"#Contact")
        self.assertEqual(data['bar']['_extensionSchemas'], [])

        self.assertIn('releaseHistory', data)
        self.assertIn('versionHistory', data)
        self.assertEqual(data['releaseHistory']['@id'], "ark:/88888/goober/pdr:v")
        self.assertEqual(data['releaseHistory']['@type'], ["nrdr:ReleaseHistory"])
        self.assertEqual(len(data['releaseHistory']['hasRelease']), 1)
        self.assertEqual(data['releaseHistory']['hasRelease'][0]['hank'], 'aaron')
        self.assertEqual(data['releaseHistory']['hasRelease'][0]['version'], '1.0')
        self.assertEqual(data['releaseHistory']['hasRelease'][0]['location'],
                         "https://pdr.nist.gov/od/id/ark:/88888/goober/pdr:v/1.0")

    def test_create_release_history_for(self):
        hist = bagut.create_release_history_for("goob")
        self.assertEqual(hist['@id'], "goob/pdr:v")
        self.assertEqual(hist['@type'], ["nrdr:ReleaseHistory"])
        self.assertEqual(hist['hasRelease'], [])

        self.assertEqual(bagut.create_release_history_for("goob.gurn")['@id'], "goob.gurn/pdr:v")
        self.assertEqual(bagut.create_release_history_for("goob.rel")['@id'], "goob/pdr:v")
        self.assertEqual(bagut.create_release_history_for("goob.v1")['@id'], "goob/pdr:v")
        self.assertEqual(bagut.create_release_history_for("goob.v1_2")['@id'], "goob/pdr:v")
        self.assertEqual(bagut.create_release_history_for("goob.v1.2")['@id'], "goob/pdr:v")
        self.assertEqual(bagut.create_release_history_for("goob.v1_2_3")['@id'], "goob/pdr:v")
        self.assertEqual(bagut.create_release_history_for("goob.v2_1_3_0")['@id'], "goob/pdr:v")
        
        hist = bagut.create_release_history_for("gary.v1_0_0")
        self.assertEqual(hist['@id'], "gary/pdr:v")
        self.assertEqual(hist['@type'], ["nrdr:ReleaseHistory"])
        self.assertEqual(hist['hasRelease'], [])

    def test_to_version_ext(self):
        self.assertEqual(bagut.to_version_ext("1.0"), "/pdr:v/1.0")
        self.assertEqual(bagut.to_version_ext("goob"), "/pdr:v/goob")

    def test_update_release_ref(self):
        ref = { "issued": "never" }
        with self.assertRaises(ValueError):
            bagut.update_release_ref([])
        with self.assertRaises(ValueError):
            bagut.update_release_ref(ref)

        ref['version'] = "2.1.9"
        bagut.update_release_ref(ref)
        self.assertEqual(ref, { "issued": "never", "version": "2.1.9" })

        bagut.update_release_ref(ref, "ark:/88888/goob")
        self.assertEqual(ref, { "issued": "never", "version": "2.1.9", "@id": "ark:/88888/goob/pdr:v/2.1.9"})

        ref['@id'] = "ark:/88888/gurn"
        bagut.update_release_ref(ref)
        self.assertEqual(ref, { "issued": "never", "version": "2.1.9", "@id": "ark:/88888/gurn/pdr:v/2.1.9"})

        ref['@id'] = "ark:/88888/fred.v2_1_9"
        bagut.update_release_ref(ref)
        self.assertEqual(ref, { "issued": "never", "version": "2.1.9", "@id": "ark:/88888/fred/pdr:v/2.1.9"})

        bagut.update_release_ref(ref, "asdfxkcd", "https://example.com/id/")
        self.assertEqual(ref, { "issued": "never", "version": "2.1.9", "@id": "asdfxkcd/pdr:v/2.1.9",
                                "location": "https://example.com/id/asdfxkcd/pdr:v/2.1.9"})

        ref['@id'] = "ark:/88888/fred.v2_1_9"
        bagut.update_release_ref(ref)
        self.assertEqual(ref, { "issued": "never", "version": "2.1.9", "@id": "ark:/88888/fred/pdr:v/2.1.9",
                                "location": "https://example.com/id/ark:/88888/fred/pdr:v/2.1.9"})

        ref['@id'] = "ark:/88888/mds2-8888.v2_1_9"
        ref['location'] = "https://data.nist.gov/od/id/ark:/88888/mds2-8888.v2_1_9"
        bagut.update_release_ref(ref)
        self.assertEqual(ref, { "issued": "never", "version": "2.1.9",
                                "@id": "ark:/88888/mds2-8888/pdr:v/2.1.9",
                                "location": "https://data.nist.gov/od/id/ark:/88888/mds2-8888/pdr:v/2.1.9"})
        
        
                    
                         
if __name__ == '__main__':
    test.main()
