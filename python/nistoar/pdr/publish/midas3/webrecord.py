"""
a module that manages the recording of web requests so that they can be played back
"""
import logging, os
from cStringIO import StringIO

RECORD_FORMAT = "=*= %(asctime)s %(name)s %(message)s"

class WebRequest(object):
    """
    a class for colllecting data from a web service request
    """
    def __init__(self, recorder, op=None, resource=None, headers=None, body="", qs=None):
        self.recorder = recorder

        self._op = None
        self._res = None
        self._body = StringIO()
        self.time = None
        self.service = None
        
        self.op = op
        self.resource = resource
        self.body = body
        self.qs = qs
        self._headers = []
        if headers:
            self._headers.extend(headers)

    @property
    def op(self):
        """The HTTP method value requested (e.g. "GET")"""
        return self._op

    @op.setter
    def op(self, val):
        if not val:
            val = "UNSPECIFIED"
        self._op = val

    @property
    def resource(self):
        """
        The URL path of the resource that the request was sent to
        """
        return self._res

    @resource.setter
    def resource(self, val):
        if not val:
            val = "/"
        self._res = val

    @property
    def headers(self):
        return self._headers

    def add_header(self, nameorline, val=None):
        """
        add a header time to the record
        :param str nameorline:  either the name of the header item being added, or the entire 
                                (properly formatted) header line including the value.  This 
                                value is assumed to be the latter if val is not provided
        :param str val:         the value of the header item 
        """
        nameorline = nameorline.rstrip("\n")
        if val is not None:
            nameorline += ": " + val.strip("\n")
        self._headers.append(nameorline)
            
        return self

    def add_header_from_wsgienv(self, wsgienv):
        """
        extract all request header info from the WSGI environment dictionary.  This includes 
        CONTENT_TYPE, CONTENT_LENGTH, and all keys that start with "HTTP_".
        """
        for (key, val) in wsgienv.items():
            if key == 'CONTENT_TYPE':
                key = 'Content-Type'
            elif key == 'CONTENT_LENGTH':
                key = 'Content-Length'
            elif key.startswith("HTTP_"):
                key = "-".join([w.capitalize() for w in key.split("_")[1:]])
            else:
                continue
            self.add_header(key, val)

        return self

    @property
    def body(self):
        """The full text sent in the body of the request"""
        return self._body.getvalue()

    @body.setter
    def body(self, val):
        if val is None:
            val = ''
        self._body = StringIO()
        self._body.write(val)

    def add_body_text(self, txt):
        """
        append the given text to the internally-held body text.  No additional newline characters are 
        added.
        """
        self._body.write(txt)
        return self
            
    def read_body(self, fd):
        """
        read the text from the given file stream and append it to the current body text.
        The file stream will be drained, but the caller is responsible for closing it.
        """
        for line in fd:
            self.add_body_text(line)
        return self

    def record(self):
        """
        record this request to its recorder
        """
        if not self.recorder:
            raise RuntimeException("Request Record not connected to a recorder (%s %s)",
                                   self.op, self.resource)
        self.recorder.record(self)

    @classmethod
    def from_wsgi(cls, recorder, wsgienv, readbody=False):
        """
        create a record given the request information in the environment dictionary provided 
        by the WSGI framework.  By default, the body is not read and inserted into the record; 
        however setting readbody to True will cause the input stream containing the body to be
        read in its entirety.
        """
        out = cls(recorder)
        out.op = wsgienv.get('REQUEST_METHOD')
        out.resource = wsgienv.get('SCRIPT_NAME','') + wsgienv.get('PATH_INFO','/')
        out.qs = wsgienv.get('QUERY_STRING')
        out.add_header_from_wsgienv(wsgienv)
        if readbody and 'wsgi.input' in wsgienv:
            out.read_body(wsgienv['wsgi.input'])
        return out

    def __str__(self):
        return "WebRequest(%s %s)" % (self.op, self.resource)

