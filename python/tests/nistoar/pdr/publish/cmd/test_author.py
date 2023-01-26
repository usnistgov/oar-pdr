import os, sys, logging, argparse, pdb, imp, time, json, shutil
import unittest as test
from copy import deepcopy
from datetime import date

from nistoar.testing import *
from nistoar.pdr import cli
from nistoar.pdr.publish.cmd import author
from nistoar.pdr.exceptions import PDRException, ConfigurationException
from nistoar.pdr.preserv.bagit import NISTBag, BagBuilder
import nistoar.pdr.config as cfgmod

testdir = os.path.dirname(os.path.abspath(__file__))
pdrmoddir = os.path.dirname(os.path.dirname(testdir))
datadir = os.path.join(pdrmoddir, "preserv", "data")

class TestAddAuthorCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("work")
        self.config = {}
        self.authcmd = author.AddAuthorCmd()
        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(self.authcmd)

        self.bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), self.bagdir)
        
    def tearDown(self):
        self.tf.clean()

    def test_parse_withall(self):
        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(author)

        args = self.cmd.parse_args("-q authors add pdr2222".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "authors")
        self.assertEqual(args.authors_subcmd, "add")
        self.assertEqual(args.aipid, ["pdr2222"])

    def test_parse(self):
        args = self.cmd.parse_args("-q add pdr2222".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "add")
        self.assertEqual(args.aipid, ["pdr2222"])
        self.assertIsNone(args.bagparent)
        self.assertIsNone(args.fn)
        self.assertIsNone(args.family)
        self.assertIsNone(args.given)
        self.assertIsNone(args.middle)
        self.assertIsNone(args.orcid)
        self.assertIsNone(args.affil)

        args = self.cmd.parse_args("-q add pdr2222 -f Cranston".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "add")
        self.assertEqual(args.aipid, ["pdr2222"])
        self.assertIsNone(args.bagparent)
        self.assertIsNone(args.fn)
        self.assertEqual(args.family, "Cranston")
        self.assertIsNone(args.given)
        self.assertIsNone(args.middle)
        self.assertIsNone(args.orcid)
        self.assertIsNone(args.affil)

    def test_parse_affil(self):
        args = self.cmd.parse_args("-q add pdr2222 -i NIST".split())
        self.assertEqual(args.workdir, "")
        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertEqual(args.cmd, "add")
        self.assertEqual(args.aipid, ["pdr2222"])
        self.assertIsNone(args.bagparent)
        self.assertIsNone(args.fn)
        self.assertIsNone(args.family)
        self.assertIsNone(args.given)
        self.assertIsNone(args.middle)
        self.assertIsNone(args.orcid)
        self.assertEqual(args.affil, [["NIST"]])

        args = self.cmd.parse_args("-q add pdr2222 -i NIST MML ODI".split())
        self.assertEqual(args.affil, [["NIST", "MML", "ODI"]])

        args = self.cmd.parse_args("-q add pdr2222 -i NIST MML ODI -i UIUC NCSA".split())
        self.assertEqual(args.affil, [["NIST", "MML", "ODI"], ["UIUC", "NCSA"]])

authors = [
    {
        "fn": "Gurn W. Cranston",
        "familyName": "Cranston",
        "middleName": "Werner",
        "givenName": "Gurn",
        "orcid": "0000-1234-5678-9101",
        "affiliation": [
            {
                "title": "National Institute of Standards and Technology",
                "subunits": [ "MML", "ODI" ],
                "@id": "ror:05xpvk416"
            },
            {
                "title": "University of Maryland"
            }
        ]
    },
    {
        "fn": "M. Trail",
        "familyName": "Trail",
        "givenName": "Mark",
        "orcid": "0000-1234-5678-9102",
        "affiliation": [
            {
                "title": "University of Maryland"
            }
        ]
    }
]


class TestEditAuthorCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("work")
        self.config = {}
        # self.authors = deepcopy(authors)
        self.authcmd = author.EditAuthorCmd()
        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(self.authcmd)

        self.bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), self.bagdir)

        bldr = BagBuilder(os.path.dirname(self.bagdir), os.path.basename(self.bagdir))
        bldr.update_metadata_for('', {'authors': authors}, message="updating for unittest")
        os.remove(bldr.bag.annotations_file_for(''))
        
    def tearDown(self):
        self.tf.clean()

    def test_select_authors(self):
        self.assertEqual(self.authcmd.select_authors("National", [], []), [])
        self.assertEqual(self.authcmd.select_authors("goober", [], authors), [])
        self.assertEqual(self.authcmd.select_authors("Cran", [], authors), [])
        self.assertEqual(self.authcmd.select_authors("Nation", [], authors), [])
        self.assertEqual(self.authcmd.select_authors("ror:05xpvk416", [], authors), [])

        selected = self.authcmd.select_authors("1234", [], authors)
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]['givenName'], "Gurn")
        self.assertEqual(selected[1]['givenName'], "Mark")
        selected = self.authcmd.select_authors("1234", ['o'], authors)
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]['givenName'], "Gurn")
        self.assertEqual(selected[1]['givenName'], "Mark")
        selected = self.authcmd.select_authors("9102", ['o'], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Mark")

        selected = self.authcmd.select_authors("Trail", [], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Mark")
        selected = self.authcmd.select_authors("Trail", ['n'], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Mark")
        self.assertEqual(self.authcmd.select_authors("Trail", ['g'], authors), [])

        selected = self.authcmd.select_authors("Gurn", ['g'], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Gurn")
        self.assertEqual(self.authcmd.select_authors("Werner", ['g'], authors), [])
        selected = self.authcmd.select_authors("Gurn", ['n'], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Gurn")

        selected = self.authcmd.select_authors("University", ['a'], authors)
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]['givenName'], "Gurn")
        self.assertEqual(selected[1]['givenName'], "Mark")
        selected = self.authcmd.select_authors("University", ['a'], authors)
        self.assertEqual(len(selected), 2)
        selected = self.authcmd.select_authors("National", ['a'], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Gurn")

        self.assertEqual(self.authcmd.select_authors("National", ['u'], authors), [])
        selected = self.authcmd.select_authors("MML", [], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Gurn")
        selected = self.authcmd.select_authors("MML", ['u'], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Gurn")
        selected = self.authcmd.select_authors("MML", ['a'], authors)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['givenName'], "Gurn")

    def test_update_auth_data(self):
        auths = deepcopy(authors)

        args = self.cmd.parse_args("edit id -n @MarkTrail -g M. -f trial -i UIUC NCSA astronomy LSST".split())
        self.authcmd.update_auth_data(auths[1], args)
        self.assertEqual(auths[1]['fn'], "@MarkTrail")
        self.assertEqual(auths[1]['givenName'], "M.")
        self.assertEqual(auths[1]['familyName'], "trial")
        self.assertEqual(auths[1]['@type'], "foaf:Person")
        self.assertEqual(len(auths[1]['affiliation']), 1)
        self.assertEqual(auths[1]['affiliation'][0]['title'], "UIUC")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][0], "NCSA")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][1], "astronomy")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][2], "LSST")

        args = self.cmd.parse_args("edit id -i USForestService -i UIUC NCSA astronomy LSST".split())
        self.authcmd.update_auth_data(auths[1], args)
        self.assertEqual(auths[1]['fn'], "@MarkTrail")
        self.assertEqual(auths[1]['givenName'], "M.")
        self.assertEqual(auths[1]['familyName'], "trial")
        self.assertEqual(auths[1]['@type'], "foaf:Person")
        self.assertEqual(len(auths[1]['affiliation']), 2)
        self.assertEqual(auths[1]['affiliation'][0]['title'], "USForestService")
        self.assertNotIn('subunit', auths[1]['affiliation'][0])
        self.assertEqual(auths[1]['affiliation'][1]['title'], "UIUC")
        self.assertEqual(auths[1]['affiliation'][1]['title'], "UIUC")
        self.assertEqual(auths[1]['affiliation'][1]['subunits'][0], "NCSA")
        self.assertEqual(auths[1]['affiliation'][1]['subunits'][1], "astronomy")
        self.assertEqual(auths[1]['affiliation'][1]['subunits'][2], "LSST")

        args = self.cmd.parse_args("edit id -i UIUC NCSA astronomy LSST -f Trail -i USForestService".split())
        self.authcmd.update_auth_data(auths[1], args)
        self.assertEqual(auths[1]['fn'], "@MarkTrail")
        self.assertEqual(auths[1]['givenName'], "M.")
        self.assertEqual(auths[1]['familyName'], "Trail")
        self.assertEqual(auths[1]['@type'], "foaf:Person")
        self.assertEqual(len(auths[1]['affiliation']), 2)
        self.assertEqual(auths[1]['affiliation'][1]['title'], "USForestService")
        self.assertNotIn('subunit', auths[1]['affiliation'][0])
        self.assertEqual(auths[1]['affiliation'][0]['title'], "UIUC")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][0], "NCSA")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][1], "astronomy")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][2], "LSST")

        args = self.cmd.parse_args("edit id -i NIST MML -i UIUC NCSA astronomy LSST".split())
        self.authcmd.update_auth_data(auths[1], args)
        self.assertEqual(auths[1]['fn'], "@MarkTrail")
        self.assertEqual(auths[1]['givenName'], "M.")
        self.assertEqual(auths[1]['@type'], "foaf:Person")
        self.assertEqual(auths[1]['familyName'], "Trail")
        self.assertEqual(len(auths[1]['affiliation']), 2)
        self.assertEqual(auths[1]['affiliation'][0]['title'], "National Institute of Standards and Technology")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][0], "MML")
        self.assertEqual(auths[1]['affiliation'][0]['@id'], "ror:05xpvk416")
        self.assertEqual(len(auths[1]['affiliation'][0]['subunits']), 1)
        self.assertEqual(auths[1]['affiliation'][1]['title'], "UIUC")
        self.assertEqual(auths[1]['affiliation'][1]['subunits'][0], "NCSA")
        self.assertEqual(auths[1]['affiliation'][1]['subunits'][1], "astronomy")
        self.assertEqual(auths[1]['affiliation'][1]['subunits'][2], "LSST")

        args = self.cmd.parse_args("edit id -E -g Mark".split())
        self.authcmd.update_auth_data(auths[1], args)
        self.assertEqual(auths[1]['fn'], "Mark Trail")
        self.assertEqual(auths[1]['givenName'], "Mark")
        self.assertEqual(auths[1]['familyName'], "Trail")
        self.assertNotIn('middleName', auths[1])

        args = self.cmd.parse_args("edit id -E -m Z.".split())
        self.authcmd.update_auth_data(auths[1], args)
        self.assertEqual(auths[1]['fn'], "Mark Z. Trail")
        self.assertEqual(auths[1]['givenName'], "Mark")
        self.assertEqual(auths[1]['familyName'], "Trail")
        self.assertEqual(auths[1]['middleName'], "Z.")

        args = self.cmd.parse_args("edit id -E --delete-middle-name".split())
        self.authcmd.update_auth_data(auths[1], args)
        self.assertEqual(auths[1]['fn'], "Mark Trail")
        self.assertEqual(auths[1]['givenName'], "Mark")
        self.assertEqual(auths[1]['familyName'], "Trail")
        self.assertNotIn('middleName', auths[1])

    def test_execute(self):
        argline = "-q edit -b "+self.workdir+\
                  " pdr2210 -k Trail -n @MarkTrail -g M. -f trial -i UIUC NCSA astronomy LSST"
        self.cmd.execute(argline.split(), deepcopy(self.config))

        bag = NISTBag(self.bagdir)
        nerd = bag.nerdm_record(False)
        auths = nerd.get('authors')

        self.assertEqual(auths[1]['fn'], "@MarkTrail")
        self.assertEqual(auths[1]['givenName'], "M.")
        self.assertEqual(auths[1]['familyName'], "trial")
        self.assertEqual(auths[1]['@type'], "foaf:Person")
        self.assertEqual(len(auths[1]['affiliation']), 1)
        self.assertEqual(auths[1]['affiliation'][0]['title'], "UIUC")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][0], "NCSA")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][1], "astronomy")
        self.assertEqual(auths[1]['affiliation'][0]['subunits'][2], "LSST")

        self.assertEqual(auths[0]['fn'], "Gurn W. Cranston")
        self.assertEqual(auths[0]['givenName'], "Gurn")
        self.assertEqual(auths[0]['familyName'], "Cranston")
        self.assertEqual(len(auths[0]['affiliation']), 2)

        nerd = bag.nerdm_record(True)
        auths = nerd.get('authors')
        self.assertEqual(auths[1]['fn'], "@MarkTrail")

    def test_execute_asannots(self):
        argline = "-q edit -b "+self.workdir+\
                  " pdr2210 -a -k Trail -n @MarkTrail -g M. -f trial -i UIUC NCSA astronomy LSST"
        self.cmd.execute(argline.split(), deepcopy(self.config))

        bag = NISTBag(self.bagdir)
        nerd = bag.nerdm_record(True)
        auths = nerd.get('authors')
        self.assertEqual(auths[1]['fn'], "@MarkTrail")

        nerd = bag.nerdm_record(False)
        auths = nerd.get('authors')
        self.assertEqual(auths[-1]['fn'], "M. Trail")


