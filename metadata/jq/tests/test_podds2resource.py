#!/usr/bin/python
#
import os, unittest, json, subprocess as subproc, types, pdb
import ejsonschema as ejs

nerdm = "https://www.nist.gov/od/dm/nerdm-schema/v0.1#"
nerdmpub = "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#"
datadir = os.path.join(os.path.dirname(__file__), "data")
janaffile = os.path.join(datadir, "janaf_pod.json")
pdlfile = os.path.join(datadir, "nist-pdl-oct2016.json")
jqlib = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

class TestJanaf(unittest.TestCase):  # 

    def setUp(self):
        # pdb.set_trace() # nerdm::podds2resourc
        self.out = send_file_thru_jq('nerdm::podds2resource', janaffile,
                                     {"id": "ark:ID"})

    def test_id(self): self.assertEquals(self.out['@id'], "ark:ID")
    def test_al(self): self.assertEquals(self.out['accessLevel'], "public")
    def test_context(self):
        self.assertEquals(self.out['@context'],
                          "https://www.nist.gov/od/dm/nerdm-pub-context.jsonld")
    def test_schema(self):
        self.assertEquals(self.out['$schema'],
                          "https://www.nist.gov/od/dm/nerdm-schema/v0.1#")
    def test_extsch(self):
        
        exts = self.out['$extensionSchemas']
        self.assertEquals(len(exts), 1)
        self.assertIn(nerdmpub+"/definitions/PublishedDataResources", exts)

    def test_restypes(self):
        types = self.out['@type']
        self.assertIsInstance(types, list)
        self.assertEquals(len(types), 1)
        self.assertEquals(types[0], "nrdp:PublishedDataResource")

    def test_arestr(self):
        props = "title modified ediid landingPage license".split()
        for prop in props:
            self.assertIn(prop, self.out, "Property not found: " + prop)
            self.assertIsInstance(self.out[prop], types.StringTypes,
                "Property '{0}' not a string: {1}".format(prop, self.out[prop]))

    def test_arearrays(self):
        props = "description bureauCode programCode language references components".split()
        for prop in props:
            self.assertIn(prop, self.out, "Property not found: " + prop)
            self.assertIsInstance(self.out[prop], list,
                "Property '{0}' not a list: {1}".format(prop, self.out[prop]))

    def test_ediid(self):
        self.assertEquals(self.out['ediid'],
                          "ECBCC1C1301D2ED9E04306570681B10735")

    def test_components(self):
        comps = self.out['components']
        self.assertGreaterEqual(len(comps), 318,
                   "Missing components; only {0}/{1}".format(len(comps), 318))
        self.assertLessEqual(len(comps), 318,
                   "Extra components; have {0}/{1}".format(len(comps), 318))

        props = "title describedBy downloadURL mediaType".split()
        for prop in props:
            self.assertIn(prop, comps[0], "Property not found: " + prop)
            self.assertIsInstance(comps[0][prop], types.StringTypes,
                "Property '{0}' not a string: {1}".format(prop, comps[0][prop]))

        exts = comps[0]['$extensionSchemas']
        self.assertEquals(len(exts), 1)
        self.assertIn(nerdmpub+"/definitions/DataFile", exts)

        typs = comps[0]['@type']
        self.assertEquals(len(typs), 2)
        self.assertEquals(typs[0], "nrdp:DataFile")
        self.assertEquals(typs[1], "dcat:Distribution")

        props = "describedBy downloadURL".split()
        for prop in props:
            self.assertTrue(comps[0][prop].startswith("http://www.nist.gov/"),
                            prop+" property not a URL: "+comps[0][prop])

    def test_valid(self):
        pass

def format_argopts(argdata):
    """
    format the input dictionary into --argjson options
    """
    argopts = []
    if argdata:
        if not isinstance(argdata, dict):
            raise ValueError("args parameter is not a dictionary: "+str(argdata))
        for name in argdata:
            argopts += [ "--argjson", name, json.dumps(argdata[name]) ]

    return argopts
    

def send_file_thru_jq(jqfilter, filepath, args=None):
    """
    This executes jq with JSON data from the given file and returns the converted
    output.

    :param str jqfilter:  The jq filter to apply to the input
    :param str filepath:  the path to the input JSON data file
    :param dict args:     arguments to pass in via --argjson
    """
    argopts = format_argopts(args)
    
    with open(filepath):
        pass
    if not isinstance(jqfilter, types.StringTypes):
        raise ValueError("jqfilter parameter not a string: " + str(jqfilter))

    cmd = "jq -L {0}".format(jqlib).split() + argopts

    def impnerdm(filter):
        return 'import "pod2nerdm" as nerdm; ' + filter

    cmd.extend([impnerdm(jqfilter), filepath])

    proc = subproc.Popen(cmd, stdout=subproc.PIPE, stderr=subproc.PIPE)
    (out, err) = proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(err + "\nFailed jq command: "+formatcmd(cmd))

    return json.loads(out)

def formatcmd(cmd):
    if not isinstance(cmd, (list, tuple)):
        return str(cmd)
    if isinstance(cmd, tuple):
        cmd = list(cmd)    
    for i in range(len(cmd)):
        if len(cmd[i].split()) > 1:
            cmd[i] = "'{0}'".format(cmd[i])
        elif cmd[i].startswith('"') and cmd[i].endswith('"'):
            cmd[i] = "'{0}'".format(cmd[i])
    return " ".join(cmd)

class TestSelf(unittest.TestCase):

    def test_format_argopts(self):
        opts = format_argopts({"id": "ark:ID", "goober": [ 1, 2 ]})
        self.assertEqual(opts,
            ['--argjson', 'id', '"ark:ID"', '--argjson', 'goober', '[1, 2]'])

    def test_bad_format_argopts(self):
        with self.assertRaises(ValueError):
            opts = format_argopts(["id", "ark:ID", "goober", [ 1, 2 ]])

    def test_send_file_badfile(self):
        with self.assertRaises(IOError):
            send_file_thru_jq('.', "nonexistent_file.json")
        
    def test_send_file_badfilter(self):
        with self.assertRaises(IOError):
            send_file_thru_jq({}, "nonexistent_file.json")

    def test_formatcmd(self):
        cmd = ['jq', '-L', 'jqlib', 'import "pod2nerdm" as nerdm; .accessLevel',
               'janaf_pod.json']
        self.assertEquals(formatcmd(cmd),
     "jq -L jqlib 'import \"pod2nerdm\" as nerdm; .accessLevel' janaf_pod.json")
        
    def test_send_file(self):
        out = send_file_thru_jq(".accessLevel", janaffile)
        self.assertEquals(out, 'public')
        
    def test_send_file_w_args(self):
        out = send_file_thru_jq(".accessLevel", janaffile,
                                {"id": "ID", "goob": "gurn"})
        self.assertEquals(out, 'public')
        

if __name__ == '__main__':
    unittest.main()



          
    
