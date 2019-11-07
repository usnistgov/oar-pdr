# EditControlModule

This directory provides overall control over editing the resource
metadata.  When the configuration parameter `editEnabled` is set to
true, the user will see included in the landing page view an edit
control bar featuring an "Edit" button to start the editing process.
During this process, changes made by the user are save as part of a
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
    server.  It also provides service operations for obtaining editign
    authorization.

