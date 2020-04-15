import os, sys, pdb, json, subprocess, threading, time
import unittest as test

from nistoar.testing import *
import nistoar.pdr.utils as utils

testdir = os.path.dirname(os.path.abspath(__file__))
testdatadir = os.path.join(testdir, 'data')
testdatadir3 = os.path.join(testdir, 'preserv', 'data')
testdatadir2 = os.path.join(testdatadir3, 'simplesip')

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

class TestMeausreDirSize(test.TestCase):
    def test_measure1(self):
        vals = utils.measure_dir_size(testdatadir)
        self.assertEqual(vals[1], 4)
        self.assertEqual(vals[0], 1405)

    def test_measure2(self):
        vals = utils.measure_dir_size(testdatadir2)
        self.assertEqual(vals[1], 5)
        self.assertEqual(vals[0], 9272)

class TestRmtree(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()

    def tearDown(self):
        self.tf.clean()

    def touch(self, parent, files):
        if not isinstance(files, (list, tuple)):
            files = [ files ]
        if isinstance(parent, (list, tuple)):
            parent = os.path.join(*parent)

        for f in files:
            with open(os.path.join(parent, f), 'w') as fd:
                fd.write("goober!")

    def test_rmtree(self):
        root = self.tf.mkdir("root")
        os.makedirs(os.path.join(root, "one/two/three"))
        os.makedirs(os.path.join(root, "one/four"))
        self.touch([root, "one/four"], "foo bar chew".split())
        self.touch([root, "one"], "hank snow".split())

        self.assertTrue(os.path.exists(os.path.join(root, "one/two/three")))
        self.assertTrue(os.path.exists(os.path.join(root, "one/four/chew")))

        top = os.path.join(root,"one")
        self.assertTrue(os.path.exists(root))
        self.assertTrue(os.path.exists(top))
        utils.rmtree(top)
        self.assertTrue(os.path.exists(root))
        self.assertFalse(os.path.exists(top))

    def test_rmmtdir(self):
        root = self.tf.mkdir("root")
        top = os.path.join(root,"one")
        os.mkdir(top)
        self.assertTrue(os.path.exists(root))
        self.assertTrue(os.path.exists(top))
        utils.rmtree(top)
        self.assertTrue(os.path.exists(root))
        self.assertFalse(os.path.exists(top))

    def test_rmfile(self):
        root = self.tf.mkdir("root")
        self.touch(root, "one")

        top = os.path.join(root, "one")
        self.assertTrue(os.path.exists(root))
        self.assertTrue(os.path.exists(top))
        utils.rmtree(top)
        self.assertTrue(os.path.exists(root))
        self.assertFalse(os.path.exists(top))


class TestLockedFile(test.TestCase):

    class OtherThread(threading.Thread):
        def __init__(self, func, pause=0.05):
            threading.Thread.__init__(self)
            self.f = func
            self.pause = pause
        def run(self):
            if self.f:
                time.sleep(self.pause)
                self.f('o')

    def lockedop(self, who, mode='r', sleep=0.5):
        with utils.LockedFile(self.lfile, mode) as lockdfile:
            self.rfd.write(who+'a')
            time.sleep(sleep)
            self.rfd.write(who+'r')
    
    def setUp(self):
        self.tf = Tempfiles()
        self.lfile = self.tf("test.txt")
        self.rfile = self.tf("result.txt")
        self.rfd = None

    def tearDown(self):
        self.tf.clean()

    def test_shared_reads(self):
        def f(who):
            self.lockedop(who, 'r')
        t = self.OtherThread(f)
        with open(self.rfile,'w') as self.rfd:
            t.start()
            f('t')
            t.join()
        with open(self.rfile) as self.rfd:
            data = self.rfd.read()

        self.assertEqual(data, "taoatror")
            
    def test_exclusive_writes1(self):
        def f(who):
            self.lockedop(who, 'w')
        t = self.OtherThread(f)
        with open(self.rfile,'w') as self.rfd:
            t.start()
            f('t')
            t.join()
        with open(self.rfile) as self.rfd:
            data = self.rfd.read()

        self.assertEqual(data, "tatroaor")
            
    def test_exclusive_writes2(self):
        def f(who):
            self.lockedop(who, 'w')
        t = self.OtherThread(f)
        with open(self.rfile,'w') as self.rfd:
            t.start()
            self.lockedop('t', 'r')
            t.join()
        with open(self.rfile) as self.rfd:
            data = self.rfd.read()

        self.assertEqual(data, "tatroaor")
            
    def test_exclusive_writes3(self):
        def f(who):
            self.lockedop(who, 'r')
        t = self.OtherThread(f)
        with open(self.rfile,'w') as self.rfd:
            t.start()
            self.lockedop('t', 'w')
            t.join()
        with open(self.rfile) as self.rfd:
            data = self.rfd.read()

        self.assertEqual(data, "tatroaor")

class TestJsonIO(test.TestCase):
    # this class focuses on testing the locking of JSON file IO
    
    testdata = os.path.join(testdatadir3,
                            "3A1EE2F169DD3B8CE0531A570681DB5D1491.json")

    def setUp(self):
        self.tf = Tempfiles()
        self.jfile = self.tf("data.json")

    def tearDown(self):
        self.tf.clean()

    class OtherThread(threading.Thread):
        def __init__(self, func, pause=0.05):
            threading.Thread.__init__(self)
            self.f = func
            self.pause = pause
        def run(self):
            if self.f:
                time.sleep(self.pause)
                self.f()

    def write_test_data(self):
        with open(self.testdata) as fd:
            data = json.load(fd)

    def test_writes(self):
        # this is not a definitive test that the use of LockedFile is working
        data = utils.read_json(self.testdata)
        data['foo'] = 'bar'
        def f():
            utils.write_json(data, self.jfile)
        t = self.OtherThread(f)

        data2 = dict(data)
        data2['foo'] = 'BAR'
        
        t.start()
        utils.write_json(data2, self.jfile)
        t.join()

        # success in these two lines indicate that the file was not corrupted
        data = utils.read_json(self.jfile)
        self.assertIn('@id', data)

        # success in this test indicates that writing happened in the expected
        # order; failure means that the test function is not test what we
        # exected.
        self.assertEqual(data['foo'], 'bar')

    def test_readwrite(self):
        # this is not a definitive test that the use of LockedFile is working
        data = utils.read_json(self.testdata)
        with open(self.jfile,'w') as fd:
            json.dump(data, fd)
        data['foo'] = 'bar'
        def f():
            utils.write_json(data, self.jfile)
        t = self.OtherThread(f)
        
        t.start()
        td = utils.read_json(self.jfile)
        t.join()

        self.assertIn('@id', td)
        self.assertNotIn('foo', td)
        td = utils.read_json(self.jfile)
        self.assertIn('@id', td)
        self.assertEqual(td['foo'], 'bar')

    def test_writeread(self):
        # this is not a definitive test that the use of LockedFile is working
        data = utils.read_json(self.testdata)
        with open(self.jfile,'w') as fd:
            json.dump(data, fd)
        data['foo'] = 'bar'
        self.td = None
        def f():
            self.td = utils.read_json(self.jfile)
        t = self.OtherThread(f)
        
        t.start()
        utils.write_json(data, self.jfile)
        t.join()

        self.assertIn('@id', self.td)
        self.assertEqual(self.td['foo'], 'bar')

    


if __name__ == '__main__':
    test.main()
