# ConfigModule

This module provides the application configuratoin infrastructure.

## The Configuration Architecture

Components are provided configuration data via an [`AppConfig`](config.ts)
class via Angular's dependency injection mechanism.  Configuration values can
be retrieved directly from the instance's properties
(e.g. `cfg.locations.distService`) or via its `get()` method
(e.g. `cfg.get("location.distService")`).  The latter allows for the caller to
set a default value if one is not provided in the configuration
(e.g. `cfg.get("location.distService", "/od/ds")`).

An `AppConfig` instance is created via a `ConfigService` instance.  The
[`ConfigService`](config.service.tst) class itself is abstract, and the
various implementing sublcasses use different techniques for loading the
configuration data, depending on the runtime mode.  A factory function,
`newConfigService()`, detects the current mode and instantiates the
appropriate implementation class.  The different modes are intended to support
the following runtime scenarios:

<dl>
  <dt> Browser-side only for development </dt>
  <dd> This is intended for rapid-cycle development (e.g. iterating on a
       component layout).  The application runs completely in the browser
       (i.e. without the benefit of server-side rending), and it is
       typically launched by executing <code>npm run start</code>.  Using the
       <code>AngularEnvironmentConfigService</code> implementation, the
       configuration data is drawn from the <code>config</code> object hard-coded
       into the
       <code><a href="../../environments/environment.ts">environments/environment.ts</a></code>.
       The developer is free to edit this file for development and
       testing purposes but normally would not check those changes in.
       </dd>

  <dt> Server-side rendering for development </dt>
  <dd> This mode is used with the developer wants to ensure that server-side
       rending is working properly.  The application runs both on the server
       and (then) in the browser and is initiated via the command,
       <code>npm run serve:ssr</code>.  In this setup, the server gets its
       configuration data from the `config` object hard-coded into
       <code><a href="../../environments/environment.prod.ts">environments/environment.prod.ts</a></code>
       at build-time (i.e. before running, <code>npm run build:ssr</code>).  This
       configuration data is delivered to browser-side app via
       Angular's <code>TransferState</code> mechanism.
       <p>
       Like with the previous scenario, the developer is free to edit
       the <code>environment.prod.ts</code> file (but not check it in); however,
       the developer might find using the <code>PDR_CONFIG_FILE</code>, described
       in the next scenario, just as convenient.  </dd>

  <dt> Production operation (under oar-docker) </dt>
  <dd> This mode is similar to the previous node where the server-side
       app delivers the configuration data to the browser via
       <code>TransferState</code> but with one important difference.  On the
       server, the docker container that launches the server-side app
       will first retrieve the configuration from the config service
       and write it to a file on disk.  It sets the location of that
       file into the <code>PDR_CONFIG_FILE</code> environment variable.  This
       will trigger the `ConfigService` factory function in the
       server-side app to instantiate a <code>ServerFileConfigService</code>
       instance, which loads the configuration from that file.  </dd>
</dl>

The factory function, [`newConfigService()`](config.service.ts#L251),
automatically determines the runtime mode and creates the appropriate
`ConfigService` implementation.  Three configuration paramters can help the
developer understand what mode has been engaged and where the configuration
data came from.  Two are set by the `ConfigService` itself, and one comes only
from the configuration source file:

<dl>
   <dt> <code>source</code> </dt>
   <dd> The value is a label indicating the origin of the configuration data;
        the value is hard-coded into the <code>ConfigService</code>
        implementation.  The currently defined labels are:
        <ul>
           <li> <code>server-file</code> (from
                <code>ServerFileConfigService</code>) -- the data was read in
                from a file on the server's disk.  This only occurs in the
                server-side app. </li>
           <li> <code>transfer-state</code> (from
                <code>TransferStateConfigService</code>) -- the data was read
                in from the <code>TransferState</code>.  This only occurs in the 
                browser-side app. </li>
           <li> <code>angular-env</code> (from
                <code>AngularEnvironmentConfigService</code>) -- the data was
                read in from Angular's environment module.  This can occur 
                either in the server-side or browser-side app, depending on the
                runtime mode. </li>
        </ul> </dd>

   <dt> <code>mode</code> </dt>
   <dd> The value is usually to either "dev" or "prod" by the
        <code>ConfigService</code>, but the value can be set explicitly in the
        configuration source file.  The semantics of the possible values is
        intended to be the same as the the Angular environments labels.
        Typically, the value will be set to "dev" if the configuration came from
        <code><a href="../../environments/environment.ts">environments/environment.ts</a></code>.
        </dd> 

   <dt> <code>status</code> </dt>
   <dd> This value is <em>not</em> set by the <code>ConfigService</code>;
        rather, it is set explicitly in the configuration source file.  This
        value, if set, will be displayed (as a "badge") in the header of the
        landing page and serves as a further indicator of the runtime context
        which can be customized by the developer.  The default value set in the
        <code><a href="../../environments/environment.ts">environement.ts</a></code>
        file is "Dev Version", reflecting the developer's rapid development-cycle
        mode.  "Dev-Server Version" indicates a development mode in which the
        configuration was set on the server and successfully delivered to the
        browser.  "Misconfigured Version" is intended as a signal that the
        value was read from the default 
        <code><a href="../../environments/environment.prod.ts">environement.prod.ts</a></code>
        file is rather than from, say, the configuration service.  </dd>
</dl>

## AppConfig

An injectable class for delivering configuration data.  The expected parameter
names are set by being an extension of the LPSConfig interface where the
parameters are defined (both syntactically and semantically).

## ConfigService

The abstract base class for implementations that load configuration data from
different possible sources.


