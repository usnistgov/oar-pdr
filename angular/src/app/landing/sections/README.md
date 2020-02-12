A module for components that lay out the content of a resource landing page into sections.
Each section is handled by a different component (`resource*.component`), and the 
`LandingBody` (`../landingbody.component`) brings the sections together into 
the body of the landing page.  

The section components are:

`ResourceIdentityComponent`
> "Front matter" that identifies the resource (by title and PID), its type, authors and contact, and the primary literature article associated with the resource.

`ResourceDescriptionComponent`
> Summarizing information about the resource, including the deescription/abstract, additional discussion, subject keywords and applicable research topics. 

`ResourceDataComponent`
> Information and links for accessing the data associated with this resource. 

`ResourceRefsComponent`
> The reference list 

`ResourceMetadataComponent`
> Access and visualization of the resource metadata, including links for exporting the metadata in various formats and schemas.

