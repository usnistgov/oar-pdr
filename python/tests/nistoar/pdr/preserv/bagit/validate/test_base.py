import os, sys, pdb, json, re
import unittest as test

import nistoar.pdr.preserv.bagit.validate.base as base
import nistoar.pdr.preserv.bagit.bag as bag

datadir = os.path.join( os.path.dirname(os.path.dirname(
                           os.path.dirname(__file__))), "data" )
bagdir = os.path.join(datadir, "samplembag")

class TestValidationIssue(test.TestCase):

    def test_ctor(self):
        issue = base.ValidationIssue("Life", "3.1", "A1.1")

        self.assertEqual(issue.profile, "Life")
        self.assertEqual(issue.profile_version, "3.1")
        self.assertEqual(issue.label, "A1.1")
        self.assertEqual(issue.type, issue.ERROR)
        self.assertTrue(issue.passed())
        self.assertFalse(issue.failed())
        self.assertEqual(issue.specification, "")
        self.assertEqual(len(issue.comments), 0)

        issue = base.ValidationIssue("Life", "3.1", "A1.1", base.REC,
                                     spec="Life must self replicate.",
                                     passed=False)

        self.assertEqual(issue.profile, "Life")
        self.assertEqual(issue.profile_version, "3.1")
        self.assertEqual(issue.label, "A1.1")
        self.assertEqual(issue.type, issue.REC)
        self.assertFalse(issue.passed())
        self.assertTrue(issue.failed())
        self.assertEqual(issue.specification, "Life must self replicate.")
        self.assertEqual(len(issue.comments), 0)

        issue = base.ValidationIssue("Life", "3.1", "A1.1", base.REC,
                                     spec="Life must self replicate.",
                                     passed=False)

        self.assertEqual(issue.profile, "Life")
        self.assertEqual(issue.profile_version, "3.1")
        self.assertEqual(issue.label, "A1.1")
        self.assertEqual(issue.type, issue.REC)
        self.assertEqual(issue.specification, "Life must self replicate.")
        self.assertFalse(issue.passed())
        self.assertTrue(issue.failed())
        self.assertEqual(len(issue.comments), 0)

        issue = base.ValidationIssue("Life", "3.1", "A1.1", base.REC,
                                     spec="Life must self replicate.",
                                     comments=["little", "green"])

        self.assertEqual(issue.profile, "Life")
        self.assertEqual(issue.profile_version, "3.1")
        self.assertEqual(issue.label, "A1.1")
        self.assertEqual(issue.type, issue.REC)
        self.assertTrue(issue.passed())
        self.assertFalse(issue.failed())
        self.assertEqual(issue.specification, "Life must self replicate.")
        self.assertEqual(len(issue.comments), 2)
        self.assertEqual(issue.comments[0], "little")
        self.assertEqual(issue.comments[1], "green")

    def test_description(self):
        
        issue = base.ValidationIssue("Life", "3.1", "A1.1")
        self.assertEqual(issue.summary, "PASSED: Life 3.1 A1.1")
        self.assertEqual(str(issue), issue.summary)
        self.assertEqual(issue.description, issue.summary)

        issue = base.ValidationIssue("Life", "3.1", "A1.1",
                                     spec="Life must self-replicate")
        self.assertEqual(issue.summary,
                         "PASSED: Life 3.1 A1.1: Life must self-replicate")
        self.assertEqual(str(issue), issue.summary)
        self.assertEqual(issue.description, issue.summary)

        issue = base.ValidationIssue("Life", "3.1", "A1.1",
                                     spec="Life must self-replicate", 
                                     passed=False, comments=["Little", "green"])
        self.assertEqual(issue.summary,
                         "ERROR: Life 3.1 A1.1: Life must self-replicate")
        self.assertEqual(str(issue),
                     "ERROR: Life 3.1 A1.1: Life must self-replicate (Little)")
        self.assertEqual(issue.description,
           "ERROR: Life 3.1 A1.1: Life must self-replicate\n  Little\n  green")

class TestValidatorBase(test.TestCase):

    def setUp(self):
        self.bag = bag.NISTBag(bagdir)

    class _TestBase(base.ValidatorBase):
        def test_raise_except(self, bag, want=base.ALL, results=None):
            out = results
            if not out:
                out = base.ValidationResults(bag.name, want)

            t = self._issue("re-goob", "raise an exception")
            re.search(r"goob[g", "gurn")  # a deliberate fail via exception
            out._rec(t, True)

            return out

    def test_catch_except(self):
        tests = self._TestBase({})

        try:
            res = tests.test_raise_except(self.bag)
            self.fail("failed to raise exception as necessary for test")
        except Exception as ex:
            pass

        res = tests.validate(self.bag)
        self.assertEqual(res.count_applied(), 1)
        self.assertEqual(res.count_failed(), 1)
        self.assertIn("Traceback", res.failed()[0].description)
        self.assertIn(", line ", res.failed()[0].description)

    
    def test_fmt_exc(self):
        a = {}
        try:
            a['hello']
            self.fail("failed to detect test KeyError")
        except Exception as ex:
            prob = base._fmt_exc()
            self.assertIn('Traceback', prob)
            self.assertIn(', line ', prob)
            self.assertIn('KeyError', prob)

    


if __name__ == '__main__':
    test.main()
    

