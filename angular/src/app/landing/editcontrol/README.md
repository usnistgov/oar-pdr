# EditControlModule

This directory provides overall control over editing of the resource
metadata.  When the configuration parameter `editEnabled` is set to
true, the user will see included in the landing page view an edit
control bar featuring an "Edit" button to start the editing process.
During this process, changes made by the user are saved as part of a
"draft" version of the metadata and cached on the PDR server.  When
all changes are completed, the user commits all of their changes, and
the draft metadata replaces the original metadata.  

The editing process described above is managed via three main
components:
  * `EditControlBar` -- this is the visual component that contains the
    "Edit" and "Save" buttons (as well as a "Discard" button) used to
    start the editing process and then finish it.  
  * `MetadataUpdateService` -- when the user user makes a change to
    some portion of the metadata via some specialized editing widget,
    the widget saves its changes by sending them to this service.
  * `CustomizationService` -- this service is used by the
    `MetadataUpdateService` to send updates to the draft to the
    server.  It also provides service operations for obtaining editing
    authorization.

Other services and components play roles in the editing process which
are described in the sections below.  

## The Authentication/Authorization Process

This module interacts with an authentication server to authenticate
the user (and obtain identity information) and with a PDR
customization service to determine if the user is authorized to edit
the landing page metadata.  Both of these interactions are
encapsulated in the `AuthService` (from `auth.service.ts`).  The
process is initiated when the user clicks the "Edit" button (in the
`EditControlComponent`).

In order to edit metadata and save the changes with the remote
customization service, a `CustomizationService` instance is needed to
communicate with the customization service.  Updates to metadata sent
to the service must be accompanied by an authorization token; this token
represents a specific user's permission to edit a specific record, and
it is cached in the `CustomizationService`.  The `AuthService` is
responsible for obtaining the token, creating the
`CustomizationService` instance with the token inside, and injecting
the `CustomizationService` into the `MetadataUpdateService` which
editing components use to update metadata.

The `AuthService` obtains an authorization token with the following
process, triggered by the user's click of the "Edit" button, which in
turn calls the `AuthService` method, `authorizeEditing()`:

  1.  If the `AuthService` already has an authorization token, it is
      wrapped in a `CustomizationService` instance; editing is
      enabled.

  2.  Otherwise, the `AuthService` requests an authorization token by
      accessing the authorization endpoint of the customization
      service (`/_perm/`_resource-id_, where _resource-id_ is the
      identifier of the resource to be edited).  If the service knows
      the user's user-ID (via a session cookie), it will determine if
      the user has permission to edit the resource.  If so, the user
      identity information and a token is returned; if not, just the
      user identity info is returned.  If the user's identity is not
      known, no information is returned, indicating that the user
      needs to authenticate.

  3.  If the user-ID was not known, the authentication
      service is engaged to authenticate the user.  The browser is
      redirected to a customization service endpoint for
      authenticating the user (`/saml/login`); the URL of the current
      landing page is provided to that endpoint as the value of the
      `redirectTo` query parameter.

      The landing page URL itself will have a query parameter itself,
      `editmode=true`.

      The customization service's authentication endpoint will
      redirect to the institutional authentication service.

  4.  If the user is not authenticated to the authentication service,
      the user will eventually see a form or pop-up for entering their
      institutional credentials, and then the browser is then sent
      back to a customization service endpoint (`/saml/SSO`) which
      redirects back to the landing page (with `editmode=true`).  If
      the user is already authentication, redirection sends the
      browser back to the landing page without any user interaction.

  5.  When the browser returns to the landing page with the query
      parameter, `editmode=true`, step 2 above is repeated to obtain
      an authorization token.  If the authentication process was
      successful, the customization service will be able to return
      user identity information; if the user is allowed to edit, it
      will also return the token.  If the authentication process was
      _not_ successful _or_ an authorization token was _not_ returned,
      the landing page will abort the attempt to turn on editing and
      display a message to this effect.

## Updating and Propagating Metadata

Initially, the resource metadata is loaded into the landing page
application via the `MetadataService`, and it comes from the metadata
service.  The `LandingPageComponent` takes responsibility for
retrieving the resource metadata; it passes the metadata to its child
components via one-way data binding (and those components can send
metadata down to their children in the same way).  

When the user clicks on the "Edit" button, the
`EditControlComponent` (after authentication and authorization)
directs the `MetadataUpdateService` to replace the original data
with the draft metadata stored remotely in the customization service.
This is done via a two-way ("banana-in-a-box") binding to the
`EditControlComponent`.  The latter has accessto the draft metadata
via the `MetadataUpdateService`; when the draft metadata is received,
it is passed back up to the `LandingPageComponent` via the two-way
binding and replaces the version provided bythe `MetadataService`.


  


