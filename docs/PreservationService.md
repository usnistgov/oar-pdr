# The Preservation Service

*Note:* _This needs to be revised for the MIDAS Mark III convention._

The Preservation Service is a service that operates inside the NIST
internal network.  Its general purpose to turn Submission Information
Packages (SIPs) into Archive Information Packages--or bags, ingest
their content into the data repository, and place the bags into
long-term storage.  The primary use case enables the preservation of
datasets created through the MIDAS system.  

The service is triggered through a web-based, REST interface
accessible only to authorized clients.  For data submitted through
MIDAS, MIDAS calls the service after the data has been reviewed and
approved for release.  This document describes the REST interface.

## Overview

The test preservation service has the following base URL:
```
   https://datapubtest.nist.gov/preserv/midas/
```
The test service uses the same URL but with the host,
`datapub.nist.gov`.  In general terms, the input parameter is the
MIDAS UUID for the dataset, and the main output data is the checksum
of the serialized bag that was produced.  In general, a client
interacts with the service asynchronously; however, for most data
submissions (having a sufficiently small size), a single synchronous
call to the service is sufficient for getting the bag's checksum.

Following the REST service pattern, different HTTP methods are used
for different types of interactions.  In each case, the UUID of the
dataset being preserved is appended to the base URL.  In particular:

* PUT is used to preserve a dataset for the first time.
* GET is used to get the status and results of the preservation request.
* PATCH is used to preserve an update to a dataset.

Success is indicated with an HTTP response code in the 200-299 range.
Errors are indicated by HTTP response code in the 400 range for client
errors and 500 for server errors.  Error responses will include a
header status message.  All responses, except those resulting from
server errors, will return JSON-formatted bodies.

When the preservation process is complete, one (usually) or more
zipped bag file containing the dataset's contents will have been
delivered to the "public" directory for replication to long-term
storage and the publicly-accessible S3 bucket.  Along side each bag
file will be a checksum file: having the same name as the bag but with
an additional `.sha256` extension appended, it contains the bag file's
SHA-256 hash.

<a name="details"></a>
## Service Interaction Workflow

<a name="PUT"></a>
### Preserving a Dataset for the First Time

When a MIDAS dataset has been reviewed for release, a user can trigger
its publication through the MIDAS interface.  MIDAS "delivers" the
data via the PUT method:

Method | PUT
-------|------------
URL    | <tt>https://datapubtest.nist.gov/preserv/midas/</tt>_UUID_
Input  | None
Output | JSON, status of preservation

