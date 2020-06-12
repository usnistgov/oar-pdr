# FrameModule

This module provides components that make up the "frame" of the landing
page--namely, the header and the footer.  Also included is a generic
message bar for displaying messages for the user.  

## HeadbarComponent

Features:
 * Set as a black bar for the top of the page
 * NIST PDR logo that links to the PDR home page (currently the SDP)
 * PDR-wide links:
   * About page
   * Search page (the SDP)
   * User's Datacart
 * Labels indicating the version and status of the PDR
   * this uses the badge style from bootstrap

## FootbarComponent

Features:
 * Set as a (thick) black bar for the bottom of the page
 * Includes standard NIST footer content (links to agency web site, etc.)

## MessageBarComponent and UserMessageService

These two classes work together to capture and display application
messages to the user:  components or services can send messages for
display by sending it through a UserMessageService instance; the
MessageBarComponent connected to the UserMessageService will display
it.

A message has a "class" category attached to it that depends on how it
was submitted (i.e. via `warn()`, `inform()`, `syserror()`, etc.)  The
display of the message will differ depending on the associated
customized style.


 
