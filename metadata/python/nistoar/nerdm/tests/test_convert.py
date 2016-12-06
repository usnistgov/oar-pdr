import unittest, pdb, os, json

import nistoar.nerdm.convert as cvt

mddir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
assert os.path.basename(mddir) == "metadata", "Bad mddir: "+mddir
jqlibdir = os.path.join(mddir, "jq")
datadir = os.path.join(jqlibdir, "tests", "data")
janaffile = os.path.join(datadir, "janaf_pod.json")

class TestPODds2Res(unittest.TestCase):

    def test_convert_file(self):
        cvtr = cvt.PODds2Res(jqlibdir)
        res = cvtr.convert_file(janaffile, "ark:ID")
        self.assertEquals(res["@id"], "ark:ID")
        self.assertEquals(res["accessLevel"], "public")

    def test_convert(self):
        cvtr = cvt.PODds2Res(jqlibdir)

        with open(janaffile) as fd:
            data = fd.read()
            
        res = cvtr.convert(data, "ark:ID")
        self.assertEquals(res["@id"], "ark:ID")
        self.assertEquals(res["accessLevel"], "public")

    def test_convert_data(self):
        cvtr = cvt.PODds2Res(jqlibdir)

        with open(janaffile) as fd:
            data = json.load(fd)
            
        res = cvtr.convert_data(data, "ark:ID")
        self.assertEquals(res["@id"], "ark:ID")
        self.assertEquals(res["accessLevel"], "public")

        
        
if __name__ == '__main__':
    unittest.main()
