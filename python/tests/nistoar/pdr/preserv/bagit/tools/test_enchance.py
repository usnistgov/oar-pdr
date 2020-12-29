import os, sys, pdb, shutil, logging, json, re
from collections import OrderedDict
import unittest as test

from nistoar.testing import *
import nistoar.pdr.preserv.bagit.builder as bldr
import nistoar.pdr.preserv.bagit.tools.enhance as tools
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.utils import read_nerd

# datadir = tests/nistoar/pdr/preserv/data
datadir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data"
)

loghdlr = None
rootlog = logging.getLogger()
def setUpModule():
    global loghdlr
    global rootlog
    ensure_tmpdir()
#    logging.basicConfig(filename=os.path.join(tmpdir(),"test_builder.log"),
#                        level=logging.INFO)
#    rootlog = logging.getLogger()
    loghdlr = logging.FileHandler(os.path.join(tmpdir(),"test_builder.log"))
    loghdlr.setLevel(logging.DEBUG)
    loghdlr.setFormatter(logging.Formatter(bldr.DEF_BAGLOG_FORMAT))
    rootlog.addHandler(loghdlr)
    rootlog.setLevel(logging.DEBUG)
    rootlog.info("configured logging for test")

def tearDownModule():
    global loghdlr
    if loghdlr:
        if rootlog:
            rootlog.removeHandler(loghdlr)
        loghdlr = None
    rmtmpdir()

rescfg = {
    "app_name": "NIST Open Access for Research: oar-pdr",
    "app_version": "testing",
    "app_url": "http://github.com/usnistgov/oar-pdr/",
    "email": "datasupport@nist.gov"
}

class TestAuthorFetcher(test.TestCase):

    testbag = os.path.join(datadir, "samplembag")

    def setUp(self):
        self.tf = Tempfiles()
        self.cfg = {
        }
 
        shutil.copytree(self.testbag, os.path.join(self.tf.root,"testbag"))
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        self.tf.track("testbag")

        # for some reason, this dataset's DOI is not working properly
        self.bag.update_metadata_for('', {'doi': "doi:10.18434/M3M956"});

    def tearDown(self):
        self.bag._unset_logfile()
        self.bag = None
        self.tf.clean()

    def test_ctor(self):
        enh = tools.AuthorFetcher()
        self.assertIsNotNone(enh.cfg)
        self.assertIsNotNone(enh.doir)

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_fetch_authors(self):
        enh = tools.AuthorFetcher(rescfg)

        md = self.bag.bag.nerd_metadata_for('', True)
        # self.assertNotIn('authors', md)
        self.assertIn('doi', md)

        auths = enh.fetch_authors(md)
        self.assertTrue(isinstance(auths, list))
        self.assertTrue(len(auths) > 0)
        self.assertEqual(auths[0]['familyName'], 'Levine')
        self.assertEqual(len(auths), 4)
        
    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_update_authors(self):
        enh = tools.AuthorFetcher(rescfg)

        md = self.bag.bag.nerd_metadata_for('', True)
        self.assertNotIn('authors', md)
        self.assertIn('doi', md)

        self.assertTrue(enh.update_authors(self.bag))

        md = self.bag.bag.nerd_metadata_for('', True)
        self.assertIn('authors', md)
        md = self.bag.bag.annotations_metadata_for('')
        self.assertNotIn('authors', md)
        md = self.bag.bag.nerd_metadata_for('', False)
        self.assertIn('authors', md)

        auths = md['authors']
        self.assertTrue(len(auths) > 0)
        self.assertEqual(auths[0]['familyName'], 'Levine')
        self.assertEqual(len(auths), 4)
        
    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_update_authors_as_annot(self):
        enh = tools.AuthorFetcher(rescfg)

        md = self.bag.bag.nerd_metadata_for('', True)
        self.assertNotIn('authors', md)
        self.assertIn('doi', md)

        self.assertTrue(enh.update_authors(self.bag, True))

        md = self.bag.bag.nerd_metadata_for('', False)
        self.assertNotIn('authors', md)
        md = self.bag.bag.annotations_metadata_for('')
        self.assertIn('authors', md)
        md = self.bag.bag.nerd_metadata_for('', True)
        self.assertIn('authors', md)

        auths = md['authors']
        self.assertTrue(len(auths) > 0)
        self.assertEqual(auths[0]['familyName'], 'Levine')
        self.assertEqual(len(auths), 4)

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_func_update_authors(self):
        md = self.bag.bag.nerd_metadata_for('', True)
        self.assertNotIn('authors', md)
        self.assertIn('doi', md)

        self.assertTrue(tools.update_authors(self.bag, True, rescfg))

        md = self.bag.bag.nerd_metadata_for('', False)
        self.assertNotIn('authors', md)
        md = self.bag.bag.annotations_metadata_for('')
        self.assertIn('authors', md)
        md = self.bag.bag.nerd_metadata_for('', True)
        self.assertIn('authors', md)

        auths = md['authors']
        self.assertTrue(len(auths) > 0)
        self.assertEqual(auths[0]['familyName'], 'Levine')
        self.assertEqual(len(auths), 4)