class TestAddAuthorCmd(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.workdir = self.tf.mkdir("work")
        self.config = {}
        # self.authors = deepcopy(authors)
        self.authcmd = author.AddAuthorCmd()
        self.cmd = cli.PDRCLI()
        self.cmd.load_subcommand(self.authcmd)

        self.bagdir = os.path.join(self.workdir, "pdr2210")
        shutil.copytree(os.path.join(datadir, "metadatabag"), self.bagdir)
        
    def tearDown(self):
        self.tf.clean()

    def test_update_to_datapub(self):
        bag = NISTBag(self.bagdir)
        nerd = bag.nerdm_record(False)
        self.assertEqual(nerd["@type"], ["nrdp:PublicDataResource"])
        self.assertEqual(len(nerd['_extensionSchemas']), 1)
        self.assertTrue(nerd["_extensionSchemas"][0].endswith("/PublicDataResource"))

        upd = self.authcmd.update_to_datapub(nerd)
        self.assertEqual(upd["@type"], ["nrdp:DataPublication", "nrdp:PublicDataResource", "dcat:Dataset"])
        self.assertEqual(len(upd['_extensionSchemas']), 1)
        self.assertTrue(upd["_extensionSchemas"][-1].endswith("/DataPublication"))
        self.assertEqual(len(upd), 2)

        upd = self.authcmd.update_to_datapub(upd)
        self.assertEqual(len(upd), 0)

        upd = self.authcmd.update_to_datapub({})
        self.assertEqual(upd["@type"], ["nrdp:DataPublication", "dcat:Dataset"])
        self.assertEqual(len(upd['_extensionSchemas']), 1)
        self.assertTrue(upd["_extensionSchemas"][-1].endswith("/DataPublication"))
        self.assertEqual(len(upd), 2)

        upd = self.authcmd.update_to_datapub({"$extensionSchemas": []})
        self.assertEqual(upd["@type"], ["nrdp:DataPublication", "dcat:Dataset"])
        self.assertNotIn('_extensionSchemas', upd)
        self.assertIn('$extensionSchemas', upd)
        self.assertEqual(len(upd['$extensionSchemas']), 1)
        self.assertTrue(upd["$extensionSchemas"][-1].endswith("/DataPublication"))
        self.assertEqual(len(upd), 2)
        
        nerd['@type'].insert(0, "nrd:SRD")
        nerd['@type'].append("dcat:Dataset")
        upd = self.authcmd.update_to_datapub(nerd)
        self.assertEqual(upd["@type"], ["nrd:SRD", "nrdp:DataPublication", "nrdp:PublicDataResource",
                                        "dcat:Dataset"])
        self.assertEqual(len(upd['_extensionSchemas']), 1)
        self.assertTrue(upd["_extensionSchemas"][-1].endswith("/DataPublication"))
        self.assertEqual(len(upd), 2)

        nerd['@type'] = ["nrd:SRD", "dcat:Dataset"]
        del nerd["_extensionSchemas"]
        upd = self.authcmd.update_to_datapub(nerd)
        self.assertEqual(upd["@type"], ["nrd:SRD", "nrdp:DataPublication", "dcat:Dataset"])
        self.assertEqual(len(upd['_extensionSchemas']), 1)
        self.assertTrue(upd["_extensionSchemas"][-1].endswith("/DataPublication"))
        self.assertEqual(len(upd), 2)


    def test_execute(self):
        argline = "-q add -b "+self.workdir+\
                  " pdr2210 -n @MarkTrail -g M. -f trial -i UIUC NCSA astronomy LSST"
        self.cmd.execute(argline.split(), deepcopy(self.config))

        bag = NISTBag(self.bagdir)
        nerd = bag.nerdm_record(False)
        auths = nerd.get('authors')

        self.assertEqual(auths[0]['fn'], "@MarkTrail")
        self.assertEqual(auths[0]['givenName'], "M.")
        self.assertEqual(auths[0]['familyName'], "trial")
        self.assertEqual(len(auths[0]['affiliation']), 1)
        self.assertEqual(auths[0]['affiliation'][0]['title'], "UIUC")
        self.assertEqual(auths[0]['affiliation'][0]['subunits'][0], "NCSA")
        self.assertEqual(auths[0]['affiliation'][0]['subunits'][1], "astronomy")
        self.assertEqual(auths[0]['affiliation'][0]['subunits'][2], "LSST")
        self.assertEqual(auths[0]['@type'], "foaf:Person")

        nerd = bag.nerdm_record(True)
        auths = nerd.get('authors')
        self.assertGreater(len(auths), 1)
        self.assertNotEqual(auths[-1]['fn'], "@MarkTrail")

    def test_execute_asannots(self):
        argline = "-q add -a -b "+self.workdir+\
                  " pdr2210 -n @MarkTrail -g M. -f trial -i UIUC NCSA astronomy LSST"
        self.cmd.execute(argline.split(), deepcopy(self.config))

        bag = NISTBag(self.bagdir)
        nerd = bag.nerdm_record(True)
        auths = nerd.get('authors')

        self.assertGreater(len(auths), 1)

        self.assertEqual(auths[-1]['fn'], "@MarkTrail")
        self.assertEqual(auths[-1]['givenName'], "M.")
        self.assertEqual(auths[-1]['familyName'], "trial")
        self.assertEqual(auths[-1]['@type'], "foaf:Person")
        self.assertEqual(len(auths[-1]['affiliation']), 1)
        self.assertEqual(auths[-1]['affiliation'][0]['title'], "UIUC")
        self.assertEqual(auths[-1]['affiliation'][0]['subunits'][0], "NCSA")
        self.assertEqual(auths[-1]['affiliation'][0]['subunits'][1], "astronomy")
        self.assertEqual(auths[-1]['affiliation'][0]['subunits'][2], "LSST")

        nerd = bag.nerdm_record(False)
        auths = nerd.get('authors')
        self.assertIsNone(auths)


    
        
        
            


if __name__ == '__main__':
    test.main()

