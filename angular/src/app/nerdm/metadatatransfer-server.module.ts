/** 
 * Support for MetadataTransfer on the server side
 *
 * This implementation is based on the angular ServerTransferStateModule (provided
 * via the open license at https://angular.io/license). 
 */
import { NgModule, InjectionToken } from '@angular/core';
import { DOCUMENT } from '@angular/platform-browser';
import { BEFORE_APP_SERIALIZED } from '@angular/platform-server';

import { MetadataTransfer } from './nerdm';

const escapeHTMLchars = function(text : string, doc : Document) : string {
    let div = doc.createElement('div');
    div.appendChild(doc.createTextNode(text));
    return div.innerHTML.replace(/"/g,'&quot;').replace(/'/g,"&apos;");
}

const convertNerdmSchema = function(textContent: string) : string{
    let inputObject = JSON.parse(textContent);
    let returnSchemaObject: any = {};

    returnSchemaObject['@context'] = "https://schema.org";
    returnSchemaObject['@type'] = "WebSite";

    if(inputObject['ediid'])
        returnSchemaObject['url'] = "https://data.nist.org/od/id/" + inputObject['ediid'];


    if(inputObject['title'])
        returnSchemaObject['name'] = inputObject['title'];

    returnSchemaObject['sameAs'] = "NIST Public Data Repository";

    if(inputObject['description'])
        returnSchemaObject['description'] = inputObject['description'];

    returnSchemaObject['about'] = "?";
    returnSchemaObject['abstract'] = "?";
    returnSchemaObject['dateCreated'] = new Date();
    returnSchemaObject['conditionsOfAccess'] = "Open to public";

    if(inputObject['keyword'])
        returnSchemaObject['keywords'] = inputObject['keyword'].toString();

    return JSON.stringify(returnSchemaObject, null, 2);
}

/**
 * the factory function for inserting metadata into script elements in the 
 * document DOM.  
 *
 * Each metadata record stored in the MetadataTransfer will be serialized into 
 * its own script element and inserted into the document DOM.  The id for the 
 * element will be set to the metadata's label.  The type attribute will be some
 * form of "application/json", depending on the content:  if the record contains
 * a "@context" property, it will be set to "application/ld+json".  
 * 
 * This implementation inserts the script elements as the first children of 
 * the body element. 
 *
 * @param doc    the document DOM to insert the metadata into
 * @param mdtrx  the MetadataTransfer containing the metadata to serialize into 
 *                 the document.
 * @return function -- a no-arg function that will actually write out the data 
 *                 synchronously.
 */
export function serializeMetadataTransferFactory(doc : Document, mdtrx : MetadataTransfer) {
    return () => {
        let insertPoint = doc.body.firstElementChild;
        mdtrx.labels().forEach((label) => {
            let data = mdtrx.get(label);
            if (data == null)
                data = null;

            let script = doc.createElement('script');
            script.id = escapeHTMLchars(label, doc);
            console.log("Embedding metadata with id='"+script.id+"'");
            let type = "application/json";
            if (data && data.hasOwnProperty("@context"))
                type = "application/ld+json";
            script.setAttribute("type", type);
            // script.textContent = mdtrx.serialize(label);
            script.textContent = convertNerdmSchema(mdtrx.serialize(label));
            console.log('script.textContent', script.textContent);
            doc.body.insertBefore(script, insertPoint)
        });
    };
}

/**
 * a module for serializing the contents of an app's MetadataTransfer singleton
 *
 * This is modeled after the ServerTransferStateModule
 */
@NgModule({
    providers: [
        MetadataTransfer,
        {
            provide: BEFORE_APP_SERIALIZED,
            useFactory: serializeMetadataTransferFactory,
            deps: [DOCUMENT, MetadataTransfer],
            multi: true
        }
    ]
})
export class ServerMetadataTransferModule { }

export { MetadataTransfer };
