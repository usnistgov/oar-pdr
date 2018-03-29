import os, sys, pdb, json, subprocess
import unittest as test

import nistoar.pdr.utils as utils

testdir = os.path.dirname(os.path.abspath(__file__))
testdatadir = os.path.join(testdir, 'data')
testdatadir2 = os.path.join(testdir, 'preserv', 'data', 'simplesip')

class TestMimeTypeLoading(test.TestCase):

    def test_defaults(self):

        self.assertEquals(utils.def_ext2mime['json'], "application/json")
        self.assertEquals(utils.def_ext2mime['txt'], "text/plain")
        self.assertEquals(utils.def_ext2mime['xml'], "text/xml")

    def test_update_mimetypes_from_file(self):
        map = utils.update_mimetypes_from_file(None,
                                  os.path.join(testdatadir, "nginx-mime.types"))
        self.assertEquals(map['mml'], "text/mathml")
        self.assertEquals(map['jpg'], "image/jpeg")
        self.assertEquals(map['jpeg'], "image/jpeg")

        map = utils.update_mimetypes_from_file(map,
                                  os.path.join(testdatadir, "comm-mime.types"))
        self.assertEquals(map['zip'], "application/zip")
        self.assertEquals(map['xml'], "application/xml")
        self.assertEquals(map['xsd'], "application/xml")
        self.assertEquals(map['mml'], "text/mathml")
        self.assertEquals(map['jpg'], "image/jpeg")
        self.assertEquals(map['jpeg'], "image/jpeg")

    def test_build_mime_type_map(self):
        map = utils.build_mime_type_map([])
        self.assertEquals(map['txt'], "text/plain")
        self.assertEquals(map['xml'], "text/xml")
        self.assertEquals(map['json'], "application/json")
        self.assertNotIn('mml', map)
        self.assertNotIn('xsd', map)
        
        map = utils.build_mime_type_map(
            [os.path.join(testdatadir, "nginx-mime.types"),
             os.path.join(testdatadir, "comm-mime.types")])
        self.assertEquals(map['txt'], "text/plain")
        self.assertEquals(map['mml'], "text/mathml")
        self.assertEquals(map['xml'], "application/xml")
        self.assertEquals(map['xsd'], "application/xml")

class TestChecksum(test.TestCase):

    def test_checksum_of(self):
        dfile = os.path.join(testdatadir2,"trial1.json")
        self.assertEqual(utils.checksum_of(dfile), self.syssum(dfile))
        dfile = os.path.join(testdatadir2,"trial2.json")
        self.assertEqual(utils.checksum_of(dfile), self.syssum(dfile))
        dfile = os.path.join(testdatadir2,"trial3/trial3a.json")
        self.assertEqual(utils.checksum_of(dfile), self.syssum(dfile))

    def syssum(self, filepath):
        cmd = ["sha256sum", filepath]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        (out, err) = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(err + "\nFailed sha256sum command: " +
                               " ".join(cmd))
        return out.split()[0]




if __name__ == '__main__':
    test.main()
