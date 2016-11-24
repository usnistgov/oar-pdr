These are (hand-created) examples of records that are compliant with
the schemas provided in the parent directory.  They are:

* **ceramicsportal.json** -- The Ceramics Webbook, example of a NIST Portal
  * Resource Types:  Portal, SRD, PublishedDataResource
  * Features:
    * The Portal includes access several other registered collections;
      this record provides links to them as components (type: IncludedResource).

* **hitsc.json** -- The High-T Superconducting materials database, an
  example of a Database with custom search page
  * Resource Types:  Database, SRD, PublishedDataResource
  * Features:
    * includes reference to documentation (user manual); reference metadata
      indicates that this document is specifically documentation via a
      reference type (refType: isDocumentedBy).
    * Search page provided as a component (type: SearchPage, Tool)

* **janaf.json** -- JANAF Thermochemical Tables, an example of a data publicatoin
  * Resource Types:  DataPublication, SRD, PublishedDataResource
  * Features:
    * Includes full author list
    * Includes DOI
    * includes 2 references to documentation (refType: isDocumentedBy).
    * includes downloadable files as components (type DataFile); also has
      type Distribution, indicating that this file is available as a
      distribution in data.gov.



