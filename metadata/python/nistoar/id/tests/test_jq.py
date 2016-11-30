import unittest, pdb, os, json

import nistoar.jq as jq

mddir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
assert os.path.basename(mddir) == "metadata", "Bad mddir: "+mddir
jqlibdir = os.path.join(mddir, "jq")
datadir = os.path.join(jqlibdir, "tests", "data")
janaffile = os.path.join(datadir, "janaf_pod.json")

class TestJqCommand(unittest.TestCase):

    def setUp(self):
        self.jqc = jq.JqCommand()

    def test_library(self):
        self.assertIsNone(self.jqc.library)
        self.jqc.library = jqlibdir
        self.assertEquals(self.jqc.library, jqlibdir)

    def test_form_argopts(self):
        opts = self.jqc.form_argopts({"id": "ark:ID", "goober": [ 1, 2 ]})
        self.assertEqual(opts,
            ['--argjson', 'id', '"ark:ID"', '--argjson', 'goober', '[1, 2]'])

    def test_bad_form_argopts(self):
        with self.assertRaises(ValueError):
            opts = self.jqc.form_argopts(["id", "ark:ID", "goober", [ 1, 2 ]])

    def test_form_cmd(self):
        self.assertEquals(self.jqc.form_cmd(".goober | [.]"),
                          ['jq', '.goober | [.]'])
        self.jqc.library = jqlibdir
        self.assertEquals(self.jqc.form_cmd(".goober | [.]",
                                          {"id": "ark:ID", "goober": [ 1, 2 ]}),
                          ['jq', '-L'+jqlibdir,
                           '--argjson', 'id', '"ark:ID"', '--argjson', 'goober',
                           '[1, 2]', '.goober | [.]'])
        self.assertEquals(self.jqc.form_cmd(".goober | [.]",
                                          {"id": "ark:ID", "goober": [ 1, 2 ]},
                                              'data.json'),
                          ['jq', '-L'+jqlibdir,
                           '--argjson', 'id', '"ark:ID"', '--argjson', 'goober',
                           '[1, 2]', '.goober | [.]', 'data.json'])
        
    def test_format_cmd(self):
        cmd = ['jq', '-L', 'jqlib', 'import "pod2nerdm" as nerdm; .accessLevel',
               'janaf_pod.json']
        self.assertEquals(self.jqc._format_cmd(cmd),
     "jq -L jqlib 'import \"pod2nerdm\" as nerdm; .accessLevel' janaf_pod.json")
        
    def test_process_file(self):
        out = self.jqc.process_file(".accessLevel", janaffile)
        self.assertEquals(out, 'public')
        
    def test_process_file_w_args(self):
        out = self.jqc.process_file(".accessLevel", janaffile,
                                {"id": "ID", "goob": "gurn"})
        self.assertEquals(out, 'public')

    def test_process_data(self):
        data = {"id": "ID", "goob": "gurn"}
        out = self.jqc.process_data("[.goob]", json.dumps(data))
        self.assertEquals(out, ["gurn"])
        
        
if __name__ == '__main__':
    unittest.main()
