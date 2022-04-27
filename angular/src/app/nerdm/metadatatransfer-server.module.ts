/** 
 * Support for MetadataTransfer on the server side
 *
 * This implementation is based on the angular ServerTransferStateModule (provided
 * via the open license at https://angular.io/license). 
 */
import { NgModule, InjectionToken } from '@angular/core';
import { DOCUMENT } from "@angular/common";
import { BEFORE_APP_SERIALIZED } from '@angular/platform-server';

import { NerdmRes, MetadataTransfer } from './nerdm';
import { NERDResource } from '../nerdm/nerdm';
import { NerdmConversionService, SchemaLabel, MetadataEnvelope } from '../nerdm/nerdmconversion.service';

const escapeHTMLchars = function(text : string, doc : Document) : string {
    let div = doc.createElement('div');
    div.appendChild(doc.createTextNode(text));
    return div.innerHTML.replace(/"/g,'&quot;').replace(/'/g,"&apos;");
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
export function serializeMetadataTransferFactory(doc : Document, mdtrx : MetadataTransfer,
                                                 converter : NerdmConversionService = null)
{
    return () => {
        let mdclass = 'structured-data ';

        mdtrx.labels().forEach((id) => {
            let data = mdtrx.get(id) as NerdmRes;
            if (data == null)
                return;

            // Creating the script for Nerdm data transfer
            let script = doc.createElement('script');
            script.id = escapeHTMLchars(SchemaLabel.NERDM_RESOURCE+':'+id, doc);
            console.log("Embedding metadata with id='"+script.id+"'");
            let type = "application/json";
            if (data && data.hasOwnProperty("@context"))
                type = "application/ld+json";

            script.setAttribute("type", type);
            script.setAttribute("class", mdclass + SchemaLabel.NERDM_RESOURCE.replace('#', ' '));
            script.textContent = mdtrx.serialize(id);
            doc.head.appendChild(script)

            if (converter) {
                // Creating the script elements for other formats (like Schema.org)
                let converted: MetadataEnvelope = null;
                for(let fmt of converter.formatsToEmbed()) {
                    converted = converter.convertTo(data, fmt);
                    if (converted === null)
                        continue;
                    script = doc.createElement('script');
                    script.id = escapeHTMLchars(converted.label+':'+id, doc);
                    script.type = converted.contentType;
                    script.setAttribute("class", mdclass + converted.label.replace('#', ' '));
                    script.text = converted.serialize();
                    doc.head.appendChild(script);
                }
            }
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
        NerdmConversionService,
        {
            provide: BEFORE_APP_SERIALIZED,
            useFactory: serializeMetadataTransferFactory,
            deps: [DOCUMENT, MetadataTransfer, NerdmConversionService],
            multi: true
        }
    ]
})
export class ServerMetadataTransferModule { }

export { MetadataTransfer };
