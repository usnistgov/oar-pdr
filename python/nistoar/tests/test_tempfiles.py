import os, pdb, shutil
import warnings as warn
import unittest as test

from nistoar.tests import tmpdir, ensure_tmpdir, rmtmpdir, rmdir, Tempfiles

class TestFunctions(test.TestCase):

    def test_tmpdir(self):
        td = tmpdir()
        self.assertEqual(os.path.dirname(td), os.getcwd())
        self.assertRegexpMatches(os.path.basename(td), r"^_test.\d+$")

        td = tmpdir("/tmp")
        self.assertEqual(os.path.dirname(td), "/tmp")
        self.assertRegexpMatches(os.path.basename(td), r"^_test.\d+$")

        td = tmpdir(dirname="_goob")
        self.assertEqual(os.path.dirname(td), os.getcwd())
        self.assertEqual(os.path.basename(td), "_goob")

        td = tmpdir("/tmp", "_goob")
        self.assertEqual(os.path.dirname(td), "/tmp")
        self.assertEqual(os.path.basename(td), "_goob")

    def test_ensure_dir(self):
        tdir = tmpdir()
        base = os.path.basename(tdir)

        td = ensure_tmpdir()
        self.assertEquals(td, tdir)
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        self.assertEqual(os.path.dirname(td), os.getcwd())
        self.assertRegexpMatches(os.path.basename(tdir), r"^_test.\d+$")
        shutil.rmtree(td)
        assert not os.path.exists(td)

        td = ensure_tmpdir("/tmp")
        self.assertEquals(td, os.path.join("/tmp", base))
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        self.assertEqual(os.path.dirname(td), "/tmp")
        self.assertRegexpMatches(os.path.basename(td), r"^_test.\d+$")
        shutil.rmtree(td)
        assert not os.path.exists(td)

        td = ensure_tmpdir(dirname="_goob")
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        self.assertEqual(os.path.dirname(td), os.getcwd())
        self.assertEqual(os.path.basename(td), "_goob")
        shutil.rmtree(td)
        assert not os.path.exists(td)

        td = ensure_tmpdir("/tmp", "_goob")
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        self.assertEqual(os.path.dirname(td), "/tmp")
        self.assertEqual(os.path.basename(td), "_goob")
        shutil.rmtree(td)
        assert not os.path.exists(td)
        
    def test_rmdir(self):
        td = ensure_tmpdir()
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        f = os.path.join(td, "junk.txt")
        with open(f, 'w') as fd:
            fd.write("Hello world!\n")
        self.assertTrue(os.path.exists(f))

        rmdir(td)
        self.assertFalse(os.path.exists(f))
        self.assertFalse(os.path.exists(td))

    def test_rmtmpdir(self):
        td = ensure_tmpdir()
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        f = os.path.join(td, "junk.txt")
        with open(f, 'w') as fd:
            fd.write("Hello world!\n")
        self.assertTrue(os.path.exists(f))

        rmtmpdir()
        self.assertFalse(os.path.exists(f))
        self.assertFalse(os.path.exists(td))

        td = ensure_tmpdir("/tmp", "_goob")
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        self.assertEqual(os.path.dirname(td), "/tmp")
        self.assertEqual(os.path.basename(td), "_goob")
        f = os.path.join(td, "junk.txt")
        with open(f, 'w') as fd:
            fd.write("Hello world!\n")
        self.assertTrue(os.path.exists(f))

        rmtmpdir("/tmp", "_goob")
        self.assertFalse(os.path.exists(f))
        self.assertFalse(os.path.exists(td))

class TestTempfiles(test.TestCase):

    def tearDown(self):
        tempdir = tmpdir()
        if os.path.exists(tempdir):
            shutil.rmtree(tempdir)

    def test_ctor(self):
        tf = Tempfiles()
        self.assertEqual(tf.root, tmpdir())
        self.assertTrue(os.path.exists(tf.root))
        self.assertFalse(tf._autoclean)
        self.assertEqual(len(tf._files), 0)

    def test_path(self):
        tf = Tempfiles()
        path = tf("goob")
        self.assertEqual(path, os.path.join(tf.root, "goob"))
        self.assertTrue(os.path.exists(tf.root))
        self.assertFalse(os.path.exists(path))

    def test_mkdir(self):
        tf = Tempfiles()
        path = tf.mkdir("goob")
        self.assertEqual(path, os.path.join(tf.root, "goob"))
        self.assertTrue(os.path.exists(tf.root))
        self.assertTrue(os.path.exists(path))

    def test_clean(self):
        tf = Tempfiles()
        dir = tf.mkdir("goob")
        self.assertTrue(os.path.exists(dir))
        f = tf.track("goob/junk.txt")
        self.assertEqual(f, os.path.join(dir, "junk.txt"))
        with open(f, 'w') as fd:
            fd.write("Hello world!\n")
        self.assertTrue(os.path.exists(f))

        tf.clean()
        self.assertFalse(os.path.exists(f))
        self.assertFalse(os.path.exists(dir))
        
        self.assertTrue(os.path.exists(tf.root))


if __name__ == '__main__':
    test.main()
    
