# NerdmModule

This directory provides support for handling NERDm metadata. This includes, in
particular, `NerdmRes`, an interface representing the NERDm metadata record
itself, and `MetadataService`, a service that retrieves the metadata record.

## The MetadataService Architecture

The `MetadataService` class is abstract, and the various implementing
subclasses use different techniques for retrieving the metadata record,
depending on the runtime mode.  A factory function, `createMetadataService()`,
detects the current mode and instantiates the appropriate implementation
class.  The different modes are intended to support the following runtime
scenarios: 

<dl>
  <dt> Browser-side only for development </dt>
  <dd> This is intended for rapid-cycle development (e.g. iterating on a
       component layout).  The application runs completely in the browser
       (i.e. without the benefit of server-side rending).  Data is retrieved
       directly by the browser-side app via a configured (RMM) service such as
       the production one running at data.nist.gov (see
       <a href="../config">../config</a> for a description of different
       configuration scenarios).  The application is started typically by
       executing <code>npm run start</code>.  The
       <code>RemoteWebMetadataService</code> provides this ability, and it is
       usually wrapped in a <code>CachingMetadataService</code> to cache the
       retrieved metadata in memory.
       </dd>

  <dt> Server-side rendering for development </dt>
  <dd> This mode is used with the developer wants to ensure that server-side
       rending is working properly.  The application runs both on the server
       and (then) in the browser and is initiated via the command,
       <code>npm run serve:ssr</code>.  In this setup, the server retrieves the
       metadata and transmits it to the browser by embedding it in the
       delivered HTML page using a `MetadataTransfer` instance (see next section).
       <p>
       The browser-side extracts the metadata via the <code>TransferMetadataService</code>.
       The server-side can retrieve the data from a running web service (like
       the browser did in the previous scenario above) or by reading record
       files from a directory on disk (via the <code>ServerDiskCacheMetadataService</code>).
       The latter is triggered setting an environment variable,
       <code>PDR_METADATA_DIR</code>, to the directory containing record files.  </dd>

  <dt> Production operation (under oar-docker) </dt>
  <dd> This mode runs just like the previous mode where the server is
       configured to retrieve data from the production metadata service (RMM).
       On the server, it is expected that the docker container that launches
       the server-side app will first retrieve the configuration from the
       config service and write it to a file on disk.  It sets the location of
       that file into the <code>PDR_CONFIG_FILE</code> environment variable (see
       <a href="../config">../config</a>).  Further, the container can override
       the base URL for the metadata service (to set it to a different endpoint
       in its private docker network) by setting the
       <code>PDR_METADATA_SVCEP</code>.  (This overridden value will not be
       shared with the client; see <a href="../config">../config</a>
       regarding providing configuration to the browser-side app.) 
</dl>

A `MetadataService` is provided to components via Angular's dependency
injection infrastructure and the
[`createMetadataService()`](nerdm.service.ts#L218); consult the function
implementation to see the exact details of how an `MetadataService`
implementation is chosen.  Support for the `PDR_METADATA_SVCEP` override is
handled in [`nerdm.module.ts`](nerdm.module.ts).  See [../config](../config)
for more information about how configuration is supported.

## `MetadataTransfer`: Delivering metadata to the browser-side app

In the production scenario, the server-side app is responsible for retreiving
the metadata record to be displayed.  If the requested record does not exist,
the server returns a 404 HTTP response.  (And if an internal failure occurs, it
should return 500.)  On successful retrieval, though, server delivers the
metadata to the browser-side app by embedding it as JSON in the HTML page
(within a `<script>` element).  The purpose of this is two-fold:

  1. It saves browser from having to retrieve the record itself from service,
     eliminating a possible failure mode, improving performance, and
     guaranteeing that the server and browser have the exact same information.

  2. It supports an emerging standard for metadata sharing in which non-browser
     clients can "scrape" the metadata from the web page.  (Google would be one
     key client.)

The `MetadataTransfer` class (and it related infrastructure) is responsible for
delivering the metadata from the server to the browser, and it is modeled on
Angular's `TransferState` support.  The reason `TransferState` itself is used
instead is that it does not embed the metadata in an interoperable way.  In
particular,

   * `TransferState` encodes all of the data being shared with the browser as a
     JSON object (in a `<script>` element), where each data item is given an
     internally assigned key.  Clients wishing to extract metadata are
     expecting a `<script>` element that only contains the metadata record
     encoded as a JSON-LD object.

   * `TransferState`, when encoding the JSON, HTML-escapes all of the quotes
     (i.e. with `&quot;`); this is also contrary to the expectations of
     interoperable clients.  

In the server-browser runtime mode (scenarios 2 and 3 in the previous section),
the server-side's `MetadataService` automatically engages a `MetadataTransfer`
instance that will inject the metadata into HTML page after the entire
component display has been rendered, just before delivering the completed HTML
document to the client.  Meanwhile, the `MetadataService` provided to the
browser-side app will draw its metadata from a `MetadataTransfer` instance that
has automatically extracted the metadata record from the HTML page.

Serialization is implemented in
[`metadatatransfer-server.module.ts`](metadatatransfer-server.module.ts), and 
deserialization is implemented in
[`metadatatransfer-browser.module.ts`](metadatatransfer-browser.module.ts).
Just like with the use of `TransferState`, the server-side application module,
`AppServerModule` imports `ServerMetadataTransferModule`, and the browser-side
imports `BrowserMetadataTransferModule`.


