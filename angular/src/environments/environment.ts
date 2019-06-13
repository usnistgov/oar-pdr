/*
 * The following is the deprecated environment using the old configuration framework.
 * It is included here keep the application working using the old framework while 
 * the new one is being integrated.  It will be removed when the migration is 
 * complete.
 */
export const environment = {
  production: false,
  RMMAPI: 'http://testdata.nist.gov/rmm/',
    SDPAPI:  'http://testdata.nist.gov/sdp/',
    PDRAPI:  'http://localhost:5555/#/id/',
    DISTAPI: 'https://localhost/od/ds/',
    METAPI:  'http://localhost/metaurl/',
    LANDING: 'http://testdata.nist.gov/rmm/'
};

/*
 * Angular build-time environments data.
 * 
 * Environment Label: dev (default)
 *
 * When building under the dev environment mode, the contents of this file will get built into 
 * the application.  
 *
 * This is the default version of this file.  When the app is built via `ng build --env=label`,
 * the contents of ./environment.label.ts will be used instead.  
 */
import { LPSConfig } from '../app/config/config';

export const context = {
    production: false
};

export const config : LPSConfig = {
    locations: {
        orgHome:     "https://nist.gov/",
        portalBase:  "https://data.nist.gov/",
        pdrHome:     "https://data.nist.gov/pdr/",
        pdrSearch:   "https://data.nist.gov/sdp/"
    },
    mode:        "dev",
    status:      "Dev Version",
    appVersion:  "v1.1.0",
    production:  context.production
}

