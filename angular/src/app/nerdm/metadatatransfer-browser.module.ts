/** 
 * Support for MetadataTransfer on the server side
 *
 * This implementation is based on the angular ServerTransferStateModule (provided
 * via the open license at https://angular.io/license). 
 */
import { NgModule, InjectionToken } from '@angular/core';
import { DOCUMENT } from '@angular/platform-browser';

import { MetadataTransfer } from './nerdm';

/**
 * the factory function for creating a browser-side MetadataTransfer instance
 * loaded with records extracted from the downloaded HTML document.
 */
export function initBrowserMetadataTransfer(doc : Document) : MetadataTransfer {
    let out : MetadataTransfer = new MetadataTransfer();

    let att : string = null;
    let data : {}|null = null;
    const scripts = doc.body.getElementsByTagName("script");
    for (let i=0; i < scripts.length; i++) {
        att = scripts[i].getAttribute("type");
        if (!att || (att != "application/json" && att != "application/ld+json"))
            continue;
        att = scripts[i].getAttribute("id");
        if (!att || att.endsWith("-state"))  // TransferState; don't want this
            continue;

        // att = unescapeHTML(att);
        console.log("Found embedded information with id='"+att+"'");
        try {
            data = JSON.parse(scripts[i].textContent);
            if (data == {})
                data = null;
            out.set(att, data);
        } catch (e) {
            console.warn('Failed to parse transfered JSON metadata for id='+att+": "+e.message);
        }
    }

    return out;
}

/**
 * service module to load MetadataTransfer instance on the browser side
 */
@NgModule({
    providers: [
        { provide: MetadataTransfer, useFactory: initBrowserMetadataTransfer,
          deps: [ DOCUMENT ] }
    ]
})
export class BrowserMetadataTransferModule { }
