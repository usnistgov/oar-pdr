"""
load field documentation into the RMM's MongoDB database

The RMM's MongoDB database contains NERDm records for searching via the SDP.
The fields collection contains information about the NERDm fields that the 
SDP can use to dynamically build an interface that includes helpful information
about the fields.  This module is responsible for loading field information 
into the database.  
"""
import json

from .loader import Loader, RecordIngestError, UpdateWarning, LoadLog
from .loader import ValidationError, SchemaError, RefResolutionError

DEF_BASE_SCHEMA = "https://www.nist.gov/od/dm/field-help/v0.1#"
DEF_SCHEMA = DEF_BASE_SCHEMA + "/definitions/FieldInfo"

class FieldLoader(Loader):
    """
    a class for validating and loading field documentation into the Mongo 
    database.
    """

    def __init__(self, dbhost, dbname, schemadir, defschema=DEF_SCHEMA):
        """
        create the loader.  

        :param dbhost str:     the hostname and port number to use to access 
                               the MongoDB database in the form HOST:PORT.
        :param dbname str:     the MongoDB database name to load data into
        :param schemadir str:  the path to a directory containing the JSON 
                            schemas needed to validate the input JSON data.
        """
        super(FieldLoader, self).__init__(dbhost, dbname, "fields", schemadir)
        self._schema = defschema

    def load(self, fielddata, validate=True, results=None):
        """
        load the field documentation from the given JSON data
        :param fielddata (dict, list):  one of 3 types of JSON data to load: 
                            a FieldInfo object, an array of  FieldInfo objects, 
                            or a Fields object (containing fields array).
        :param validate bool:   False if validation should be skipped before
                            loading; otherwise, loading will fail if the input
                            data is not valid.
        """
        if hasattr(fielddata, 'iteritems'):
            # JSON object
            return self.load_obj(fielddata, validate, results)
        elif hasattr(fielddata, '__getitem__'):
            # JSON array
            return self.load_array(fielddata, validate, results)
        else:
            raise ValueError("FieldLoader: input is not supported JSON data: "+
                             type(fielddata))

    def load_obj(self, fielddata, validate=True, results=None):
        if "fields" in fielddata:
            # a wrapped list of FieldInfo objects
            if validate and self._val and "_schema" in fielddata and \
               not fielddata['_schema'].startswith(DEF_BASE_SCHEMA):
                # can't assume FieldInfo format; validate whole document;
                # this will raise an exception
                self.validate(fielddata)
                validate = False

            return self.load_array(fielddata['fields'], validate, results)

        else:
            # assume we have a FieldInfo object
            if not results:
                results = LoadLog("NERDm fields")

            try:
                key = { "name": fielddata['name'] }
            except KeyError, ex:
                return results.add({'name': '?'},
                      RecordIngestError("Data is missing input key value, name"))

            errs = None
            if validate:
                schemauri = fielddata.get("_schema")
                if not schemauri:
                    schemauri = DEF_SCHEMA

                errs = self.validate(fielddata, schemauri)
                if errs:
                    return results.add(key, errs)

            try:
                self.load_data(fielddata, key)
            except Exception, ex:
                errs = [ex]
            return results.add(key, errs)

    def load_array(self, fielddata, validate=True, results=None):
        probs = []
        for fd in fielddata:
            results = self.load_obj(fd, validate, results)

        return results

    def load_from_file(self, filepath, validate=True, results=None):
        """
        load the field docuementation from a file containing the field JSON data.
        """
        with open(filepath) as fd:
            try:
                data = json.load(fd)
            except ValueError, ex:
                raise JSONEncodingError(ex)
        return self.load(data, validate=validate, results=results)
