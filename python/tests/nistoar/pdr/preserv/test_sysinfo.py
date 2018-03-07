import os, pdb
import warnings as warn
import unittest as test

import nistoar.pdr.preserv as pres

class TestPreservationSystem(test.TestCase):

    def test_version(self):
        si = pres.PreservationSystem()
        self.assertNotEqual(si.system_version, "dev")
        self.assertGreater(len(si.system_version), 1)

    def test_sysname(self):
        si = pres.PreservationSystem()
        self.assertEqual(si.system_name, "Public Data Repository")

    def test_subsysname(self):
        si = pres.PreservationSystem()
        self.assertEqual(si.subsystem_name, "Preservation")

    def test_sysabbrev(self):
        si = pres.PreservationSystem()
        self.assertEqual(si.system_abbrev, "PDR")

    def test_subsysabbrev(self):
        si = pres.PreservationSystem()
        self.assertEqual(si.subsystem_abbrev, "Preservation")




if __name__ == '__main__':
    test.main()
    
