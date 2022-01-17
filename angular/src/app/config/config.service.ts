import { Inject, InjectionToken } from '@angular/core';
import { isPlatformServer } from '@angular/common';
import { TransferState, makeStateKey, StateKey } from '@angular/platform-browser';
import * as proc from 'process';
import * as fs from 'fs';

import { AppConfig, LPSConfig } from './config';
import * as ngenv from '../../environments/environment';

export const CONFIG_KEY_NAME : string = "LPSConfig";
export const CONFIG_TS_KEY : StateKey<string> = makeStateKey(CONFIG_KEY_NAME);
export const CFG_DATA : InjectionToken<LPSConfig> = new InjectionToken<LPSConfig>("lpsconfig");

/**
 * create a deep copy of an object
 */
export function deepCopy(obj) {
    // this implementation comes courtesy of and with thanks to Steve Fenton via
    // https://stackoverflow.com/questions/28150967/typescript-cloning-object/42758108
    var copy;

    // Handle the 3 simple types, and null or undefined
    if (null == obj || "object" != typeof obj) return obj;

    // Handle Date
    if (obj instanceof Date) {
        copy = new Date();
        copy.setTime(obj.getTime());
        return copy;
    }

    // Handle Array
    if (obj instanceof Array) {
        copy = [];
        for (var i = 0, len = obj.length; i < len; i++) {
            copy[i] = deepCopy(obj[i]);
        }
        return copy;
    }

    // Handle Object
    if (obj instanceof Object) {
        copy = {};
        for (var attr in obj) {
            if (obj.hasOwnProperty(attr)) copy[attr] = deepCopy(obj[attr]);
        }
        return copy;
    }
 
    throw new Error("Unable to copy obj! Its type isn't supported.");
}

/**
 * a service that will create an AppConfig instance loaded with values 
 * approriate for the runtime context.
 */
export abstract class ConfigService {

    /**
     * return an AppConfig instance that is appropriate for the runtime 
     * context.
     */
    abstract getConfig() : AppConfig; 
    
}

/**
 * a ConfigService that can cache the configuration for transfer to a browser-side
 * environment.  
 * 
 * This provides the ability (via cache(LPSConfig)) to save the configuration to the 
 * cache which would typically be called after the configuration data is loaded into 
 * the class for the first time.  The default implementation of getConfig() provided 
 * by this subclass does just that, defering the loading to a new abstract function, 
 * loadConfig().  
 *
 * The implementation of the getConfig() function provided by this class will manipulate
 * the LPSConfig cached to the cache to hide the server-side-specific API endpoints from 
 * browser-side.  
 */
export abstract class CachingConfigService extends ConfigService {
    protected config : AppConfig|null = null;

    /**
     * initialize the cache for this service
     * @param cache      the TransferState to cache the data to the first time it 
     *                   is accessed via getConfig()
     */
    constructor(protected cache? : TransferState) {
        super();
    }

    /**
     * load the configuration data from the appropriate source for the implementation
     * and return it.
     * @return LPSConfig -- the loaded configuration data
     */
    abstract loadConfig() : LPSConfig;

    /**
     * return an AppConfig instance that is appropriate for the runtime 
     * context.
     */
    getConfig() : AppConfig {
        if (! this.config) {
            let cfgdata : LPSConfig = this.loadConfig();
            this.config = new AppConfig(this._useServerSide(cfgdata));

            if (this.cache) 
                this.cache.set(CONFIG_TS_KEY, new AppConfig(this._hideServerSide(cfgdata)))
        }
        return this.config;
    }

    protected _useServerSide(cfgdata : LPSConfig) {
        cfgdata = deepCopy(cfgdata);
        if (cfgdata['APIs'] && cfgdata['APIs']['serverSide']) {
            cfgdata['APIs'] = { ...cfgdata['APIs'], ...cfgdata['APIs']['serverSide'] };
            delete cfgdata['APIs']['serverSide'];
        }
        return cfgdata;
    }

    protected _hideServerSide(cfgdata : LPSConfig) {
        cfgdata = deepCopy(cfgdata);
        if (cfgdata['APIs'] && cfgdata['APIs']['serverSide'])
            delete cfgdata['APIs']['serverSide'];
        return cfgdata;
    }
}

/**
 * A ConfigService that pulls it data from the environmental context
 * that Angular builds into the app.  
 * 
 * This service is intended for use in development mode running either as 
 * client-only in the browser or on the server.  
 */
export class AngularEnvironmentConfigService extends CachingConfigService {
    private source : string = "angular-env";
    private defMode : string = "dev";

    /**
     * construct the service
     * @param platid   the PLATFORM_ID value for determining if we are running on the server
     *                 or in the browser.
     * @param cache    the TransferState instance for the application.  If we are on the server,
     *                 getConfig() will cache the configuration to the TransferState object.
     */
    constructor(private platid : object, cache : TransferState) {
        super(cache);
    }

    /**
     * load the configuration data from the appropriate source for the implementation
     * and return it.
     * @return LPSConfig -- the loaded configuration data
     */
    loadConfig() : LPSConfig {
        console.log("Loading development-mode configuration data from the Angular built-in environment");
        let out : LPSConfig = deepCopy(ngenv.config);
        out["source"] = this.source;
        if (! out["mode"]) 
            out["mode"] = this.defMode;
        return out;
    }