class WebRecorder(object):
    """
    a class that will record messages sent to a web service
    """

    def __init__(self, recordfile=None, svcname=None, level=logging.DEBUG):
        """
        Create a WebRecorder instance.  If a filename is not provided, no messages will be 
        recorded (unless a handler is added via add_handler()).  
        :param str  recordfile:   the path to a file where requests should be recorded
        :param str  svcname:      a name to give the service the request came to.  This name 
                                    appears in the output record, just before the request method.
                                    The default, if not provided, is "WebRec"
        :param int level:         the logging level for accepting requests by method
        """
        if not svcname:
            svcname = "WebRec"
        self.svcname = svcname
        self._handler = None
        self._recfile = None
        if recordfile:
            self._recfile = recordfile
            self.reclog = logging.getLogger(svcname)
            self.reclog.propagate = 0
            self.reclog.setLevel(level)
            self.open_file()

        self.levels = {
            "GET":    logging.INFO,
            "HEAD":   logging.DEBUG,
            "POST":   logging.ERROR,
            "PUT":    logging.ERROR,
            "PATCH":  logging.ERROR,
            "DELETE": logging.INFO
        }

    def open_file(self):
        """
        commence recording to the file set at construction.  If the file is already open (as it
        is at construction), it does nothing.  Normally, this is called after a close_file().
        """
        if not self._handler and self._recfile:
            self._handler = logging.FileHandler(self._recfile)
            self._handler.setFormatter(logging.Formatter(RECORD_FORMAT))
            self._handler.setLevel(logging.DEBUG)
            self.add_handler(self._handler)

    def close_file(self):
        """
        stop recording to the file set at construction and close it.  This does nothing if the 
        file is already closed.
        """
        if self._handler:
            self._handler.close()
            self.remove_handler(self._handler)
            self._handler = None

    def add_handler(self, handler, setfmt=True):
        """
        add a log handler to also receive request records in addition to the file set at 
        construction.
        :param logging.Handler handler:   the handler instance to add
        :param bool setfmt:               if True (default), the handler will set the message 
                                            format that the handler should apply to entries;
                                            if False, it will be assumed that the desired format
                                            is already set.
        """
        reclog = self.reclog
        if not reclog:
            self.reclog = logging.getLogger(self.svcname)
            self.reclog.propagate = 0
        if setfmt:
            handler.setFormatter(logging.Formatter(RECORD_FORMAT))
        self.reclog.addHandler(handler)

    def remove_handler(self, handler):
        """
        remove a handler added via add_handler()
        """
        if self.reclog:
            self.reclog.removeHandler(handler)

    def start_record(self, op, resource, qs=None, headers=None, body=None):
        """
        create, initialize, and return a record representing a web service request
        :param str op:        the HTTP method being invoked (e.g. "GET")
        :param str resource:  the URL path to the the resource being requested
        :param str qs:        the query string provided with the request
        :param list headers:  an array of (unparsed) header line that accompanied the request
        :param str body:      the message body sent with the request.  
        """
        return WebRequest(self, op, resource, headers, body, qs)

    def from_wsgi(self, wsgienv, readbody=False):
        """
        create a record given the request information in the environment dictionary provided 
        by the WSGI framework.  By default, the body is not read and inserted into the record; 
        however setting readbody to True will cause the input stream containing the body to be
        read in its entirety.
        """
        return WebRequest.from_wsgi(self, wsgienv, readbody)

    def record_from_wsgi(self, wsgienv, readbody=False):
        """
        immediately record a the request encapsulated in the environment dictionary provided 
        by the WSGI framework.  By default, the body is not read and, therefore, is not included
        in the record; however setting readbody to True will cause the input stream containing 
        the body to be read in its entirety.
        """
        self.from_wsgi(wsgienv, readbody).record()

    def record(self, request):
        """
        record a WebRequest
        """
        if request and self.reclog:
            log = self.reclog.getChild(request.op)
            lvl = self.levels.get(request.op, logging.DEBUG)
            if log.isEnabledFor(lvl):
                log.log(lvl, self._message_for(request))
        
    def _message_for(self, req):
        msg = req.resource
        if req.qs:
            msg += '?' + req.qs
        if req.headers:
            for h in req.headers:
                msg += "\n{0}".format(h)
        if req.body:
            msg += "\n-+-\n" + req.body + "\n"
        return msg
        
    def GET(self, resource, headers=None, qs=None):
        return self.start_record("GET", resource, qs, headers)

    def HEAD(self, resource, headers=None, qs=None):
        return self.start_record("HEAD", resource, qs, headers)

    def DELETE(self, resource, headers=None, qs=None):
        return self.start_record("DELETE", resource, qs, headers)

    def POST(self, resource, headers=None, qs=None, body=None):
        return self.start_record("POST", resource, qs, headers, body)

    def PUT(self, resource, headers=None, qs=None, body=None):
        return self.start_record("PUT", resource, qs, headers, body)

    def recGET(self, resource, headers=None, qs=None):
        self.GET(resource, headers, qs).record()

    def recHEAD(self, resource, headers=None, qs=None):
        self.HEAD(resource, headers, qs).record()

    def recDELETE(self, resource, headers=None, qs=None):
        self.DELETE(resource, headers, qs).record()

    def recPUT(self, resource, headers=None, qs=None, body=None):
        self.PUT(resource, headers, qs, body).record()

    def recPOST(self, resource, headers=None, qs=None, body=None):
        self.POST(resource, headers, qs, body).record()


