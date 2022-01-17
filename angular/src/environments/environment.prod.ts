export const environment = {
  production: true,
  RMMAPI: 'http://testdata.nist.gov/rmm/',
  SDPAPI:  'http://testdata.nist.gov/sdp/',
  PDRAPI:  'http://localhost:5555/#/id/',
  DISTAPI: 'https://localhost/od/ds/',
  METAPI:  'http://localhost/metaurl/',
  LANDING: 'http://testdata.nist.gov/rmm/'
};

import { LPSConfig } from '../app/config/config';

export const context = {
    production: true,
    useMetadataService: false,
    useCustomizationService: true
};

export const config : LPSConfig = {
    locations: {
        orgHome: "https://nist.gov/",
        portalBase: "https://data.nist.gov/",
        pdrHome: "https://data.nist.gov/pdr/",
        pdrSearch: "https://data.nist.gov/sdp/",
        mdService:   "https://data.nist.gov/rmm/records/",
        taxonomyService: "https://data.nist.gov/rmm/taxonomy"
    },
    APIs: {
        mdService: "https://data.nist.gov/od/id/",
        mdSearch:  "https://data.nist.gov/rmm",
        metrics:   "https://data.nist.gov/rmm/usagemetrics",
        taxonomy:   "https://data.nist.gov/rmm/taxonomy",
        // customization: "https://testdata.nist.gov/customization",
        customization: "https://data.nist.gov/customization",
        distService: "https://data.nist.gov/od/ds/"
    },
    mode:        "dev",
    status:      "Dev Version",
    appVersion:  "v1.1.0",
    production:  context.production,
    editEnabled: false,
    gacode: "not-set",
    screenSizeBreakPoint: 1060,
    bundleSizeAlert: 500000000,
    embedMetadata: "schema.org",
    // Decide how many seconds to wait to refresh metrics after user download one/more files
    delayTimeForMetricsRefresh: 300  
}

export const testdata : {} = { }