    /**
     * return an AppConfig instance that is appropriate for the runtime 
     * context.  This will synchronously return an AppConfig rather than a 
     * Promise.  
     */
    getConfig() : AppConfig {
        if (! this.config) {
            this.config = new AppConfig(this.loadConfig());
            if (isPlatformServer(this.platid))
                this.cache.set(CONFIG_TS_KEY, this.config);
        }
        return this.config;
    }
}

/**
 * a ConfigService that reads in its data from a file on local disk.  
 * 
 * This will only work on the server.  The data is read in from a given
 * JSON-formatted file specified at construction.
 * 
 * This service is intended for when the LPS is running in a docker container 
 * from oar-docker.  The container launch script pulls configuration from the
 * config-server and writes it to a file.
 */
export class ServerFileConfigService extends CachingConfigService {

    private source : string = "server-file";
    private defMode : string = "prod";       // i.e. in the docker context

    /**
     * construct the service.  
     * 
     * @param cfgfile   the (full) path to the file to read JSON-encoded data from
     * @param cache     the TransferState to cache the data to the first time it 
     *                  is accessed via getConfig()
     * @throw Error -- if cfgfile is not set or does not point to an existing file.  
     */
    constructor(private cfgfile : string, cache? : TransferState) {
        super(cache);
        if (! cfgfile)
            throw new Error("Configuration file not provided");
        if (! fs.existsSync(cfgfile))
            throw new Error(cfgfile + ": File not found");
        if (! fs.statSync(cfgfile).isFile())
            throw new Error(cfgfile + ": Not a file");
    }

    /**
     * read the configuration data in from a JSON file
     * @return LPSConfig -- the loaded configuration data
     */
    loadConfig() : LPSConfig {
        console.log("Loading configuration data from " + this.cfgfile);

        // synchronous read.  (The file is typically short.)
        let out : LPSConfig = JSON.parse(fs.readFileSync(this.cfgfile, 'utf8'));
        out["source"] = this.source;
        if (! out["mode"])
            out["mode"] = this.defMode;
        return out;
    }
}

/**
 * a server-side ConfigService that provides data that was loaded in when the 
 * server started. 
 */
export class ServerLoadedConfigService extends CachingConfigService {

    /**
     * initialize the service
     * @param cfgdata    the previously loaded configuration data.  It is assumed 
     *                   that the "mode" and "source" properties have already been
     *                   appropriately set.  
     * @param cache      the TransferState to cache the data to the first time it 
     *                   is accessed via getConfig()
     */
    constructor(private cfgdata : LPSConfig, cache? : TransferState) {
        super(cache);
        if (! cfgdata)
            throw new Error("Server failed to load config data");
    }

    /**
     * return configuration data previously loaded by the server.  This simply
     * returns the data set at construction time.
     */
    loadConfig() : LPSConfig {
        console.log("Loading configuration data previously loaded by server");
        return this.cfgdata;
    }
}

/**
 * a ConfigService that pulls in data the transfer state
 */
export class TransferStateConfigService extends ConfigService {

    private source : string = "transfer-state";
    private defMode : string = "prod";

    /**
     * create the service given a TransferState container
     */
    constructor(private cache : TransferState) {
        super();
        if (! cache.hasKey(CONFIG_TS_KEY))
            throw new Error("Config key not found in TransferState: " + CONFIG_KEY_NAME);
    }

    /**
     * return an AppConfig instance that is appropriate for the runtime 
     * context.  This implementation extracts the configuration data from 
     * the transfer state.
     */
    getConfig() : AppConfig {
        console.log("Loading configuration data delivered from the server.");

        let data : LPSConfig|null = this.cache.get(CONFIG_TS_KEY, null) as LPSConfig;
        if (! data)
            throw new Error("Missing key from transfer state: " + CONFIG_KEY_NAME)
        data["source"] = this.source;
        if (! data["mode"])
            data["mode"] = this.defMode;
        return new AppConfig(data);
    }
}

/**
 * return ConfigService appropriate for current runtime context.
 * 
 * If the app is running in the user's browser, the service will look for 
 * the returned service will load configuration data from the app's the 
 * transfer state.  If it is not there, we can assume that 
 * we are running in development-client-only mode and 
 * retrieve the data from the built-in environment.  If the app is running 
 * on the server, we can retrieve the data from a local file whose path
 * is set in the OS environment variable (OAR_CONFIG_FILE).  If that is 
 * not set, we can assume we are running in development-server mode.
 *
 * @param platid    the PLATFORM_ID for determining if we are running on the server
 * @param cache     a TransferState instance to check for config data
 * @param cfgdata   (optional) LPSConfig object that contains the configuration data loaded 
 *                    explicitly by some other means.  (This hook is intended for future 
 *                    ways of loading the configuration data on the server.)
 */
export function newConfigService(platid : Object, cache : TransferState, cfgdata? : LPSConfig)
    : ConfigService
{
    if (cache.hasKey(CONFIG_TS_KEY))
        // this means we're on (should be) on the browser side
        return new TransferStateConfigService(cache);

    if (isPlatformServer(platid) && cfgdata)
        // this means we're on the server in production-like mode
        // this will stash the data into the TransferState
        return new ServerLoadedConfigService(cfgdata, cache)

    if (isPlatformServer(platid) && proc.env["PDR_CONFIG_FILE"])
        // this means we're on the server in production-like mode
        // this will stash the data into the TransferState
        return new ServerFileConfigService(proc.env["PDR_CONFIG_FILE"], cache)

    // This is the default intended for a development context
    // this will stash the data into the TransferState
    return new AngularEnvironmentConfigService(platid, cache);
}