class TestEnrichReferences(test.TestCase):

    testbag = os.path.join(datadir, "samplembag")
    log = rootlog.getChild('TestEnrichReferences')

    def setUp(self):
        self.tf = Tempfiles()
        self.cfg = {
        }
 
        shutil.copytree(self.testbag, os.path.join(self.tf.root,"testbag"))
        self.bag = bldr.BagBuilder(self.tf.root, "testbag", self.cfg)
        self.tf.track("testbag")

    def tearDown(self):
        self.bag._unset_logfile()
        self.bag = None
        self.tf.clean()

    def test_ctor(self):
        enh = tools.ReferenceEnhancer(rescfg, self.log)
        self.assertIsNotNone(enh.cfg)
        self.assertIsNotNone(enh.doir)
        self.assertIsNotNone(enh.log)

    def test_enhancer_for(self):
        enh = tools.ReferenceEnhancer(rescfg, self.log).enhancer_for(self.bag)
        self.assertTrue(isinstance(enh.refs, OrderedDict))
        self.assertEqual(len(enh.refs), 1)

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_merge_enhanced_ref(self):
        enh = tools.ReferenceEnhancer(rescfg, self.log).enhancer_for(self.bag)
        self.assertEqual(len(enh.refs), 1)

        # add a new DOI to the references list
        doid = "10.1126/science.169.3946.635"
        doiu = "https://doi.org/"+doid
        self.assertTrue(enh.merge_enhanced_ref("doi:"+doid))
        self.assertEqual(len(enh.refs), 2)
        self.assertIn(doiu, enh.refs)
        self.assertEqual(enh.refs.keys()[1], doiu)
        self.assertEqual(enh.refs[doiu]['location'], doiu)
        self.assertIn('citation', enh.refs[doiu])
        self.assertIn('title', enh.refs[doiu])
        self.assertEqual(enh.refs[doiu]['refType'], "IsCitedBy")

        # test effectiveness of override, and of updates
        del enh.refs[doiu]['title']
        enh.refs[doiu]['description'] = "The Real Story"
        enh.refs[doiu]['refType'] = "IsSupplementTo"
        self.assertFalse(enh.merge_enhanced_ref("doi:"+doid, False))
        self.assertIn('citation', enh.refs[doiu])
        self.assertNotIn('title', enh.refs[doiu])
        self.assertIn('description', enh.refs[doiu])
        enh.merge_enhanced_ref("doi:"+doid, True)
        self.assertIn('citation', enh.refs[doiu])
        self.assertIn('title', enh.refs[doiu])
        self.assertEqual(enh.refs[doiu]['description'], "The Real Story")
        self.assertEqual(enh.refs[doiu]['refType'], "IsSupplementTo")

        # test alternate forms of DOI
        del enh.refs[doiu]['citation']
        del enh.refs[doiu]['title']
        self.assertTrue(enh.merge_enhanced_ref("http://dx.doi.org/"+doid, False))
        self.assertIn('citation', enh.refs[doiu])
        self.assertIn('title', enh.refs[doiu])
        self.assertEqual(enh.refs[doiu]['description'], "The Real Story")
        self.assertEqual(enh.refs[doiu]['refType'], "IsSupplementTo")

        del enh.refs[doiu]['citation']
        del enh.refs[doiu]['title']
        self.assertTrue(enh.merge_enhanced_ref("https://doi.org/"+doid, False))
        self.assertIn('citation', enh.refs[doiu])
        self.assertIn('title', enh.refs[doiu])
        self.assertEqual(enh.refs[doiu]['description'], "The Real Story")
        self.assertEqual(enh.refs[doiu]['refType'], "IsSupplementTo")

        # test enhancing existing reference
        doid = "10.1364/OE.24.014100"
        doiu = "https://doi.org/10.1364/OE.24.014100"
        self.assertNotIn('title', enh.refs[doiu])
        self.assertNotIn('citation', enh.refs[doiu])
        self.assertTrue(enh.merge_enhanced_ref("doi:"+doid, False))
        self.assertIn('citation', enh.refs[doiu])
        self.assertIn('title', enh.refs[doiu])
        self.assertIn('optical sorting', enh.refs[doiu]['title'])
        self.assertNotIn('description', enh.refs[doiu])
        self.assertEqual(enh.refs[doiu]['refType'], "IsReferencedBy")

        # test failure mode
        self.assertFalse(enh.merge_enhanced_ref("doi:88888/baddoi", False))
        

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_enhance_existing(self):
        enh = tools.ReferenceEnhancer(rescfg, self.log).enhancer_for(self.bag)
        self.assertEqual(len(enh.refs), 1)
        self.assertNotIn('title', enh.refs[enh.refs.keys()[0]])
        self.assertNotIn('citation', enh.refs[enh.refs.keys()[0]])

        enh.enhance_existing()
        self.assertEqual(len(enh.refs), 1)
        self.assertIn('title', enh.refs[enh.refs.keys()[0]])
        self.assertIn('citation', enh.refs[enh.refs.keys()[0]])

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_remove_missing_from(self):
        enh = tools.ReferenceEnhancer(rescfg, self.log).enhancer_for(self.bag)

        # setup
        doid = "10.1126/science.169.3946.635"
        doiu = "https://doi.org/"+doid
        enh.merge_enhanced_ref("doi:"+doid)
        self.assertEqual(len(enh.refs), 2)

        nondoi = "http://example.com/paper"
        enh.refs[nondoi] = { "location": nondoi, "title": "Irreproducibily"}
        enh.refs["_#noloc"] = { "title": "An old publication" }
        self.assertEqual(len(enh.refs), 4)

        # now here's the test
        # examples of refs in input list: a ref description, a DOI, nonsense
        enh.remove_missing_from([enh.refs[nondoi], "doi:"+doid, {"foo":"bar"}])
        self.assertEqual(len(enh.refs), 3)

        origdoi = "https://doi.org/10.1364/OE.24.014100"
        self.assertEqual(enh.refs.keys()[0], doiu)
        self.assertEqual(enh.refs.keys()[1], nondoi)
        self.assertEqual(enh.refs.keys()[2], "_#noloc")
        self.assertEqual(enh.refs[nondoi]['title'], "Irreproducibily")
        self.assertNotIn('citation', enh.refs[nondoi])
        self.assertIn('citation', enh.refs[doiu])
        self.assertIn('title', enh.refs[doiu])
        self.assertNotIn('citation', enh.refs["_#noloc"])

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_enhance_refs(self):
        nondoi = "http://example.com/paper"
        doid = "10.1126/science.169.3946.635"
        doiu = "https://doi.org/"+doid
        origdoi = "https://doi.org/10.1364/OE.24.014100"

        # setup
        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        rmd.insert(0, { "title": "An old publication" })
        rmd.append({ "location": doiu, "title": "Irreproducibily"})
        rmd.append({ "location": nondoi, "title": "Irreproducibily"})
        self.bag.update_metadata_for('', {'references': rmd})

        # test
        enh = tools.ReferenceEnhancer(rescfg, self.log)
        enh.enhance_refs(self.bag)
        
        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 4)

        self.assertEqual(rmd[0]['title'], "An old publication")
        self.assertNotIn('citation', rmd[0])
        self.assertEqual(rmd[1]['location'], origdoi)
        self.assertIn('citation', rmd[1])
        self.assertEqual(rmd[2]['location'], doiu)
        self.assertNotEqual(rmd[2]['title'], "Irreproducibily")
        self.assertIn('citation', rmd[2])
        self.assertEqual(rmd[3]['location'], nondoi)
        self.assertEqual(rmd[3]['title'], "Irreproducibily")
        self.assertNotIn('citation', rmd[3])

    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_enhance_refs_as_annot(self):
        nondoi = "http://example.com/paper"
        doid = "10.1126/science.169.3946.635"
        doiu = "https://doi.org/"+doid
        origdoi = "https://doi.org/10.1364/OE.24.014100"

        # setup
        enh = tools.ReferenceEnhancer(rescfg, self.log).enhance_refs(self.bag)

        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        rmd.insert(0, { "title": "An old publication", "@id": "#ref:old" })
        rmd.append({ "location": doiu, "citation": "in press",
                     "@id": "#doi:"+doid })
        rmd.append({ "location": nondoi, "title": "Irreproducibily",
                     "@id": "#ref:"+nondoi })
        self.bag.update_annotations_for('', {'references': rmd})

        # test
        enh = tools.ReferenceEnhancer(rescfg, self.log)
        enh.enhance_refs(self.bag, as_annot=True, override=False)
        
        rmd = self.bag.bag.annotations_metadata_for('').get('references', [])
        self.assertEqual(len(rmd), 4)

        self.assertEqual(rmd[0]['title'], "An old publication")
        self.assertNotIn('citation', rmd[0])
        self.assertEqual(rmd[1]['location'], origdoi)
        self.assertIn('citation', rmd[1])
        self.assertEqual(rmd[2]['location'], doiu)
        self.assertEqual(rmd[2]['citation'], "in press")
        self.assertIn('citation', rmd[2])
        self.assertEqual(rmd[3]['location'], nondoi)
        self.assertEqual(rmd[3]['title'], "Irreproducibily")
        self.assertNotIn('citation', rmd[3])

        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 1)
        self.assertEqual(rmd[0]['location'], origdoi)
        self.assertIn('citation', rmd[0])
        
    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_enhance_refs_override(self):
        origdoi = "https://doi.org/10.1364/OE.24.014100"

        # setup
        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 1)
        rmd[0]['citation'] = "in press"
        self.bag.update_metadata_for('', {'references': rmd})

        # test override=False
        enh = tools.ReferenceEnhancer(rescfg, self.log)
        enh.enhance_refs(self.bag, override=False)

        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 1)
        self.assertEqual(rmd[0]['citation'], "in press")
        self.assertNotIn('title', rmd[0])
        
        # test override=True
        enh = tools.ReferenceEnhancer(rescfg, self.log)
        enh.enhance_refs(self.bag, override=True)

        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 1)
        self.assertNotEqual(rmd[0]['citation'], "in press")
        self.assertIn('title', rmd[0])
        
    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_synchronize_annotated_refs(self):
        nondoi = "http://example.com/paper"
        doid = "10.1126/science.169.3946.635"
        doiu = "https://doi.org/"+doid
        origdoi = "https://doi.org/10.1364/OE.24.014100"

        # setup
        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 1)
        rmd[0]['citation'] = "in press"
        rmd.append({ "location": nondoi, "title": "Irreproducibily",
                     "@id": "#ref:"+nondoi })
        self.bag.update_metadata_for('', {'references': rmd})
        
        rmd.append({ "location": doiu, "citation": "in press",
                     "@id": "#doi:"+doid })
        rmd.append({ "title": "An old publication", "@id": "#ref:old" })
        self.assertEqual(len(rmd), 4)
        self.bag.update_annotations_for('', {'references': rmd})

        # test
        enh = tools.ReferenceEnhancer(rescfg, self.log)
        enh.synchronize_annotated_refs(self.bag, override=True)

        # check annotated references
        rmd = self.bag.bag.annotations_metadata_for('').get('references', [])
        self.assertEqual(len(rmd), 3)

        self.assertEqual(rmd[0]['location'], origdoi)
        self.assertEqual(rmd[0]['refType'], 'IsReferencedBy')
        self.assertNotEqual(rmd[0]['citation'], "in press")
        self.assertEqual(rmd[1]['location'], nondoi)
        self.assertEqual(rmd[1]['title'], "Irreproducibily")
        self.assertNotIn('citation', rmd[1])
        self.assertEqual(rmd[2]['title'], "An old publication")
        self.assertNotIn('citation', rmd[2])

        # check unannotated references are unchanged (and that missing reference is removed)
        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 2)
        self.assertEqual(rmd[0]['location'], origdoi)
        self.assertEqual(rmd[0]['citation'], 'in press')
        self.assertEqual(rmd[1]['location'], nondoi)
        self.assertEqual(rmd[1]['title'], "Irreproducibily")
        
    @test.skipIf("doi" not in os.environ.get("OAR_TEST_INCLUDE",""),
                 "kindly skipping doi service checks")
    def test_synchronize_annotated_refs_reftype(self):
        nondoi = "http://example.com/paper"
        doid = "10.1126/science.169.3946.635"
        doiu = "https://doi.org/"+doid
        origdoi = "https://doi.org/10.1364/OE.24.014100"

        # setup
        rmd = self.bag.bag.nerd_metadata_for('', False).get('references', [])
        self.assertEqual(len(rmd), 1)
        rmd[0]['citation'] = "in press"
        rmd[0]['refType'] = "References"
        rmd.append({ "location": doiu, "citation": "in press", "refType": "IsSupplementTo",
                     "@id": "#doi:"+doid })
        self.bag.update_metadata_for('', {'references': rmd})
        self.assertEqual(len(rmd), 2)
        self.bag.update_annotations_for('', {'references': rmd})

        # test
        enh = tools.ReferenceEnhancer(rescfg, self.log)
        enh.synchronize_annotated_refs(self.bag, override=True)

        # check annotated references
        rmd = self.bag.bag.annotations_metadata_for('').get('references', [])
        self.assertEqual(len(rmd), 2)

        self.assertEqual(rmd[0]['location'], origdoi)
        self.assertEqual(rmd[0]['refType'], 'IsCitedBy')
        self.assertNotEqual(rmd[0]['citation'], "in press")
        self.assertEqual(rmd[1]['location'], doiu)
        self.assertEqual(rmd[1]['@id'], "#doi:"+doid)
        self.assertNotEqual(rmd[1]['citation'], "in press")
        self.assertEqual(rmd[1]['refType'], 'IsSupplementTo')

    def test_normalize_doi(self):
        doi = "10.88888/goober"
        self.assertEqual(tools.normalize_doi("doi:"+doi), "https://doi.org/"+doi)
        self.assertEqual(tools.normalize_doi("https://dx.doi.org/"+doi), "https://doi.org/"+doi)
        self.assertEqual(tools.normalize_doi("https://doi.org/"+doi), "https://doi.org/"+doi)
        self.assertEqual(tools.normalize_doi(doi), doi)

        
        
        

        
        

if __name__ == '__main__':
    test.main()
