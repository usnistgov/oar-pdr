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
        
        this.url = [new UrlSegment(path_info, uparams)];
    }
}

/**
 * An ActivatedRoute test double with a `paramMap` observable.
 * Use the `setParamMap()` method to add the next `paramMap` value.
 */
export class MockActivatedRoute {
    // Use a ReplaySubject to share previous values with subscribers
    // and pump new values into the `paramMap` observable
    private subject = new ReplaySubject<ParamMap>();
    snapshot : Map;
    url : string;

    /** The mock paramMap observable */
    readonly paramMap = this.subject.asObservable();

    /**
     * construct the instance
     * @param path_info      the full path portion of the current URL being handled.
     * @param params         the parameters configured into the URL
     */
    constructor(path_info : string, public uparams?: Properties, public qparams? : QProperties) {
        this.url = path_info;
        this.setParamMap(uparams);
        this.snapshot = new MockActivatedRouteSnapshot(path_info, uparams, qparams);
    }

    /** Set the paramMap observables's next value */
    setParamMap(params?: Params) {
        this.subject.next(convertToParamMap(params));
    };
}

/**
 * @deprecated
 */
export class MockTitle extends Title {
    private _title : string = null;
    constructor() { super(null); }
    setTitle(title : string) {
        console.log("updating title to "+title);
        this._title = title;
    }
    getTitle() : string { return this._title; }
}
