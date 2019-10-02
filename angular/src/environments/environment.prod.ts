/*
 * Angular build-time environments data.
 * 
 * Environment Label: prod
 *
 * When building under the prod environment mode, the contents of this file will get built into 
 * the application; however, it's contents should be largely inconsequential as configuration 
 * data should be retrieved from the configuration service.  
 */
import { LPSConfig } from '../app/config/config';

export const context = {
    production: true,
    useMetadataService: true
};

export const config : LPSConfig = {
    locations: {
        orgHome:     "https://nist.gov/",
        portalBase:  "https://data.nist.gov/",
        pdrHome:     "https://data.nist.gov/pdr/",
        pdrSearch:   "https://data.nist.gov/sdp/"
    },
    mode:        "dev",
    status:      "Production Version",
    appVersion:  "v1.2.X",
    production:  context.production,
    editEnabled: true
}

export const testdata : {} = {
};

