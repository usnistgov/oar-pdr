"""
load Taxonomy records into the RMM's MongoDB database
"""
import json, os, sys

from .loader import (Loader, RecordIngestError, JSONEncodingError,
                     UpdateWarning, LoadLog)
from .loader import ValidationError, SchemaError, RefResolutionError

DEF_BASE_SCHEMA = "https://www.nist.gov/od/dm/simple-taxonomy/v1.0#"
DEF_SCHEMA = DEF_BASE_SCHEMA + "/definitions/Term"

COLLECTION_NAME="taxonomy"

class TaxonomyLoader(Loader):
    """
    a class for validating and loading the SDP taxonomy into the Mongo database.
    """

    def __init__(self, dburl, schemadir, onupdate='quiet', defschema=DEF_SCHEMA):
        """
        create the loader.  

        :param dburl  str:    the URL of MongoDB database in the form,
                              'mongodb://HOST:PORT/DBNAME' 
        :param schemadir str:  the path to a directory containing the JSON 
                            schemas needed to validate the input JSON data.
        :param onupdate:    a string or function that controls reactions to 
                            the need to update an existing record; see 
                            documentation for load_data().
        :param defschema str:  the URI for the schema to validated new records 
                               against by default. 
        """
        super(TaxonomyLoader, self).__init__(dburl, COLLECTION_NAME, schemadir)
        self._schema = defschema
        self.onupdate = onupdate

    def _mkloadlog(self):
        return LoadLog("Taxonomy Terms")

    def load_array(self, termdata, validate=True, results=None, id=None):
        if len(termdata) > 1:
            id = None
        for term in termdata:
            results = self.load_obj(term, validate, results, id)

        return results

    def load_obj(self, termdata, validate=True, results=None, id=None):
        if "vocab" in termdata:
            # a Taxonomy (containing many terms)
            if validate and self._val and "_schema" in termdata and \
               not termdata['_schema'].startswith(DEF_BASE_SCHEMA):
                # can't assume Taxonomy format; validate whole document;
                # this will raise an exception
                self.validate(termdata)
                validate = False

            return self.load_array(termdata['vocab'], validate, results, id)

        else:
            # assume we have a Term object
            if not results:
                results = self._mkloadlog()
            if 'parent' not in termdata:
                termdata['parent'] = ""
            try:
                key = { "term": termdata['term'], "parent": termdata['parent'] }
            except KeyError, ex:
                if id is None:
                    id = str({'term': '?'})
                return results.add(id,
                      RecordIngestError("Data is missing input key value, name"))
            if id is None:
                id = key    

            if 'label' not in termdata:
                termdata['label'] = termdata['term']    

            errs = None
            if validate:
                schemauri = termdata.get("_schema")
                if not schemauri:
                    schemauri = self._schema

                errs = self.validate(termdata, schemauri)
                if errs:
                    return results.add(id, errs)

            try:
                self.load_data(termdata, key, self.onupdate)
            except Exception, ex:
                errs = [ex]
            return results.add(id, errs)

    def load(self, termdata, validate=True, results=None, id=None):
        """
        load taxonomy terms from the given JSON data
        :param termdata (dict, list):  one of 3 types of JSON data to load: 
                            a Term object, an array of Term objects, 
                            or a Taxonomy object (containing vocab array or 
                            Terms).
        :param validate bool:   False if validation should be skipped before
                            loading; otherwise, loading will fail if the input
                            data is not valid.
        :param id:    a name to record results against in the returned LoadLog;
                      if not provided, the extracted key will be used as 
                      applicable.  
        """
        if hasattr(termdata, 'iteritems'):
            # JSON object
            return self.load_obj(termdata, validate, results, id)
        elif hasattr(termdata, '__getitem__'):
            # JSON array
            return self.load_array(termdata, validate, results, id)
        else:
            raise ValueError("TaxnomyLoader: input is not supported JSON data: "+
                             type(termdata))

    def load_from_file(self, filepath, validate=True, results=None):
        """
        load the field docuementation from a file containing the field JSON data.
        """
        with open(filepath) as fd:
            try:
                data = json.load(fd)
            except ValueError, ex:
                if not results:
                    results = self._mkloadlog()
                return results.add(filepath, [ JSONEncodingError(ex) ])

        return self.load(data, validate=validate, results=results, id=filepath)
