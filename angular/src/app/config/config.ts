/**
 * Classes used to support the configuration infrastructure.  
 * 
 * Configuration parameters used by the application are defined in the form of
 * interfaces.  The AppConfig is an implementation of the app-level configuration
 * interface, LPSConfig, that can be injected into Components.  
 */
import { Injectable } from '@angular/core';

/**
 * URLs to key repository destinations.  These are URLs accessed via HTML links when the 
 * user actively clicks on a link in the page.  Because these locations appear in HTML, and 
 * therefore accessed browser-side exclusively, they must publicly-accessible URLs.
 *
 * These values can also serve as defaults for infering URLs--including API endpoints--that
 * are not explicitly set.
 */
export interface WebLocations {

    /**
     * the institutional home page (e.g. NIST)
     */
    orgHome: string;

    /**
     * the science portal base URL.  
     */
    portalBase?: string;

    /**
     * the home page for the PDR
     */
    pdrHome?: string;

    /**
     * the PDR search page (i.e. the SDP search page)
     */
    pdrSearchPortal?: string;

    /**
     * the base URL for generating view of search results from a search query
     */
    pdrSearchResults?: string;

    /**
     * the base URL for the distribution service and downloading dataset files
     */
    distService?: string;

    /**
     * the base URL for the ID-to-metadata resolving service
     */
    mdService?: string;

    /**
     * the base URL for generating a search resutls
    mdSearch?: string;
     */

    /**
     * the URL to fetch taxonomy list
    taxonomyService?: string;
     */

    /**
     * the base URL for generating the landing page for a given ID
     */
    landingPageService?: string;

    /**
     * the NERDm info page
     */
    nerdmAbout?: string;

    /**
     * other locations are allowed
     */
    [locName: string]: any;
}

/**
 * API endpoint URLs.  These base URLs are intended for services accessed via 
 * Typescript code (as opposed to those that appear in HTML links).
 * 
 * The proper API URL to use can depend on whether the code is running server-side
 * or browser-side.  One should set server-side URLs under "serverSide"; these will 
 * automatically over-ride the ones above them on the serverSide (via the ConfigService).
 * Thus, always access the URL parameters via their normal names.  
 *
 * For example, the metadata resolver service API, "mdService", needs to be accessed 
 * via Typescript code, set the browser-side version of the URL as "APIs.mdSearch", 
 * and set the service-side as "APIs.serverSide.mdSearch"; regardless, always access 
 * the parameter via "APIs.mdSearch" to get the appropriate version.  
 */
export interface APIEndpoints {

    /**
     * the (RMM) metadata search endpoint.  This URL is expected to be appended with a 
     * search query for returning arbitrary metadata.  Note that the mdService is intended 
     * for resolving an ID into a specific metadata record.
     */
    mdSearch?: string;

    /**
     * the base URL for the ID-to-metadata resolving service
     */
    mdService?: string;

    /**
     * the metrics data API.
     */
    metrics?: string;

    /**
     * the endpoint for retrieving the theme taxonomy terms
     */
    taxonomy?: string;

    /**
     * the base URL for the distribution service API (including data bundling)
     */
    distService?: string;

    /**
     * Base URL for customization service to use
     */
    customization?: string;

    /**
     * the server-side versions of the above URLs
     */
    serverSide?: APIEndpoints;

    /**
     * other API URLs are allowed
     */
    [locName: string]: any;
}

/**
 * the aggregation of parameters needed to configure the Landing Page Service
 */
export interface LPSConfig {

    /**
     * URLs used in links plugged into HTML templates
     */
    locations: WebLocations;

    /**
     * Endpoint URLs for APIs accessed from code
     */
    APIs: APIEndpoints;

    /**
     * True if editing widgets should be made available in the landing page.
     * This is intended to be true for the internal publishing version of the 
     * landing page, and false for the external one.  The default will be false.
     */
    editEnabled?: boolean;

    /**
     * a label to display (in the head bar) indicating the status of displayed interface.  
     *
     * This is usually populated in production contexts; example values
     * include "Review Version", "Dev Version".  
     */
    status?: string;

    /**
     * the interface version to display (in the head bar)
     */
    appVersion?: string;

    /**
     * Google Analytics code
     */
    gaCode?: string;

    /**
     * other parameters are allowed
     */
    [propName: string]: any;
}

