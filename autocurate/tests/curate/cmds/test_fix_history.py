import os, sys, pdb, shutil, json, tempfile
import unittest as test
from copy import deepcopy

from curate.cmds import fix_history as cmd

from nistoar.pdr.utils import read_nerd
from nistoar.pdr.preserv.bagit.bag import NISTBag

exedir  = os.path.dirname(os.path.abspath(__file__))
datadir = os.path.join(os.path.dirname(exedir), 'data')
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(exedir))))
bagsrc  = os.path.join(basedir, "python/tests/nistoar/pdr/preserv/data")
testbag = os.path.join(bagsrc, "metadatabag")

tmpdir = None
def setUpModule():
    global tmpdir
    tmpdir = tempfile.mkdtemp(prefix="_testcmd_")

def tearDownModule():
    global tmpdir
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)

class TestFixHistory(test.TestCase):

    def test_hist_not_up_to_date(self):
        self.assertTrue(cmd.hist_not_up_to_date(None))
        self.assertTrue(cmd.hist_not_up_to_date({}))
        self.assertTrue(cmd.hist_not_up_to_date({"@id": "ark:/88434/goob/pdr:v"}))

        rh = {
            "@id": "ark:/88434/goob/pdr:v",
            "hasRelease": [
                { "@id": "ark:/88434/goob/pdr:v/1.0.0" }
            ]
        }
        self.assertTrue(not cmd.hist_not_up_to_date(rh))
        rh['hasRelease'][0]['@id'] = "ark:/88434/goob.v1_0_0"
        rh['hasRelease'].append({ "@id": "ark:/88434/goob/pdr:v/1.0.1" })
        self.assertTrue(cmd.hist_not_up_to_date(rh))
        rh['hasRelease'][0]['@id'] = "ark:/88434/goob/pdr:v/1.0.0"
        rh['@id'] = "ark:/88434/goob.rel"
        self.assertTrue(cmd.hist_not_up_to_date(rh))

    def test_ensure_relhist_id(self):
        hist = {}
        cmd.ensure_relhist_id(hist, "ark:/88434/goob")
        self.assertEqual(hist.get('@id'), "ark:/88434/goob/pdr:v")

        hist['@id'] = os.path.dirname(hist['@id']) + ".rel"
        cmd.ensure_relhist_id(hist, "ark:/88434/goob")
        self.assertEqual(hist.get('@id'), "ark:/88434/goob/pdr:v")

    def test_fix_release_ref(self):
        id = "ark:/88434/gurn"
        with self.assertRaises(RuntimeError):
            cmd.fix_release_ref({}, id)

        hist = { "version": "1.0.1" }
        cmd.fix_release_ref(hist, id)
        self.assertEqual(hist.get('@id'), id+"/pdr:v/1.0.1")
        self.assertEqual(hist.get('location'), "https://data.nist.gov/od/id/"+id+"/pdr:v/1.0.1")

        del hist['location']
        cmd.fix_release_ref(hist, id)
        self.assertEqual(hist.get('@id'), id+"/pdr:v/1.0.1")
        self.assertEqual(hist.get('location'), "https://data.nist.gov/od/id/"+id+"/pdr:v/1.0.1")

        hist["@id"] = id
        hist["location"] = "https://data.nist.gov/od/id/"+id
        cmd.fix_release_ref(hist, id)
        self.assertEqual(hist.get('@id'), id+"/pdr:v/1.0.1")
        self.assertEqual(hist.get('location'), "https://data.nist.gov/od/id/"+id+"/pdr:v/1.0.1")

    def test_fix_release_history(self):
        src = {
            "version": "1.0.1+ (edit)",
            "versionHistory": [
                {
                    "version": "1.0.0",
                    "issued": "2024-09-25",
                    "@id": "ark:/88434/mds2-3402",
                    "location": "https://data.nist.gov/od/id/ark:/88434/mds2-3402",
                    "description": "initial version"
                }
            ],
            "releaseHistory": {
                "@id": "ark:/88434/mds2-3402.rel",
                "@type": [
                    "nrdr:ReleaseHistory"
                ],
                "hasRelease": [
                    {
                        "version": "1.0.0",
                        "issued": "2024-09-25",
                        "@id": "ark:/88434/mds2-3402/pdr:v/1.0.0",
                        "location": "https://data.nist.gov/od/id/ark:/88434/mds2-3402/pdr:v/1.0.0",
                        "description": "initial version"
                    },
                    {
                        "version": "1.0.1",
                        "issued": "2024-07-09 00:00:00",
                        "@id": "ark:/88434/mds2-3402/pdr:v/1.0.1",
                        "location": "https://data.nist.gov/od/id/ark:/88434/mds2-3402/pdr:v/1.0.1",
                        "description": "metadata update"
                    }
                ]
            }
        }
        id = "ark:/88434/mds2-3402"

        annot = deepcopy(src)
        cmd.fix_release_history(annot, id)
        self.assertNotIn('versionHistory', annot)
        self.assertEqual(annot.get('releaseHistory',{}).get('@id'), id+"/pdr:v")
        self.assertEqual(len(annot['releaseHistory'].get('hasRelease',[])), 2)
        ref = annot['releaseHistory'].get('hasRelease',[])[-1]
        self.assertEqual(ref.get('version'), "1.0.1")
        self.assertTrue(ref.get('@id').endswith("/pdr:v/1.0.1"))
        self.assertTrue(ref.get('location').endswith("/pdr:v/1.0.1"))
        ref = annot['releaseHistory'].get('hasRelease',[])[0]
        self.assertEqual(ref.get('version'), "1.0.0")
        self.assertTrue(ref.get('@id').endswith("/pdr:v/1.0.0"))
        self.assertTrue(ref.get('location').endswith("/pdr:v/1.0.0"))

        annot = deepcopy(src)
        annot['releaseHistory']['hasRelease'].pop(0)
        self.assertEqual(len(annot['releaseHistory'].get('hasRelease',[])), 1)
        cmd.fix_release_history(annot, id)
        self.assertNotIn('versionHistory', annot)
        self.assertEqual(annot.get('releaseHistory',{}).get('@id'), id+"/pdr:v")
        self.assertEqual(len(annot['releaseHistory'].get('hasRelease',[])), 2)
        ref = annot['releaseHistory'].get('hasRelease',[])[-1]
        self.assertEqual(ref.get('version'), "1.0.1")
        self.assertTrue(ref.get('@id').endswith("/pdr:v/1.0.1"))
        self.assertTrue(ref.get('location').endswith("/pdr:v/1.0.1"))
        ref = annot['releaseHistory'].get('hasRelease',[])[0]
        self.assertEqual(ref.get('version'), "1.0.0")
        self.assertTrue(ref.get('@id').endswith("/pdr:v/1.0.0"))
        self.assertTrue(ref.get('location').endswith("/pdr:v/1.0.0"))

        annot = deepcopy(src)
        del annot['releaseHistory']
        cmd.fix_release_history(annot, id)
        self.assertNotIn('versionHistory', annot)
        self.assertEqual(annot.get('releaseHistory',{}).get('@id'), id+"/pdr:v")
        self.assertEqual(len(annot['releaseHistory'].get('hasRelease',[])), 1)
        ref = annot['releaseHistory'].get('hasRelease',[])[0]
        self.assertEqual(ref.get('version'), "1.0.0")
        self.assertTrue(ref.get('@id').endswith("/pdr:v/1.0.0"))
        self.assertTrue(ref.get('location').endswith("/pdr:v/1.0.0"))

        annot = { "version": "1.0.0+ (edit)", "annotated": "2025-12-04T20:21:52" }
        cmd.fix_release_history(annot, id)
        self.assertNotIn('versionHistory', annot)
        self.assertEqual(annot.get('releaseHistory',{}).get('@id'), id+"/pdr:v")
        self.assertEqual(len(annot['releaseHistory'].get('hasRelease',[])), 1)
        ref = annot['releaseHistory'].get('hasRelease',[])[0]
        self.assertEqual(ref.get('version'), "1.0.0")
        self.assertEqual(ref.get('issued'), "2025-12-04T20:21:52")
        self.assertTrue(ref.get('@id').endswith("/pdr:v/1.0.0"))
        self.assertTrue(ref.get('location').endswith("/pdr:v/1.0.0"))

    def setUp(self):
        self.aipid = "mds00hw91v"
        self.testbag = os.path.join(tmpdir, self.aipid)

    def tearUp(self):
        if os.path.isdir(self.testbag):
            shutil.rmtree(self.testbag)

    def test_apply_fix(self):
        shutil.copytree(testbag, self.testbag)
        bag = NISTBag(self.testbag)
        id = bag.nerd_metadata_for("").get('@id')
        self.assertIn(self.aipid, id)
        annot = bag.annotations_metadata_for("")
        self.assertNotIn("releaseHistory", annot)
        self.assertNotIn("versionHistory", annot)

        cmd.apply_fix(self.testbag)
        annot = bag.annotations_metadata_for("")
        self.assertIn("releaseHistory", annot)
        self.assertNotIn("versionHistory", annot)
        self.assertEqual(annot['releaseHistory'].get('@id'), id+"/pdr:v")
        self.assertEqual(len(annot['releaseHistory'].get('hasRelease', [])), 1)
        self.assertEqual(annot['releaseHistory']['hasRelease'][0].get('@id'), id+"/pdr:v/1.0.0")

        
        

                         
if __name__ == '__main__':
    test.main()
