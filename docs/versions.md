# Identifiers and Version Tracking in the PDR

The NIST Public Data Repository (PDR) supports revision of resource
publicaitons after the initial publication.  Each edition is given a
sequential version to distinguish them.  So that the specific versions
can be referred to in a linked data context, versions are built into
the PDR's identifier conventions.  This document explains the version
and associated identifier conventions used by the PDR generally and
then explains how it is supported specifically in the publishing
pipelines.

## Version Conventions

In general, the PDR assigns a three-level numeric version of the form:

_X.Y.Z_

where _X_, _Y_, and _Z_ are each integers and reflect the levels
reflect the significance of the revision (analagous to the Semantic
Versioning, or SemVer, convention common to software release
versioning):

  _Z_ -- reflects an update to the publication's metadata only.  These
         changes usually affect content and formatting of the
         landing page.  For publications where the PDR houses the data
         files that make up the publication, content of the these
         files have not changed.

  _Y_ -- reflects a change in the data files that comprise the
         resource publication (as well as possibly the associated
         metadata).  This includes changes to previously
         published files, the addition of new files, or the removal
         files.  When this value is incremented, the _Z_ value is set
         to "0".  

  _Z_ -- reflects a major reissue of the resource including both
         file content and metadata.  Currently, this is incremented
         only upon special request by the author.  When it is incremented,
         the _Y_ and _Z_ values are each set to "0".  

The publishing pipelines in general will detect if the resource has
been published before.  If it has not, the initial version will be set
to "1.0.0".  As with the SemVer convention, the sequence of assigned
versions assigned to a resource reflect the time order that the
revisions were released.  The assigned version can be customized by
the author (usually by special request); this is usually done to match
the version conventions used by the author.  Customized versions,
however, must follow the PDR's sequencing convention.

The version string is stored in the NERDm metadata via its "version"
property.  In addition, the "releaseHistory" property lists brief
descriptions of all the versions that are part of the sequence of
revisions; each includes a comment briefly describing what changed.  

In some contexts, the version displayed to PDR visitors may only
display the _X_ and _Y_ fields.

## Resource Identifier Conventions

Each resource in the PDR is assigned an internal identifier with an
ARK format [1] with the form,

`ark:/`_ARKNAAN_/_CONV_-_LOCALID_

where,

  _ARKNAAN_ -- the ARK Naming Assigning Authority Number; for NIST,
               this is "88434".
  _PIPE_ -- is a publisher-unique namespace (often called a "shoulder")
               that reflect publishing pipeline that was used when the
               resource was first published.  Resource published
               through MIDAS have the form "mds_N_", where _N_ is the
               major version of the publishing pipeline.  (Within the
               PDR, this is often refered to as the "SIP type".)
  _LOCALID_ -- a local identifier assigned by the publishing
               pipeline.  Often this is a sequence number (e.g. "2303").

Once this PDR-ID is assigned, it does not change across the
different revisions and assigned versions.  If two resources have
different PDR-IDs they are treated as distinct in the PDR with
separate evolutions.  The authors, however, can declare ad hoc
relationships between them (like one deprecates another).

When this PDR-ID is resolved (e.g. to a landing page or to metadata),
it should resolve by default to the latest version of the resource.

### Version-tracking Identifiers

The PDR supports a related set of identifiers used to track and refer
to specific versions of the resource.  Generally, these are not seen
by casual users of the repository.

A version-specific identifier appends a suffix of ".vX_Y_Z" to the
general form described above.  It will resolve to to the "X.Y.Z"
version of the resource.  An example would be,
"ark:/88434/mds2-2303.v1_0_0".

The PDR supports a special type of collection called a "release
sequence".  This assembles all of the published versions of a resource
into a logical collection representing the release history of the
resource.  The identifier for this collection has a suffix of ".rel"
appended to the general ID form, as in "ark:/88434/mds2-2303.rel".
This identifier will resolve to a description of the release history
of the resource.