/**
 * a class implementation of the LPSConfig interface.  
 * 
 * This adds functions for specialized access to the parameters, such as
 * specifying a default value.  
 * 
 * See {@link LPSConfig} for property documentation.
 */
export class AppConfig implements LPSConfig {

    locations: WebLocations;
    APIs: APIEndpoints;
    editEnabled: boolean;
    status: string;
    appVersion: string;
    gaCode     : string;

    /**
     * create an AppConfig directly from an LPSConfig object
     * @param params   the input data
     */
    constructor(params: LPSConfig) {
        for (var key in params)
        this[key] = params[key];
        this.inferMissingValues();
    }

    /*
    * set some defaults for missing configuration values based on what has been
    * set.  
    */
    private inferMissingValues(): void {
        // set the default locations URLs
        if (! this.locations.portalBase) {
            this.locations.portalBase = this.locations.orgHome;
            if (! this.locations.portalBase.endsWith('/'))
                this.locations.portalBase += '/';
            this.locations.portalBase += 'data/';
        }

        if (! this.locations.pdrHome)
            this.locations.pdrHome = this.locations.portalBase + "pdr/";
        if (! this.locations.pdrSearch)
            this.locations.pdrSearch = this.locations.portalBase + "sdp/";
        if (! this.locations.distService)
            this.locations.distService = this.locations.portalBase + "od/ds/";
        if (! this.locations.mdService)
            this.locations.mdService = this.locations.portalBase + "od/id/";

        /*
        if(! this.locations.taxonomyService)
            this.locations.taxonomyService = this.locations.portalBase + "rmm/taxonomy";
        */
        
        if (! this.locations.landingPageService)
            this.locations.landingPageService = this.locations.portalBase + "od/id/";
        if (! this.locations.nerdmAbout)
            this.locations.nerdmAbout = this.locations.portalBase + "od/dm/nerdm/";

        // set the default API URLs

        if (! this.APIs)
            this.APIs = {}
        if (! this.APIs.mdSearch)
            this.APIs.mdSearch = this.locations.portalBase + "rmm/"
        if (! this.APIs.mdService)
            this.APIs.mdService = this.locations.mdService;
        if (! this.APIs.distService)
            this.APIs.distService = this.locations.distService;
        if (! this.APIs.customization)
            this.APIs.customization = this.locations.portalBase + "customization/";
        if (! this.APIs.metrics)
            this.APIs.metrics = this.APIs.mdSearch + "usagemetrics/";
        if (! this.APIs.taxonomy)
            this.APIs.taxonomy = this.APIs.mdSearch + "taxonomy/";

        // Set default Google Analytic code to dev
        if (! this.gaCode) this.gaCode = "UA-115121490-8";

        if (typeof (this.editEnabled) === "undefined") this.editEnabled = false;
    }

    /**
     * get hierarchical values by name with an option to request a default value.  
     * 
     * This function accomplishes two things:  first, it provides a bit of syntactic 
     * sugar for getting at deep values in the parameter hierarchy.  That is, 
     * `cfg.get("locations.orgHome")` is equivalent to both `cfg.locations.orgHome` and
     * `cfg["location"]["orgHome"]`.  If any of the property names are not one that is 
     * predefined as a class property, only the latter of the alternatives works.  
     *
     * The second bit of functionality is the optional parameter that allows the caller 
     * to set the default value to return if the value is not set.  If the stored value
     * is null or undefined, the default value is returned.  
     * 
     * @param param   the name of the desired parameter
     */
    get<T>(param: string, defval?: T | null): T | null | undefined {
        let names: string[] = param.split(".");
        let val: any = this;
        for (var i = 0; i < names.length; i++) {
            if (typeof val != "object")
                return defval;
            val = val[names[i]];
        }
        return (val != undefined) ? val : defval;
    }

}

/**
 * a factory function for creating an AppInfo instance
 * 
 * This function's behavior will depend on whether the app is running on the server 
 * or in the client's browser, and on whether in development mode or production.  
 * If running on the server in production, the factory will pull in the configuration
 * data in from the environment.  If running in the browser, it will look for the 
 * configuration information from the transfer state.  If the data is not available 
 * in the transfer state (because it is in development mode), ...
 */
export let configFactory: () => AppConfig | null = function () {
    return null;
}
