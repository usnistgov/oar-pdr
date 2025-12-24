"""
This module sets important constants (like schema URIs) for handling NERDm 
data to make them available from Python.
"""
core_schema_base = "https://data.nist.gov/od/dm/nerdm-schema/"

schema_versions = ["v0.7", "v0.6", "v0.5", "v0.4", "v0.3", "v0.2", "v0.1"]
core_ver = schema_versions[0]
pub_ver  = schema_versions[0]
bib_ver  = schema_versions[0]
rls_ver  = schema_versions[-3]
exp_ver  = schema_versions[-1]
sip_ver  = schema_versions[-1]
agg_ver  = schema_versions[-2]

def core_schema_uri_for(version):
    """
    return the schema URI for the requested version of the Core NERDm schema
    @raises ValueError   if the given version is not a recognized version
    """
    return schema_uri_for(core_schema_base, version)

def pub_schema_uri_for(version):
    """
    return the schema URI for the requested version of the Core NERDm schema
    @raises ValueError   if the given version is not a recognized version
    """
    return schema_uri_for(core_schema_base+"pub/", version)

def bib_schema_uri_for(version):
    """
    return the schema URI for the requested version of the Core NERDm schema
    @raises ValueError   if the given version is not a recognized version
    """
    return schema_uri_for(core_schema_base+"bib/", version)

def schema_uri_for(schema_base, version):
    """
    return the schema URI for the requested version of the Core NERDm schema
    @raises ValueError   if the given version is not a recognized version
    """
    if version in schema_versions:
        return schema_base+version
    vers = "v" + version
    if vers in schema_versions:
        return schema_base+vers

    raise ValueError("Not an recognized NERDm version: " + version)

CORE_SCHEMA_URI = core_schema_uri_for(core_ver)
PUB_SCHEMA_URI = pub_schema_uri_for(pub_ver)
BIB_SCHEMA_URI = bib_schema_uri_for(bib_ver)
RLS_SCHEMA_URI = schema_uri_for(core_schema_base+"rls/", rls_ver)
EXP_SCHEMA_URI = schema_uri_for(core_schema_base+"exp/", exp_ver)
SIP_SCHEMA_URI = schema_uri_for(core_schema_base+"sip/", sip_ver)
AGG_SCHEMA_URI = schema_uri_for(core_schema_base+"agg/", agg_ver)

TAXONOMY_VOCAB_BASE_URI = "https://data.nist.gov/od/dm/nist-themes/"
TAXONOMY_VOCAB_INIT_URI = "https://www.nist.gov/od/dm/nist-themes/v1.0"

taxon_versions = ["v1.1", "v1.0"]

def taxon_uri_for(taxon_base, version):
    """
    return the schema URI for the requested version of the Core NERDm schema
    @raises ValueError   if the given version is not a recognized version
    """
    if version in taxon_versions:
        return taxon_base+version
    vers = "v" + version
    if vers in taxon_versions:
        return taxon_base+vers

    raise ValueError("Not an recognized NERDm version: " + version)

TAXONOMY_VOCAB_URI = taxon_uri_for(TAXONOMY_VOCAB_BASE_URI, taxon_versions[0])
