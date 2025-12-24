import os, sys, pdb, shutil, json, tempfile
import unittest as test

from curate.cmds import merge_coll_md as cmd

from nistoar.pdr.utils import read_nerd

exedir  = os.path.dirname(__file__)
datadir = os.path.join(os.path.dirname(exedir), 'data')

tmpdir = None
def setUpModule():
    global tmpdir
    tmpdir = tempfile.mkdtemp(prefix="_testcmd_")

def tearDownModule():
    global tmpdir
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)

class TestMergeCollMD(test.TestCase):

    def test_base_schema(self):
        self.assertEqual(cmd.base_schema("https://goober.net/"), "https://goober.net/")
        self.assertEqual(cmd.base_schema("https://goober.net/gurn/v2.3"),
                         "https://goober.net/gurn/")

    def test_merge_coll_md(self):
        mergedf = os.path.join(tmpdir, "original.json")
        updatedf = os.path.join(datadir, "updated.json")
        shutil.copyfile(os.path.join(datadir, "original.json"), mergedf)

        onerd = read_nerd(mergedf)
        self.assertNotIn("isPartOf", onerd)
        self.assertEqual(len(onerd['topic']), 2)
        unerd = read_nerd(updatedf)
        self.assertTrue(unerd.get("isPartOf"))
        self.assertEqual(len(unerd['topic']), 4)

        cmd.merge_coll_md(updatedf, "forensics", outf=mergedf)

        mnerd = read_nerd(updatedf)
        self.assertEqual(mnerd.get('isPartOf'), unerd['isPartOf'])
        self.assertEqual(len(mnerd.get('topic',[])), 4)
        self.assertEqual(len(set([t['tag'] for t in mnerd['topic']])), 4)

        
        
                        
        
                    
                         
if __name__ == '__main__':
    test.main()