class RequestLogParser(object):
    """
    a parser that creates replayable request records from a logfile
    """

    def __init__(self, recordfile):
        """
        Instantiate the parser for a given record log file
        """
        if not os.path.exists(recordfile):
            raise IOError("File not found: " + recordfile)
        self._recfile = recordfile

    class _byrecord(object):
        def __init__(self, fd):
            self.fd = fd
            self._nxt = None

        def peek(self):
            return self._nxt

        def records(self):
            "skip to the next record start"

            while True:
                line = None
                if self._nxt:
                    line = self._nxt
                    self._nxt = None
                else:
                    for line in self.fd:
                        if line.startswith("=*="):
                            break
                        line = None

                if not line:
                    raise StopIteration()
                out = self.reclines(line)
                yield out

        def reclines(self, initline):
            "iterate through the lines in the current record"
            if initline:
                yield initline
            for line in self.fd:
                if line.startswith("=*="):
                    self._nxt = line
                    break
                yield line

    def _parse_record(self, recliter):
        out = None
        line = recliter.next()
        out = self._init_req(line)

        inbody = False
        for line in recliter:
            if line.startswith("-+-"):
                inbody = True
            elif inbody:
                out.add_body_text(line)
            else:
                out.add_header(line)

        return out

    def _init_req(self, initline):
        if not initline.startswith("=*="):
            raise RuntimeError("_parse_record(): starting at wrong position in data stream")

        parts = initline.strip().split()
        parts[3:4] = parts[3].split('.', 1)

        out = WebRequest(None, parts[4], " ".join(parts[5:]))
        out.time = " ".join(parts[1:3])
        out.service = parts[3]

        return out

    def count_records(self):
        """
        count and return the number of records in this file
        """
        nl = 0
        with open(self._recfile) as fd:
            byrec = self._byrecord(fd)
            for rec in byrec.records():
                nl += 1
        return nl

    def parse(self, start=0, count=-1):
        """
        parse records out of the file
        :param int start:  the position of the first record to emit.  The first record
                           is at position 0.  If negative, start that many records from 
                           the end of the file.  
        :param int count:  the maximum number of records to emit.  If less than 0, parse 
                           all records from the start position to the end of the file.
        :rtype list:  an array of WebRequest records
        """
        out = []
        if start < 0:
            total = self.count_records()
            start = total + start
        if start < 0 and count > 0 and start+count > 0:
            count += start
            start = 0
        if start < 0:
            return out

        with open(self._recfile) as fd:
            byrec = self._byrecord(fd)
            p = 0
            for rec in byrec.records():
                if count >= 0 and p-start >= count:
                    break
                if p >= start:
                    try:
                        out.append(self._parse_record(rec))
                    except Exception as ex:
                        raise
                        # pass  # log?
                p += 1

        return out

    def parse_last(self):
        out = self.parse(-1)
        if len(out) < 1:
            return None
        return out[-1]

    
                        
