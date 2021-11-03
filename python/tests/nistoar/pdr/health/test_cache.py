import os, sys, pdb, shutil, logging, json, time, datetime, re
import unittest as test
from collections import OrderedDict, Mapping
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.health import cache
from nistoar.pdr.health.servicechecker import CheckResult


class TestCacheFunctions(test.TestCase):

    def volumes(self):
        recent = int(time.time() * 1000) - 8*3600000
        return [
            {
                'name':        "v1",
                'totalsize':   2938039514,
                'filecount':   539,
                'checkedDate': "1970-01-01T00:00:00Z",
                'checked':     1634748095922
            },
            {
                'name':        "v2",
                'totalsize':   2938039514,
                'filecount':   539,
                'checkedDate': datetime.datetime.fromtimestamp(recent/1000.0).isoformat(),
                'checked':     recent
            }
        ]

    def test_unchecked_volumes(self):
        v = cache.unchecked_volumes(self.volumes(), 20)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]['name'], "v1")

        v = cache.unchecked_volumes(self.volumes(), 7)
        self.assertEqual(len(v), 2)
        self.assertEqual(v[0]['name'], "v1")
        self.assertEqual(v[1]['name'], "v2")

        v = cache.unchecked_volumes(self.volumes(), 24*365*10)  # 10 years
        self.assertEqual(len(v), 0)

    def test_check_for_unchecked_volumes(self):
        cr = CheckResult("https://v", "GET", data=self.volumes())
        self.assertIsNone(cr.ok)
        self.assertIsNone(cr.message)
        cache.check_for_unchecked_volumes(cr, None)
        self.assertIs(cr.ok, False)
        self.assertEqual(cr.message, "Volumes have files unchecked in the last 24 hours: v1")

        cr = CheckResult("https://v", "GET", data=self.volumes())
        self.assertIsNone(cr.ok)
        self.assertIsNone(cr.message)
        cache.check_for_unchecked_volumes(cr, None, hourssince=5)
        self.assertIs(cr.ok, False)
        self.assertEqual(cr.message, "Volumes have files unchecked in the last 5 hours: v1, v2")

        cr = CheckResult("https://v", "GET", data=self.volumes())
        self.assertIsNone(cr.ok)
        self.assertIsNone(cr.message)
        cache.check_for_unchecked_volumes(cr, None, hourssince=24*265*10)
        self.assertIs(cr.ok, True)
        self.assertIsNone(cr.message)

        
        
                         


if __name__ == '__main__':
    test.main()
