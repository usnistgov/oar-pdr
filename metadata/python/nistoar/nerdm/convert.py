"""
Classes and functions for converting from and to the NERDm schema
"""
import os, json
from .. import jq

class PODds2Res(object):
    """
    a transformation engine for converting POD Dataset records to NERDm
    resource records.
    """

    def __init__(self, jqlibdir):
        """
        create the converter

        :param jqlibdir str:   path to the directory containing the nerdm jq
                               modules
        """
        self.jqt = jq.Jq('nerdm::podds2resource', jqlibdir, ["pod2nerdm:nerdm"])

    def convert(self, podds, id):
        """
        convert JSON-encoded data to a resource object

        :param podds str:   a string containing the JSON-formatted input POD 
                            Dataset record
        :param id str:      The identifier to assign to the output NERDm resource
        """
        return self.jqt.transform(podds, {"id": id})

    def convert_data(self, podds, id):
        """
        convert parsed POD record data to a resource object

        :param podds str:   a string containing the JSON-formatted input POD 
                            Dataset record
        :param id str:      The identifier to assign to the output NERDm resource
        """
        return self.jqt.transform(json.dumps(podds), {"id": id})

    def convert_file(self, poddsfile, id):
        """
        convert parsed POD record data to a resource object

        :param podds str:   a string containing the JSON-formatted input POD 
                            Dataset record
        :param id str:      The identifier to assign to the output NERDm resource
        """
        return self.jqt.transform_file(poddsfile, {"id": id})