## Dates associated with Revisions

The resource publication's metadata includes several dates that assist
in tracking the evolution of the resource with in the repository.
These are as follows:

## Other Resource Identifers

The PDR assigns additional identifiers to resources.  Some of these
are exported external users via metadata; these include an EDI
identifier and (usually) a DOI.  Others, like the SIP and AIP
identifiers, are applied implicitly and are used internally only.  All
of these can be lexigraphically distinct but bear similarities by
convention.  

### Enterprise Data Inventory (EDI) Identifier

The EDI ID serves a purpose specific to US government agencies.  Each
agency is mandated to support an Enterpris Data Inventory that lists
metadata descriptions of the data holdings of the agency.  The
descriptions of data resources that are considered public are exported
to data.gov in the Project Open Data (POD) catalog format.  The EDI ID
is the identifier that is applied to the POD resource description
within the catalog.

At NIST, the EDI predates the PDR.  Initially, the EDI (via MIDAS)
assigned identifiers composed of a random 32-character string plus a
sequence number.  Subsequently, MIDAS adopted the use of PDR-compliant
ARK identifiers with the "mdsN" shoulder and a local id matching the
MIDAS-assigned sequence or "record" number
(e.g. "ark:/88434/mds2-2303").  The PDR uses the EDI-ID as the PDR-ID
when the resource if first published (via the MIDAS publishing
pipeline).  The EDI-ID is captured within the PDR's NERDm schema via
the "ediid" property.  

NIST policy for revisions mandates that when a revision updates a
previously published file (which would trigger an increment in the _Y_
version field in the PDR), the resource must be assigned a new
EDI ID. MIDAS implements this by assigning a new record number to the
record.  When this occurs the PDR ID is _not_ changed; thus, the the
PDR-ID and and EDI-ID will not be the same.

### The Digital Object Identifier (DOI)

The DOI is a globally unique and resolvable ID that used by external
users to cite a data publication.  In the PDR, not all resources are
guaranteed to have a DOI assigned; however, NIST policy now requires
all new publications to be assigned a DOI.  For historical reasons,
some resources do not have a DOI assigned.

Currently, PDR pipelines assign DOIs; though, this was formerly
handled by MIDAS.  As with the EDI-ID, NIST policy requires that
revisions involve changes in data files to be assigned a new DOI.  In
the MIDAS publishing pipeline, the PDR assigns a DOI that uses the
EDI's ARK shoulder-local-id combination as the DOI local ID (as in,
"doi:10.80443/mds2-2303").

The DOI is captured in the NERDm metadata via the "doi" property.

### The Submission Information Package (SIP) identifier

The SIP ID is an identifier used internally by a PDR publishing
pipeline to process a submission to the PDR for publication.  Its form
depends on the publishing pipeline; with MIDAS SIPs, it matched the
EDI-ID.  

### The Archive Information Package (AIP) identifier

The AIP ID is an identifier for locating preservation packages in
long-term storage.  While assigned by the publishing pipeline, it
plays a key role in the implementation of the distribution service.  

## Support for versions within NIST-specific Publlishing Pipelines

PDR Publishing pipelines are designed in general to support a specific
convention for Submission Information Packages (SIPs in the OAIS
repository model).  Different pipelines have different ID shoulders
associated with them.  

### MIDAS (mds)

The latest MIDAS publishing pipeline adheres to the so-called Mark III
conventions (which itself has been subject to some evolution),
characterized generally by the following:

  * MIDAS pushes metadata to the PDR as POD records via the
    /pdr/latest and /pdr/draft service endpoints.
  * The resources have a local id of the form "mds2-RECNUM", where
    RECNUM is the MIDAS record number.
  * On revsion, if the author (i.e. MIDAS user) updates a previously
    published file, MIDAS assigns it a new record number; the POD
    record sent to the PDR will include a "replaces" property giving
    the EDI-ID of the record the new one deprecates.
  * If the author opts for a PDR-generated home page, the landing page
    URL will be set to the form of "https://data.nist.gov/od/id/MIDAS_ID"
  * A file's download URL will be set to the form of
    "https://data.nist.gov/od/ds/MIDAS_ID" 

