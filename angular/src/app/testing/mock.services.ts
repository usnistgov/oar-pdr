/**
 * This contains mock implementations of angular interfaces for use in unit testing
 */
import { convertToParamMap, ParamMap, Params, UrlSegment } from '@angular/router';
import { Title }    from '@angular/platform-browser';
import { ReplaySubject } from 'rxjs';
import * as rxjs from 'rxjs';

export type Map = { [name:string]: any };
export type Properties = { [name:string]: string };
export type QProperties = { [name:string]: string|string[] };

/**
 * implementation of the ParamMap interface
 */
export class SimpleParamMap implements ParamMap {
    private store : {} = {}
    keys : string[] = [];
    
    constructor(private params? : QProperties) {
        if (params) {
            let key : string;
            for (key in params) {
                this.keys.push(key);
                if (params[key] instanceof Array)
                    this.store[key] = params[key];
                else
                    this.store[key] = [params[key]];
            }
        }
    }

    has(key : string) : boolean { return this.store.hasOwnProperty(key); }
    get(key : string) : string  {
        if (! this.has(key) || this.store[key].length == 0)
            return null;

        return this.store[key][0];
    }
    getAll(key : string) : string[] {
        if (! this.has(key))
            return null;
        return this.store[key];
    }
}

/**
 * A mock implementation of the ActivatedRouteSnapshot interface for testing purposes
 */
export class MockActivatedRouteSnapshot {
    url : UrlSegment[];
    paramMap : ParamMap;
    params : Params;
    queryParams : Params;

    constructor(path_info : string, uparams?: Properties, qparams? : QProperties) {
        this.params = uparams;
        this.queryParams = qparams
        this.paramMap = new SimpleParamMap(uparams);
        this.url = path_info.split('/').map(this.toSegment);
    }

    private toSegment(pathfield: string) : UrlSegment {
        let parts : string[] = pathfield.split(';');
        let props : Properties = {};
        let kv : string[];
        for (let p of parts.slice(1)) {
            kv = p.split("=");
            if (kv.length < 2) kv.push('');
            props[kv[0]] = kv[1];
        }
        return new UrlSegment(parts[0], props)
    }
}

/**
 * An ActivatedRoute test double with a `paramMap` observable.
 * Use the `setParamMap()` method to add the next `paramMap` value.
 */
export class MockActivatedRoute {
    // Use a ReplaySubject to share previous values with subscribers
    // and pump new values into the `paramMap` observable
    private uparamSubj = new ReplaySubject<ParamMap>();
    private qparamSubj = new ReplaySubject<ParamMap>();
    private paramsSubj = new ReplaySubject<ParamMap>();
    snapshot : Map;
    url : string;

    /** The mock paramMaps observables */
    readonly paramMap = this.uparamSubj.asObservable();
    readonly queryParamMap = this.qparamSubj.asObservable();
    readonly params = this.paramsSubj.asObservable();

    /**
     * construct the instance
     * @param path_info      the full path portion of the current URL being handled.
     * @param params         the parameters configured into the URL
     */
    constructor(path_info : string, public uparams?: Properties, public qparams? : QProperties) {
        this.snapshot = new MockActivatedRouteSnapshot(path_info, uparams, qparams);
        this.url = this.snapshot.url;
        this.setParamMap(uparams);
        this.setQueryParamMap(qparams);
    }

    /** Set the paramMap observables's next value */
    setParamMap(params?: Params) {
        this.uparamSubj.next(convertToParamMap(params));
    };

    /** Set the paramMap observables's next value */
    setQueryParamMap(params?: Params) {
        this.qparamSubj.next(convertToParamMap(params));
    };

    /** Set the paramMap observables's next value */
    setParams(params?: Params) {
        this.paramsSubj.next(convertToParamMap(params));
    };
}

