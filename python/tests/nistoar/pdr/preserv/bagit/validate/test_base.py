import os, sys, pdb, json
import unittest as test

import nistoar.pdr.preserv.bagit.validate.base as base

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




if __name__ == '__main__':
    test.main()
    