The UUID implies a location on disk where the dataset can be found.
The response will be delayed up to a certain "timeout" limit.  If the
preservation is completed within that limit, the JSON response will
contain a full summary of the succesful bagging operation, including
the names and checksums of the bag files that were produced (see the
[GET section] below for highlights or the [JSON Response Format](#JSON)
for full details). 

Possible HTTP Response Codes

Code   | Name         | Condition 
-------|--------------|---------------
201    | Created      | Preservation was successfully initiated and completed.  The JSON response body will contain bag names and checksums, and the GET method is available for retrieving this same information later.  
202    | Accepted     | Preservation was successfully initiated but is still in progress.  The GET method can be used to poll the preservations progress and eventually recieve the names and checksums.
400    | Bad Request  | The input URL was badly formed and therefore not recognized.
403    | Forbidden    | Preservation was already requested for this UUID and either is in progress or has already complete; use GET to determine its status.  
404    | Not Found    | A dataset with the given UUID could not be found (in the review area).
410    | Gone         | Preservation for dataset with the given UUID was previously requested, but the information on the results is no longer available.  In other words, the information has "aged out" and been deleted.
500    | Server Error | An error occured on the server that is not due to the users input but is not recoverable.  A subsequent call via GET may return a 402 (Not Found) response.  

<a name="GET"></a>
### Checking the Status of the Preservation Process

After the initial PUT request has been made and accepted (and for a
limited time after it has completed), one can check on the status of
the preservation process:

Method | GET
-------|------------
URL    | <tt>https://datapubtest.nist.gov/preserv/midas/</tt>_UUID_
Input  | None
Output | JSON, status of preservation

The response is a JSON object describing
the current state.  The full schema of the object is described in a
section below (see [JSON Response Format](#JSON)); however, properties
include:

Property Name | JSON Type | Values and Meaning
--------------|-----------|--------------------
`status`      | string    | "in progress" (the preservation process is still in progress), "successful", "failed", "forgotten" (the preservation information has aged out), "not found" (the dataset submission does not exist), "ready" (submission exists but preservation has not yet been requested).
`message`     | string    | a printable description of the current status
`bagfiles`    | array of objects | a listing of the successfully created bag files

Each `bagfiles` element contains the following properties:

Property Name | JSON Type | Values and Meaning
--------------|-----------|--------------------
`name`        | string    | the name of a bag file
`sha256`      | string    | the SHA-256 hash of the bag file

Possible HTTP Response Codes

Code   | Name         | Condition 
-------|--------------|---------------
200    | OK           | The preservation status is known are returned in the JSON response body.
404    | Not Found    | A dataset submission with the given UUID does not appear to exist, or it exists but has PUT request has not yet been made on it.  In the later case, the `status` property in the JSON response will have a value of "ready".  
410    | Gone         | Preservation for dataset with the given UUID was previously requested, but the information on the results is no longer available.  In other words, the information has "aged out" and been deleted.
500    | Server Error | An error occured on the server that is not due to the users input but is not recoverable.

<a name="PATCH"></a>
### Preserve an Update to a Dataset

When the user uses MIDAS to update a dataset (its metadata and/or
member data files), the updates can be preserved with a call to the
PATCH method.

Method | PATCH
-------|------------
URL    | <tt>https://datapubtest.nist.gov/preserv/midas/</tt>_UUID_
Input  | None
Output | JSON, status of preservation

Like with PUT, the UUID implies a location on disk where the dataset
can be found.  The response will be delayed up to a certain "timeout"
limit.  If the preservation is completed within that limit, the JSON
response will contain a full summary of the succesful bagging
operation, including the names and checksums of the bag files that
were produced (see [JSON Response Format](#JSON) below for details).

The possible response codes are the same as for PUT (except that 409 Conflict
replaces 403 Forbidden).  

Code   | Name         | Condition 
-------|--------------|---------------
201    | Created      | Preservation was successfully initiated and completed.  The JSON response body will contain bag names and checksums, and the GET method is available for retrieving this same information later.  
202    | Accepted     | Preservation was successfully initiated but is still in progress.  The GET method can be used to poll the preservations progress and eventually recieve the names and checksums.
400    | Bad Request  | The input URL was badly formed and therefore not recognized.
404    | Not Found    | A dataset with the given UUID could not be found (in the review area).
409    | Conflict     | Preservation has yet to be requested for the first time, or another preservation request is already in progress; use GET to determine its status.  
410    | Gone         | Preservation for dataset with the given UUID was previously requested, but the information on the results is no longer available.  In other words, the information has "aged out" and been deleted.
500    | Server Error | An error occured on the server that is not due to the users input but is not recoverable.  A subsequent call via GET may return a 402 (Not Found) response.  

## JSON Response Format

Except in the event of a server error (HTTP status code, 500), all responses
will include a JSON-formatted body.  Specifically, the content will be a JSON
object with the following properties (with * indicating a field that
is always present): 

Property Name | JSON Type | Values and Meaning
--------------|-----------|--------------------
`id`          | string    | the requested UUID
`status`*     | string    | a controlled string indicating the status (see possible values below)
`message`*    | string    | a printable description of the current status
`bagfiles`    | array of objects | a listing of the successfully created bag files

Status values include:

Status value   | Meaning
---------------|-------------
"in progress"  | the preservation process is still in progress
"successful"   | preservation was requested and completed successfully
"failed"       | preservation was requested but failed to complete successfully
"forgotten"    | the preservation information is no longer available; e.g. has aged out and was deleted
"not found"    | the dataset submission does not exist
"ready"        | submission exists but preservation has not yet been requested.

Each `bagfiles` array element contains the following properties:

Property Name | JSON Type | Values and Meaning
--------------|-----------|--------------------
`name`*       | string    | the name of a bag file
`sha256`*     | string    | the SHA-256 hash of the bag file

