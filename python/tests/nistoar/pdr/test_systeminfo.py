import os, pdb
import warnings as warn
import unittest as test

import nistoar.pdr as pdr

class MySystemInfo(pdr.SystemInfoMixin):
    @property
    def system_version(self):
        return super(MySystemInfo, self).system_version

class TestSystemInfo(test.TestCase):

    def test_version(self):
        si = MySystemInfo()
        self.assertNotEqual(si.system_version, "dev")
        self.assertGreater(len(si.system_version), 1)

    def test_sysname(self):
        si = MySystemInfo()
        self.assertEqual(si.system_name, "")

    def test_subsysname(self):
        si = MySystemInfo()
        self.assertEqual(si.subsystem_name, "")

    def test_sysabbrev(self):
        si = MySystemInfo()
        self.assertEqual(si.system_abbrev, "")

    def test_subsysabbrev(self):
        si = MySystemInfo()
        self.assertEqual(si.subsystem_abbrev, "")

class TestPDRSystem(test.TestCase):

    def test_version(self):
        si = pdr.PDRSystem()
        self.assertNotEqual(si.system_version, "dev")
        self.assertGreater(len(si.system_version), 1)

    def test_sysname(self):
        si = pdr.PDRSystem()
        self.assertEqual(si.system_name, "Public Data Repository")

    def test_subsysname(self):
        si = pdr.PDRSystem()
        self.assertEqual(si.subsystem_name, "Public Data Repository")

    def test_sysabbrev(self):
        si = pdr.PDRSystem()
        self.assertEqual(si.system_abbrev, "PDR")

    def test_subsysabbrev(self):
        si = pdr.PDRSystem()
        self.assertEqual(si.subsystem_abbrev, "PDR")




if __name__ == '__main__':
    test.main()
    
