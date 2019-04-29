/**
 * Classes used to support the configuration infrastructure.  
 * 
 * Configuration parameters used by the application are defined in the form of
 * interfaces.  The AppConfig is an implementation of the app-level configuration
 * interface, LPSConfig, that can be injected into Components.  
 */
import { Injectable } from '@angular/core';

/**
 * URLs to remote locations used as links in templates
 */
export interface WebLocations {

    /**
     * the institutional home page (e.g. NIST)
     */
    orgHome: string,

    /**
     * the science portal base URL.  
     */
    portalBase?: string,

    /**
     * the home page for the PDR
     */
    pdrHome?: string,

    /**
     * the PDR search page (i.e. the SDP search page)
     */
    pdrSearch?: string,

    /**
     * the base URL for the distribution service
     */
    distService?: string,

    /**
     * the base URL for the (public) metadata service
     */
    mdService?: string,

    /**
     * the base URL for the landing page service
     */
    landingPageService?: string, 

    /**
     * the NERDm info page
     */
    nerdmAbout?: string

    /**
     * other locations are allowed
     */
    [locName: string]: any;
}

/**
 * the aggregation of parameters needed to configure the Landing Page Service
 */
export interface LPSConfig {

    /**
     * URLs used in links plugged into templates
     */
    locations: WebLocations;

    /**
     * Base URL for metadata service to use
     */
    mdAPI?: string;

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

    locations : WebLocations;
    mdAPI     : string;
    status    : string;
    appVersion: string;

    /**
     * create an AppConfig directly from an LPSConfig object
     * @param params   the input data
     */
    constructor(params : LPSConfig) {
        for (var key in params) 
            this[key] = params[key];
        this.inferMissingValues();
    }

    /*
     * set some defaults for missing configuration values based on what has been
     * set.  
     */
    private inferMissingValues() : void {
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
            this.locations.mdService = this.locations.portalBase + "rmm/";
        if (! this.locations.landingPageService)
            this.locations.landingPageService = this.locations.portalBase + "od/id/";
        if (! this.locations.nerdmAbout)
            this.locations.nerdmAbout = this.locations.portalBase + "od/dm/aboutNerdm.html";

        if (! this.mdAPI) this.mdAPI = this.locations.mdService;
    }

    /**
     * get hierarchical values by name with an option to request a default value.  
     * 
     * This function accomplishes two things:  first, it provides a bit of syntactic 
     * sugar for getting at deep values in the parameter hierarchy.  That is, 
     * `cfg.get("location.orgHome")` is equivalent to both `cfg.location.orgHome` and
     * `cfg["location"]["orgHome"]`.  If any of the property names are not one that is 
     * predefined as a class property, only the latter of the alternatives works.  
     *
     * The second bit of functionality is the optional parameter that allows the caller 
     * to set the default value to return if the value is not set.  If the stored value
     * is null or undefined, the default value is returned.  
     * 
     * @param param   the name of the desired parameter
     */
    get<T>(param : string, defval ?: T|null) : T|null|undefined {
        let names: string[] = param.split(".");
        let val : any = this;
        for (var i=0; i < names.length; i++) {
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
export let configFactory : () => AppConfig|null = function() {
    return null;
}
