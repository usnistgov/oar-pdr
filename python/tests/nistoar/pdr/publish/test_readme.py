import os, sys, pdb, shutil, logging, json, re
import unittest as test
from collections import OrderedDict
from StringIO import StringIO

from nistoar.testing import *
from nistoar.pdr.preserv.bagit import NISTBag
from nistoar.pdr.publish import readme
import nistoar.pdr.exceptions as exceptions
from nistoar.pdr.utils import read_nerd

utestdir = os.path.dirname(os.path.abspath(__file__))
pdrdir = os.path.dirname(utestdir)
datadir = os.path.join( os.path.dirname(utestdir), "preserv", "data" )
bagdir = os.path.join(datadir, "samplembag")
metabagdir = os.path.join(datadir, "metadatabag")
basedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(pdrdir))))
etcdir = os.path.join(basedir, "etc")
assert os.path.isdir(etcdir)
tmpldir = os.path.join(etcdir, "mako", "readme")

stdreclim = sys.getrecursionlimit()
# def setUpModule():
#     sys.setrecursionlimit(200)

# def tearDownModule():
#     global stdreclim
#     sys.setrecursionlimit(stdreclim)
    

class TestReadmeGenerator(test.TestCase):

    def setUp(self):
        for key in "OAR_HOME OAR_ETC_DIR OAR_MAKO_TEMPLATES_DIR".split():
            if key in os.environ:
                del os.environ[key]

        bag = NISTBag(metabagdir)
        self.nerdm = bag.nerdm_record()
        self.gen = readme.ReadmeGenerator(tmpldir)

    def test_get_tmpl8(self):
        t = self.gen._get_tmpl8("front_matter")
        out = t.render(_prompts=True, _brief=False, nrd=self.nerdm, **self.nerdm)
        self.assertGreater(len(out), 5)
        self.assertIn("Version ", out)

    def test_find_default_templatedir(self):
        self.assertIsNone(readme.ReadmeGenerator.find_default_templatedir())

        os.environ['OAR_HOME'] = "goob"
        self.assertEqual(readme.ReadmeGenerator.find_default_templatedir(),
                         os.path.join("goob", "etc", "mako", "readme"))
    
        os.environ['OAR_ETC_DIR'] = "goob"
        self.assertEqual(readme.ReadmeGenerator.find_default_templatedir(),
                         os.path.join("goob", "mako", "readme"))
    
        os.environ['OAR_MAKO_TEMPLATES_DIR'] = "goob"
        self.assertEqual(readme.ReadmeGenerator.find_default_templatedir(),
                         os.path.join("goob", "readme"))
    
        os.environ['OAR_MAKO_TEMPLATES_DIR'] = os.path.join(etcdir, "mako")
        t = readme.ReadmeGenerator()
        self.assertEqual(t.templatedir, os.path.join(etcdir, "mako", "readme"))

    def test_write_front_matter(self):
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_front_matter()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn(self.nerdm['title'][:50], txt)
        self.assertIn('Version '+self.nerdm['version'], txt)
        self.assertIn('DOI: https://doi.org/'+self.nerdm['doi'][4:], txt)
        self.assertIn('##', txt)
                         
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False)
        wrtr.write_front_matter()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn(self.nerdm['title'][:50], txt)
        self.assertIn('Version '+self.nerdm['version'], txt)
        self.assertNotIn('##', txt)

    def test_write_general_info(self):
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_general_info()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('General Information', txt)
        self.assertIn('Geographical ', txt)
        self.assertIn('[##', txt)
                         
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False)
        wrtr.write_general_info()
        txt = txt.getvalue()
        self.assertEqual(len(txt), 0)

    def test_write_data_use(self):
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_data_use()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Data Use Notes', txt)
        self.assertIn('Levine', txt)
        self.assertNotIn('##', txt)
                         
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False)
        wrtr.write_data_use()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Data Use Notes', txt)
        self.assertIn('Levine', txt)
        self.assertNotIn('##', txt)

    def test_write_references(self):
        self.nerdm['references'][0]['citation'] = "Curry & Levine 2016"
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_references()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('References', txt)
        self.assertIn("Curry & Levine 2016", txt)
        self.assertIn('##', txt)
                         
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False)
        wrtr.write_references()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('References', txt)
        self.assertIn("Curry & Levine 2016", txt)
        self.assertNotIn('##', txt)

    def test_write_version_history(self):
        
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_version_history()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Version History', txt)
        self.assertIn("1.0.0 (this version)", txt)  
        self.assertNotIn('[##', txt)

        del self.nerdm['version']
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_version_history()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Version History', txt)
        self.assertNotIn("1.0.0", txt)  
        self.assertIn("1.0 (this version)", txt)  
        self.assertNotIn('[##', txt)

        self.nerdm['version'] = "2.0.0"
        self.nerdm['versionHistory'] = [{
            "version": "1.0.0",
            "description": "initial version"
        },{
            "version": "2.0.0",
            "description": "updated after reanalysis"
        }]
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_version_history()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Version History', txt)
        self.assertIn("1.0.0", txt)
        self.assertIn("2.0.0 (this version)", txt)
        self.assertIn('[##', txt)

        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False)
        wrtr.write_version_history()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Version History', txt)
        self.assertIn("1.0.0", txt)
        self.assertIn("2.0.0", txt)
        self.assertIn("(this version)", txt)
        self.assertNotIn('[##', txt)

    def test_write_methods(self):
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_methods()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Methodological', txt)
        self.assertIn('##', txt)
                         
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False)
        wrtr.write_methods()
        txt = txt.getvalue()
        self.assertEqual(len(txt), 0)

    def test_write_data_summary(self):
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True)
        wrtr.write_data_overview()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Data Overview', txt)
        self.assertIn('  trial1.json', txt)
        self.assertIn('  trial3\n', txt)
        self.assertIn('    trial3a.json', txt)
        self.assertIn('[##', txt)
        self.assertNotIn('is accessible', txt)
                         
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False)
        wrtr.write_data_overview()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Data Overview', txt)
        self.assertIn('  trial1.json', txt)
        self.assertIn('  trial3\n', txt)
        self.assertIn('    trial3a.json', txt)
        self.assertNotIn('##', txt)
        self.assertNotIn('is accessible', txt)

        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False, True)
        wrtr.write_data_overview()
        txt = txt.getvalue()
        self.assertEqual(len(txt), 0)

        self.nerdm['components'].append({
            "@type": ["dcat:Distribution"],
            "accessURL": "https://doi.org/"+self.nerdm['doi'][4:],
            "title": "DOI Access for \""+self.nerdm['title']+"\"",
            "description": "This URL is just another way to get to the landing page."
        })
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, False, True)
        wrtr.write_data_overview()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Data Overview', txt)
        self.assertNotIn('trial1.json', txt)
        self.assertNotIn('trial3', txt)
        self.assertIn('is available', txt)
        self.assertIn('DOI Access', txt)
        self.assertIn('another way', txt)

        self.nerdm['components'][-1]['@type'] = ["nrd:Hidden", "dcat:Distribution"]
        txt = StringIO()
        wrtr = self.gen.Writer(self.gen, self.nerdm, txt, True, False)
        wrtr.write_data_overview()
        txt = txt.getvalue()
        self.assertGreater(len(txt), 5)
        self.assertIn('Data Overview', txt)
        self.assertIn('trial1.json', txt)
        self.assertIn('trial3', txt)
        self.assertNotIn('is available', txt)
        
    def test_generate(self):
        self.nerdm['references'][0]['citation'] = "Curry & Levine 2016"

        txt = StringIO()
        self.gen.generate(self.nerdm, txt, True)
        txt = txt.getvalue()
        self.assertIn(self.nerdm['title'][:50], txt)
        self.assertIn('Version '+self.nerdm['version'], txt)
        self.assertIn('###', txt)
        self.assertIn('General Information', txt)
        self.assertIn('Data Use Notes', txt)
        self.assertIn('References', txt)
        self.assertIn('Data Overview', txt)
        self.assertIn('  trial1.json', txt)
        self.assertIn('  trial3\n', txt)
        self.assertIn('    trial3a.json', txt)
        self.assertIn('Version History', txt)
        self.assertIn('Methodological Information', txt)
        self.assertIn('##', txt)
        self.assertIn('[##', txt)
                         
        txt = StringIO()
        self.gen.generate(self.nerdm, txt, True, True)
        txt = txt.getvalue()
        self.assertIn(self.nerdm['title'][:50], txt)
        self.assertIn('Version '+self.nerdm['version'], txt)
        self.assertIn('###', txt)
        self.assertIn('General Information', txt)
        self.assertIn('Data Use Notes', txt)
        self.assertIn('References', txt)
        self.assertNotIn('Data Overview', txt)
        self.assertNotIn('trial1.json', txt)
        self.assertNotIn('trial3', txt)
        self.assertNotIn('is accessible', txt)
        self.assertIn('Version History', txt)
        self.assertIn('Methodological Information', txt)
        self.assertIn('##', txt)
        self.assertIn('[##', txt)
                         
        txt = StringIO()
        self.gen.generate(self.nerdm, txt, False)
        txt = txt.getvalue()
        self.assertIn(self.nerdm['title'][:50], txt)
        self.assertIn('Version '+self.nerdm['version'], txt)
        self.assertNotIn('General Information', txt)
        self.assertIn('Data Use Notes', txt)
        self.assertIn('References', txt)
        self.assertIn('Data Overview', txt)
        self.assertIn('  trial1.json', txt)
        self.assertIn('  trial3\n', txt)
        self.assertIn('    trial3a.json', txt)
        self.assertIn('Version History', txt)
        self.assertNotIn('Methodological Information', txt)
        self.assertNotIn('##', txt)
                         
        txt = StringIO()
        self.gen.generate(self.nerdm, txt, False, True)
        txt = txt.getvalue()
        self.assertIn(self.nerdm['title'][:50], txt)
        self.assertIn('Version '+self.nerdm['version'], txt)
        self.assertNotIn('General Information', txt)
        self.assertIn('Data Use Notes', txt)
        self.assertIn('References', txt)
        self.assertNotIn('Data Overview', txt)
        self.assertNotIn('trial1.json', txt)
        self.assertNotIn('trial3', txt)
        self.assertIn('Version History', txt)
        self.assertNotIn('Methodological Information', txt)
        self.assertNotIn('##', txt)



if __name__ == '__main__':
    test.main()
