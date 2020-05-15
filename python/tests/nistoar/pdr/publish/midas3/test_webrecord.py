from __future__ import absolute_import
import os, pdb, requests, logging, time, json
from collections import OrderedDict, Mapping
from StringIO import StringIO
import unittest as test
from copy import deepcopy

from nistoar.testing import *
from nistoar.pdr.publish.midas3 import webrecord as webrec

class TestWebRecorder(test.TestCase):

    def setUp(self):
        self.tf = Tempfiles()
        self.recfile = self.tf.track("webrec.log")
        self.rcrdr = webrec.WebRecorder(self.recfile)

    def tearDown(self):
        self.rcrdr.close_file()
        self.tf.clean()

    def readlog(self):
        out = []
        with open(self.recfile) as fd:
            rec = {}
            line = None
            for line in fd:
                if line.startswith("=*="):
                    if rec:
                        if 'bodyout' in rec:
                            rec['body'] = rec['bodyout'].getvalue()
                            del rec['bodyout']
                        out.append(rec)
                    rec = {}
                    parts = line.strip().split()
                    parts[3:4] = parts[3].split('.', 1)
                    rec['time'] = " ".join(parts[1:3])
                    rec['svc'] = parts[3]
                    rec['op'] = parts[4]
                    rec['res'] = " ".join(parts[5:])
                elif line.startswith("-+-"):
                    rec['bodyout'] = StringIO()
                elif 'bodyout' in rec:
                    rec['bodyout'].write(line)
                else:
                    if 'headers' not in rec:
                        rec['headers'] = []
                    rec['headers'].append(line)

            if rec:
                if 'bodyout' in rec:
                    rec['body'] = rec['bodyout'].getvalue()
                    del rec['bodyout']
                out.append(rec)
                    
        return out

    def testGET(self):
        self.rcrdr.recGET("/foo/bar?view=sum")

        recs = self.readlog()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['op'], "GET")
        self.assertEqual(recs[0]['svc'], "WebRec")
        self.assertEqual(recs[0]['res'], "/foo/bar?view=sum")
        self.assertIn('time', recs[0])
        self.assertNotIn('body', recs[0])
        self.assertNotIn('headers', recs[0])

    def test_add_handler(self):
        buffer = StringIO()
        hdlr = logging.StreamHandler(buffer)
        self.rcrdr.add_handler(hdlr)

        self.rcrdr.recGET("/foo/bar")
        lines = buffer.getvalue().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("=*="))

        self.rcrdr.remove_handler(hdlr)
        self.rcrdr.recGET("/goob/")
        lines2 = buffer.getvalue().split("\n")
        self.assertEqual(len(lines2), 2)
        self.assertEqual(lines2[0], lines[0])
        self.assertEqual(lines2[1], lines[1])
        
        recs = self.readlog()
        self.assertEqual(len(recs), 2)

    def testPOST(self):
        body = json.dumps({"a": 1, "b": 2}, indent=2)

        self.rcrdr.recPOST("/foo/bar", body=body, qs="view=sum")
        recs = self.readlog()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['op'], "POST")
        self.assertEqual(recs[0]['svc'], "WebRec")
        self.assertEqual(recs[0]['res'], "/foo/bar?view=sum")
        self.assertIn('time', recs[0])
        self.assertNotIn('headers', recs[0])
        self.assertIn('body', recs[0])
        data = json.loads(recs[0]['body'])
        self.assertEqual(data['a'], 1)
        self.assertEqual(data['b'], 2)

    def testPUT(self):
        body = json.dumps({"a": 1, "b": 2}, indent=2)
        
        self.rcrdr.recPUT("/foo/bar", body=body)
        recs = self.readlog()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['op'], "PUT")
        self.assertEqual(recs[0]['svc'], "WebRec")
        self.assertEqual(recs[0]['res'], "/foo/bar")
        self.assertIn('time', recs[0])
        self.assertNotIn('headers', recs[0])
        self.assertIn('body', recs[0])
        data = json.loads(recs[0]['body'])
        self.assertEqual(data['a'], 1)
        self.assertEqual(data['b'], 2)

    def test_isolated(self):
        reglog = logging.getLogger()
        buf = StringIO()
        h = logging.StreamHandler(buf)
        try: 
            reglog.addHandler(h)
            self.rcrdr.recGET("/foo/bar?view=sum")
            self.assertFalse(buf.getvalue())
            recs = self.readlog()
            self.assertEqual(len(recs), 1)

            logging.getLogger("goober").error("hey!")
            self.assertTrue(buf.getvalue())
            recs = self.readlog()
            self.assertEqual(len(recs), 1)
        finally:
            reglog.removeHandler(h)

    def test_start_record(self):
        rec = self.rcrdr.start_record("HEAD", "/goob/gurn/")
        self.assertEqual(rec.op, "HEAD")
        self.assertEqual(rec.resource, "/goob/gurn/")
        self.assertIsNone(rec.qs)
        self.assertEqual(rec.headers, [])
        self.assertEqual(rec.body, '')

        rec = self.rcrdr.start_record("PATCH", "/gurn/goob/", "a=b&c=d")
        self.assertEqual(rec.op, "PATCH")
        self.assertEqual(rec.resource, "/gurn/goob/")
        self.assertEqual(rec.qs, "a=b&c=d")
        self.assertEqual(rec.headers, [])
        self.assertEqual(rec.body, '')

        rec = self.rcrdr.start_record("PATCH", "/gurn/goob/", "a=b&c=d", ["Gurn Cranston", "Johnny Cash"])
        self.assertEqual(rec.op, "PATCH")
        self.assertEqual(rec.resource, "/gurn/goob/")
        self.assertEqual(rec.qs, "a=b&c=d")
        self.assertEqual(rec.headers, ["Gurn Cranston", "Johnny Cash"])
        self.assertEqual(rec.body, '')

        rec = self.rcrdr.start_record("PATCH", "/gurn/goob/", "a=b&c=d", body="BOO!")
        self.assertEqual(rec.op, "PATCH")
        self.assertEqual(rec.resource, "/gurn/goob/")
        self.assertEqual(rec.qs, "a=b&c=d")
        self.assertEqual(rec.headers, [])
        self.assertEqual(rec.body, 'BOO!')

    def test_add_header(self):
        rec = self.rcrdr.start_record("HEAD", "/goob/gurn/")
        rec.add_header("Joe Biden")
        rec.add_header("Accept", "text/plain")
        self.assertEqual(rec.headers, ["Joe Biden", "Accept: text/plain"])

    def test_add_header_from_wsgienv(self):
        env = OrderedDict([
            ('HTTP_AUTHORIZATION', 'Bearer KEY'),
            ('CONTENT_LENGTH', "0"),
            ('HTTP_ACCEPT', 'text/plain'),
            ('CONTENT_TYPE', 'text/json'),
            ('wsgi.input', StringIO()),
            ('PATH_INFO', '/dum/'),
            ('HTTP_CONTENT_VERSION', '1.0')
        ])
        
        rec = self.rcrdr.start_record("HEAD", "/goob/gurn/")
        rec.add_header_from_wsgienv(env)
        self.assertEqual(rec.headers, ["Authorization: Bearer KEY",
                                       "Content-Length: 0",
                                       "Accept: text/plain",
                                       "Content-Type: text/json",
                                       "Content-Version: 1.0"      ])

    def test_add_body_text(self):
        rec = self.rcrdr.start_record("HEAD", "/goob/gurn/")
        self.assertEqual(rec.body, '')

        rec.add_body_text("goober")
        self.assertEqual(rec.body, 'goober')

        rec.add_body_text(" Gurn\n")
        self.assertEqual(rec.body, 'goober Gurn\n')

    def test_read_body(self):
        body = StringIO(json.dumps({"a": 1, "b": 2}, indent=2) + "\n")
        
        rec = self.rcrdr.start_record("HEAD", "/goob/gurn/")
        self.assertEqual(rec.body, '')

        rec.read_body(body)
        data = json.loads(rec.body)
        self.assertEqual(data['a'], 1)
        self.assertEqual(data['b'], 2)


    def test_parser_ctor(self):
        self.rcrdr.recGET("/foo/bar?view=sum")
        parser = webrec.RequestLogParser(self.recfile)
        self.assertEqual(parser._recfile, self.recfile)

    def test_parser_byrec_records(self):
        self.rcrdr.recPOST("/foo/bar", body="a\nb\nc\n")
        self.rcrdr.recGET("/foo/gurn")
        self.rcrdr.recGET("/foo/goob")

        with open(self.recfile) as fd:
            iter = webrec.RequestLogParser._byrecord(fd).records()
            rec = iter.next()
            self.assertIn("/foo/bar", rec.next())
        
            rec = iter.next()
            self.assertIn("/foo/gurn", rec.next())

            rec = iter.next()
            self.assertIn("/foo/goob", rec.next())

            with self.assertRaises(StopIteration):
                line = iter.next()

    def test_parser_byrec_reclines(self):
        self.rcrdr.recPOST("/foo/bar", body="a\nb\nc\n")
        self.rcrdr.recGET("/foo/gurn")

        with open(self.recfile) as fd:
            byrec = webrec.RequestLogParser._byrecord(fd)
            recs = byrec.records()
            rec = recs.next()
            self.assertIn("/foo/bar", rec.next())
            self.assertEqual("-+-\n", rec.next())
            self.assertEqual("a\n", rec.next())
            self.assertEqual("b\n", rec.next())
            self.assertEqual("c\n", rec.next())
            self.assertEqual("\n", rec.next())
            self.assertEqual("\n", rec.next())
            with self.assertRaises(StopIteration):
                rec.next()

            rec = recs.next()
            self.assertIn("/foo/gurn", rec.next())
            with self.assertRaises(StopIteration):
                rec.next()

            with self.assertRaises(StopIteration):
                recs.next()

    def test_parser_parse_record(self):
        self.rcrdr.recPOST("/foo/bar", headers=["Content-Type: text/plain"], body="a\nb\nc\n")
        self.rcrdr.recGET("/foo/gurn")

        parser = webrec.RequestLogParser(self.recfile)
        with open(parser._recfile) as fd:
            byrec = parser._byrecord(fd)
            recs = byrec.records()
            rec = parser._parse_record(recs.next())

            self.assertEquals(rec.op, "POST")
            self.assertEquals(rec.resource, "/foo/bar")
            self.assertTrue(rec.time)
            self.assertEqual(rec.service, "WebRec")
            self.assertEqual(rec.headers, ["Content-Type: text/plain"])
            self.assertEqual(rec.body, "a\nb\nc\n\n\n")

            rec = parser._parse_record(recs.next())
            self.assertEquals(rec.op, "GET")
            self.assertEquals(rec.resource, "/foo/gurn")
            self.assertTrue(rec.time)
            self.assertEqual(rec.service, "WebRec")
            self.assertEqual(rec.headers, [])
            self.assertEqual(rec.body, "")
            
    def test_parser_count_records(self):
        self.rcrdr.recHEAD("/foo/gurn")
        self.rcrdr.recPOST("/foo/bar", body="a\nb\nc\n")
        self.rcrdr.recGET("/foo/gurn")

        parser = webrec.RequestLogParser(self.recfile)
        self.assertEqual(parser.count_records(), 3)

    def test_parser_parse(self):
        self.rcrdr.recHEAD("/foo/gurn")
        self.rcrdr.recPOST("/foo/bar", headers=[
            "Accept: text/json",
            "Content-Type: text/plain"
        ], body="a\nb\nc\n")
        self.rcrdr.recGET("/foo/gurn")
        self.rcrdr.recDELETE("/foo/bar/goob")

        parser = webrec.RequestLogParser(self.recfile)
        recs = parser.parse()
        self.assertEqual(len(recs), 4)

        self.assertEqual(recs[0].op, "HEAD")
        self.assertEqual(recs[0].resource, "/foo/gurn")
        self.assertEqual(len(recs[0].headers), 0)

        self.assertEqual(recs[1].op, "POST")
        self.assertEqual(recs[1].resource, "/foo/bar")
        self.assertEqual(len(recs[1].headers), 2)
        self.assertEqual(recs[1].headers[0], "Accept: text/json")
        self.assertEqual(recs[1].headers[1], "Content-Type: text/plain")
        self.assertEqual(recs[1].body, "a\nb\nc\n\n\n")

        self.assertEqual(recs[2].op, "GET")
        self.assertEqual(recs[2].resource, "/foo/gurn")
        self.assertEqual(len(recs[2].headers), 0)

        self.assertEqual(recs[3].op, "DELETE")
        self.assertEqual(recs[3].resource, "/foo/bar/goob")
        self.assertEqual(len(recs[3].headers), 0)

        recs = parser.parse(0, 0)
        self.assertEqual(len(recs), 0)

        recs = parser.parse(-10, 4)
        self.assertEqual(len(recs), 0)

        recs = parser.parse(2, 2)
        self.assertEqual(len(recs), 2)

        self.assertEqual(recs[0].op, "GET")
        self.assertEqual(recs[0].resource, "/foo/gurn")
        self.assertEqual(len(recs[0].headers), 0)

        self.assertEqual(recs[1].op, "DELETE")
        self.assertEqual(recs[1].resource, "/foo/bar/goob")
        self.assertEqual(len(recs[1].headers), 0)

        recs = parser.parse(-3, 2)
        self.assertEqual(len(recs), 2)

        self.assertEqual(recs[0].op, "POST")
        self.assertEqual(recs[0].resource, "/foo/bar")
        self.assertEqual(len(recs[0].headers), 2)

        self.assertEqual(recs[1].op, "GET")
        self.assertEqual(recs[1].resource, "/foo/gurn")
        self.assertEqual(len(recs[1].headers), 0)

        recs = parser.parse(-5, 2)
        self.assertEqual(len(recs), 1)

        self.assertEqual(recs[0].op, "HEAD")
        self.assertEqual(recs[0].resource, "/foo/gurn")
        self.assertEqual(len(recs[0].headers), 0)


    def test_parser_parse_last(self):
        self.rcrdr.recHEAD("/foo/gurn")
        self.rcrdr.recPOST("/foo/bar", headers=[
            "Accept: text/json",
            "Content-Type: text/plain"
        ], body="a\nb\nc\n")
        self.rcrdr.recGET("/foo/gurn")
        self.rcrdr.recDELETE("/foo/bar/goob")

        parser = webrec.RequestLogParser(self.recfile)
        rec = parser.parse_last()

        self.assertEqual(rec.op, "DELETE")
        self.assertEqual(rec.resource, "/foo/bar/goob")
        self.assertEqual(len(rec.headers), 0)



if __name__ == '__main__':
    test.main()

