# jq conversion library from NIST-PDL-POD to NERDm schemas
#
# To convert a single POD Dataset document, execute the following:
#
#   jq -L $JQLIB --arg id ID \
#      'import "pod2nerdm" as nerdm; .|nerdm::podds2resource' DSFILE
#
# Here, JQLIB is the directory containing this library, ID is the identifier
# that should be assigned for that record, and DSFILE is a file containing a
# POD Dataset object.
#
# To convert the full PDL catalog into an array of NERDm records, execute:
#
#   jq -L $JQLIB --argjson id null \
#      'import "pod2nerdm" as nerdm; .|nerdm::podcat2resources' CATFILE
#      
# Here, CATFILE is the POD catalog file.  (In this example, the output records
# are all given a null identifier.)


# the base NERDm JSON schema namespace
#
def nerdm_schema:  "https://www.nist.gov/od/dm/nerdm-schema/v0.1#";

# the base NERDm JSON schema namespace
#
def nerdm_pub_schema:  "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#";

# the NERDm context location
#
def nerdm_context: "https://www.nist.gov/od/dm/nerdm-pub-context.jsonld";

# where the Datacite Document Reference types are defined
#
def dciteRefType: nerdm_schema + "/definitions/DCiteDocumentReference";

# the resource identifier provided on the command line
#
def resid:  if $id then $id else null end;

# conversion for a POD-to-NERDm reference node
#
# Input: a string containing the reference URL
# Output: a DCiteDocumentReference object
#
def cvtref:  {
    "@type": "deo:BibliographicReference",
    "refType": "IsReferencedBy",
    "location": .,
    "$extensionSchemas": [ dciteRefType ]
};

# conversion for a POD-to-NERDm distribution node.  A distribution gets converted
# to a DataFile component
#
# Input: a Distribution object
# Output: a Component object with an DataFile type given as @type
#
def dist2download: 
    .["@type"] = [ "nrdp:DataFile", "dcat:Distribution" ] |
    .["$extensionSchemas"] = [ "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile" ] 
;

# conversion for a POD-to-NERDm distribution node.  A distribution gets converted
# to a Hidden component that is not intended for external use.  (Such nodes
# exist to preserve information for conversion back into POD.)
#
# Input: a Distribution object
# Output: a Component object with an Hidden type given as @type
#
def dist2hidden:
    .["@type"] = [ "nrd:Hidden", "dcat:Distribution" ] 
;

# conversion for a POD-to-NERDm distribution node.  A distribution gets converted
# to an Inaccessible component.  This is for distributions that have neither an
# accessURL nor a downloadURL.  
#
# Input: a Distribution object
# Output: a Component object with an Inaccessible type given as @type
#
def dist2inaccess:
    .["@type"] = [ "nrd:Inaccessible", "dcat:Distribution" ]
;

# conversion for a POD-to-NERDm distribution node.  A distribution gets converted
# to a generic AccessPage component.  
#
# Input: a Distribution object
# Output: a Component object with an AccessPage type given as @type
#
def dist2accesspage:
    .["@type"] = [ "nrd:AccessPage", "dcat:Distribution" ]
;

# conversion for a POD-to-NERDm distribution node.  A distribution gets converted
# to a component of particular types depending on the input data.  See other
# dist2* macros
#
# Input: a Distribution object
# Output: a Component object with the detected types given in @type
#
def dist2comp: 
    if .downloadURL then
        dist2download
    else if .accessURL then
        if (.accessURL | test("doi.org")) then
          dist2hidden
        else
          dist2accesspage
        end
      else
        dist2inaccess
      end
    end
;

# return the DOI stored in the accessURL, if it exists.  null is returned, if
# none is found.
#
# Input: a Distribution object
# Output:  string: A DOI in in the form of "doi:..."
#
def doiFromDist:
    (map(select(.accessURL)| .accessURL | scan("https?://.*doi\\.org/.*")) | .[0]) as $auri |
    if $auri then ($auri | sub("https?://.*doi.org/"; "doi:")) else null end
;

# Converts an entire POD Dataset node to a NERDm Resource node
#
def podds2resource:
    {
        "@context": nerdm_context,
        "$schema": nerdm_schema,
        "$extensionSchemas": [ nerdm_pub_schema + "/definitions/PublishedDataResource" ],
        "@type": [ "nrdp:PublishedDataResource" ],
        "@id": resid,
        "doi": (.distribution + []) | doiFromDist,
        title,
        contactPoint,
        issued,
        modified,

        ediid: .identifier,
        landingPage,
        
        description: [ .description ],
        keyword,
        theme,

        references,
        accessLevel,
        license,
        components: .distribution,
        publisher,
        language,
        bureauCode,
        programCode
    } |
    if .references then .references = (.references | map(cvtref)) else del(.references) end |
    if .components then .components = (.components | map(dist2comp)) else del(.components) end |
    if .doi then . else del(.doi) end |
    if .theme then . else del(.theme) end |
    if .issued then . else del(.issued) end 
;

# Converts an entire POD Catalog to an array of NERDm Resource nodes
#
def podcat2resources:
    . | .dataset | map(podds2resource)
;



