"""
load NERDm records into the RMM's MongoDB database
"""
import json, os, sys

from .loader import (Loader, RecordIngestError, JSONEncodingError,
                     UpdateWarning, LoadLog)
from .loader import ValidationError, SchemaError, RefResolutionError

DEF_BASE_SCHEMA = "https://www.nist.gov/od/dm/nerdm-schema/v0.1#"
DEF_SCHEMA = DEF_BASE_SCHEMA + "/definitions/Resource"

COLLECTION_NAME="record"

class NERDmLoader(Loader):
    """
    a class for validating and loading NERDm records into the Mongo database.
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
        super(NERDmLoader, self).__init__(dburl, COLLECTION_NAME, schemadir)
        self._schema = defschema
        self.onupdate = onupdate

    def load(self, resrec, validate=True, results=None, id=None):
        """
        load a NERDm resource record into the database
        :param resrec dict:   the resource JSON record to load
        :param validate bool:   False if validation should be skipped before
                            loading; otherwise, loading will fail if the input
                            data is not valid.
        """
        if not results:
            results = self._mkloadlog()

        try:
            key = { "@id": resrec['@id'] }
        except KeyError, ex:
            if id is None:
                id = str({'@id': '?'})
            return results.add(id,
                     RecordIngestError("Data is missing input key value, @id"))
        if id is None:
            id = key    

        errs = None
        if validate:
            schemauri = resrec.get("_schema")
            if not schemauri:
                schemauri = self._schema

            errs = self.validate(resrec, schemauri)
            if errs:
                return results.add(id, errs)

        try:
            self.load_data(resrec, key, self.onupdate)
        except Exception, ex:
            errs = [ex]
        return results.add(key, errs)

    def _mkloadlog(self):
        return LoadLog("NERDm resources")

    def load_from_file(self, filepath, validate=True, results=None):
        """
        load a NERDm resource record from a file (containing one resource)
        """
        with open(filepath) as fd:
            try:
                data = json.load(fd)
            except ValueError, ex:
                raise JSONEncodingError(ex)
        return self.load(data, validate=validate, results=results, id=filepath)

    def load_from_dir(self, dirpath, validate=True, results=None):
        """
        load all the records found in a directory.  This will attempt to load
        all files in the given directory with the extension, '.json'
        """
        for root, dirs, files in os.walk(dirpath):
            # don't look in .directorys
            for i in range(len(dirs)-1, -1, -1):
                if dirs[i].startswith('.'):
                    del dirs[i]

            for f in files:
                if f.startswith('.') or not f.endswith('.json'):
                    continue
                f = os.path.join(root, f) 
                results = self.load_from_file(f, validate, results)
                                                  
        if not results:
            results = self._mkloadlog()
            
        return results

