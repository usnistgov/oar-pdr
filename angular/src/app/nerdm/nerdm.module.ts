import { NgModule, PLATFORM_ID, InjectionToken } from '@angular/core';
import { isPlatformServer } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import * as proc from 'process';

import { MetadataService, createMetadataService } from './nerdm.service'
import { MetadataTransfer } from './nerdm';
import { AppConfig } from '../config/config';

const PDR_METADATA_SVCEP : InjectionToken<string> =
    new InjectionToken<string>("PDR_METADATA_SVCEP");

/**
 * return the endpoint to use to retrieve NERDm resource records.  Normally, this 
 * value is gotten from the configuration provide by AppConfig; however, the value 
 * there can be overridden on the server if the the PDR_METADATA_SVCEP environment 
 * variable is set.
 */
export function getMetadataEndpoint(platid : Object, config : AppConfig) : string {
    if (isPlatformServer(platid) && proc.env["PDR_METADATA_SVCEP"])
        return proc.env["PDR_METADATA_SVCEP"];
    return config.get("mdAPI", "/unconfigured");
}

/**
 * A module supporting NERDm record handling, including services and a display component
 */
@NgModule({
    declarations: [ ],
    providers: [
        HttpClient,

        // The metadata service endpoint
        { provide: PDR_METADATA_SVCEP, useFactory: getMetadataEndpoint,
          deps: [ PLATFORM_ID, AppConfig ] },

        // The metadata service
        { provide: MetadataService, useFactory: createMetadataService,
          deps: [ PLATFORM_ID, PDR_METADATA_SVCEP, HttpClient, MetadataTransfer ] },
    ],
    exports: [ ]
})
export class NerdmModule { }