Note that under a major revision that changes the EDI-ID, the URLs to
the resource will change, too.

The PDR-MIDAS pipeline has three pieces to it:
  * MIDAS, the user interface for creating publications and entering
    metadata
  * the PDR Publishing Service, used by MIDAS to preview and customize
    landing pages (via the /pdr/latest and /pdr/draft endpoints)
  * the PDR Preservation Service, used to push a completed publication
    to the PDR.

As the publication author uses MIDAS to create a data publication,
MIDAS feeds thd metadata to the PDR Publishing Service.  This service
uses this metadata to create and update a draft preservation bag that
contains only metadata.  It uses the EDI-ID along with the associated
"replaces" property to determine if the resource has been published
before.  If it has, a metadata bag is created using the previous
publication's head bag as a starting point and the POD metadata is
merged into it; if not, a prototype is created based on just the POD
metadata.  

If the resource has not been published before, a PDR-ID is assigned to
the SIP that matches the ARK-based EDI-ID, and the version is
initialized to "1.0.0".  It uses the follow process to set the draft
metadata bag and set the IDs and version:

  * the PDR determines the ID of the previously published
    edition of the resource.  If the POD record has a "replaces" property,
    that is taken as the EDI-ID of the previous edition; otherwise,
    the POD's "identifier" property is taken as the previous EDI-ID.
  * From the previous EDI-ID, the AIP-ID is determined.  It uses the
    PDR's distribution service is used to find the last published head
    bag for that AIP-ID.
  * If a previous bag is not found, the resource is a first time publication:
      * a draft bag created solely on the input POD metadata
      * the version is set to "1.0.0"
      * the PDR-ID is set to the EDI-ID
  * If the previous bag does exist, the resource is a revision:
      * that bag is unpacked and used as the starting point for a
        revision metadata bag
      * the PDR-ID is retained from the previous publication
      * the EDI-ID is set to that of POD record's "identifier"
      * the "replaces" property is copied to the new resources
        metadata
      * the version is set to the value of the previous publication
        but with "+ (edit)" as indicator that the final version string
        has not been determined, yet.
        
Once a draft metadata bag is established in the PDR's publishing
space, it is just updated with new metadata from MIDAS until it is
ready to publish.

The preservation service is responsible for converting a draft
metadata bag into a final bag ready for preservation.  To trigger
preservation, MIDAS sends the final POD to the preservation service.
The PDR that metadata into the metadata bag and finalizes it for
preservation.  In particular, any data files provided by MIDAS are
added to the bag.  A revision will be considered a major change
(requiring an increment to the version's _Y_ field) if either:
  * the bag contains new, deleted, or revised data files, or
  * the bag was given a new EDI-ID
Based on this assessment the version property is replace with an
appropriately incremented version string.  The "releaseHistory"
property will be extended to describe the new version. 

Also part of the finalization is an update to key dates described
above:
  * if the resource is being published for the first time, the
    "firstIssued" date is set to the current time.
  * if the resource the _X_ or _Y_ version fields was incremented,
    the "revised" date is set to the current time.
  * the "annotated" date is set to the current time.

The preservation service is also responsible for issuing a DOI or
updating the associated metadata.  On the initial publication, the DOI
is set with a local ID comprised of the PDR-ID's shoulder-local-id
combination (as in, "doi:10.80443/mds2-2303").  If on revision the
EDI-ID has changed, the NERDm metadata will include a new DOI-ID in
its "doi" property; this will cause a new DOI to be issued for the
record.  

### Programmatic Data Publishing (pdp)




   
