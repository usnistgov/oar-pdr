import { Injectable } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { Observable, of, throwError, Subscriber } from 'rxjs';

import { AppConfig } from '../../config/config';
import { CustomizationService, WebCustomizationService, InMemCustomizationService, 
         SystemCustomizationError, ConnectionCustomizationError } from './customization.service';
import * as ngenv from '../../../environments/environment';

/**
 * a container for authorization and authentication information that is obtained
 * from the customization service while authorizing the user to edit the metadata.
 * This interface is used for receiving this information from the customization 
 * web service. 
 */
interface AuthInfo {
    /**
     * the user identifier
     */
    userId ?: string,

    /**
     * the authorization token needed to edit metadata via the customization service
     */
    token ?: string,

    [prop : string]: any;
}

/**
 * the authentication/authorization front-end service to the customization service.
 *
 * The purpose of this service is to authenticate a user and establish their authorization to 
 * edit a resource metadata record via the customization service.  In particular, this service 
 * serves as a factory for a CustomizationService that allows editing of the resource metadata 
 * associated with a particular identifier.  
 *
 * This abstract class allows for different implementations for different execution 
 * contexts.  In particular, mock versions can be provided for development and testing 
 * contexts.
 */
export abstract class AuthService {

    protected _userid : string = null;

    /**
     * the authenticated identifier for the current user.
     */
    get userID() { return this._userid; }

    /**
     * construct the service
     */
    constructor() { }

    /**
     * return true if the user is currently authorized to to edit the resource metadata.
     * If false, can attempt to gain authorization via a call to authorizeEditing();
     */
    public abstract isAuthorized() : boolean;

    /**
     * create a CustomizationService that allows the user to edit the resource metadata 
     * associated with the given ID.
     */
    public abstract authorizeEditing(resid : string) : Observable<CustomizationService>;

    /**
     * redirect the browser to the authentication service, instructing it to return back to 
     * the current landing page.  
     */
    public abstract loginUser() : void;
}

/**
 * an implementation of the CustomizationService that caches metadata updates on the 
 * server via a web service.  
 *
 * This implementation is intended for use in production.  
 */
@Injectable()
export class WebAuthService extends AuthService {

    private _endpoint : string = null;
    private _authtok : string = null;
    private _authcred : AuthInfo = {
        userId: null,
        token: null
    };

    /**
     * the endpoint URL for the customization web service 
     */
    get endpoint() { return this._endpoint; }

    /**
     * the authorization token that gives the user permission to edit the resource metadata
     */
    get authToken() { return this._authcred.token; }

    /**
     * the user ID that the current authorization has been granted to.
     */
    get userID() { return this._authcred.userId; }

    /**
     * create the AuthService according to the given configuration
     * @param config  the current app configuration which provides the customization service endpoint.
     *                (this is normally provided by the root injector).
     * @param httpcli an HttpClient for communicating with the customization web service
     */
    constructor(config : AppConfig, private httpcli : HttpClient) {
        super();
        this._endpoint = config.get('customizationAPI', '/customization/');
        if (! this._endpoint.endsWith('/')) this._endpoint += "/";
    }

    /**
     * return true if the user is currently authorized to to edit the resource metadata.
     * If false, can attempt to gain authorization via a call to authorizeEditing();
     */
    public isAuthorized() : boolean {
        return Boolean(this.authToken);
    }

    /**
     * create a CustomizationService that allows the user to edit the resource metadata 
     * associated with the given ID.  If the CustomizationService returned through the 
     * Observable is null, the user is not authorized to edit.  
     *
     * Note that instead of returning, this method may redirect the browser to an authentication
     * server to authenticate the user.  
     * 
     * @param resid    the identifier for the resource to edit
     */
    public authorizeEditing(resid : string) : Observable<CustomizationService> {
        
        if (this.authToken)
            return of(new WebCustomizationService(resid, this.endpoint, this.authToken, this.httpcli));

        // we need an authorization token
        return new Observable<CustomizationService>(subscriber => {
            this.getAuthorization(resid).subscribe(
                (info) => {
                    this._authcred.token = info.token;
                    this._authcred.userId  = info.userId;
                    if (info.token) {
                        // the user is authenticated and authorized to edit!
                        subscriber.next(
                            new WebCustomizationService(resid, this.endpoint, this.authToken, this.httpcli)
                        );
                        subscriber.complete();
                    }
                    else if (info.userId) {
                        // the user is authenticated but not authorized
                        subscriber.next(null);
                        subscriber.complete();
                    }
                    else {
                        // the user is not authenticated!
                        subscriber.complete();

                        // redirect the browser to the authentication server
                        this.loginUser();
                    }
                },
                (err) => {
                    subscriber.error(err);
                    subscriber.complete();
                }
            );
        });
    }

    /**
     * fetch an authorization to edit the current resource metadata from the customization
     * service.
     *
     * @param resid    the identifier for the resource to edit
     * @return Observable<AuthInfo>  -- On success, an AuthInfo containing either (1) the user's 
     *            ID and an authorization token, indicating that the user is both authenticated 
     *            and authorized, (2) just the user's ID, indicating that the user is authenticated
     *            but not authorized, or (3) nothing, indicating that the user is not authenticated.  
     *            If there is a CustomizationError, an exception is sent to the error handler.
     */
    public getAuthorization(resid : string) : Observable<AuthInfo> {
        let url = this.endpoint + "auth/_perm/" + resid;

        // wrap the HttpClient Observable with our own so that we can manage errors
        return new Observable<AuthInfo>(subscriber => {
            this.httpcli.get(url, {
                headers: { 'Content-Type': 'application/json' },
                observe: 'response',
                responseType: 'json'
            }).subscribe(
                (resp) => {
                    if (resp.status == 200) {
                        // URL returned OK
                        subscriber.next(resp.body as AuthInfo);
                    }
                    else if (resp.status == 404) {
                        // URL returned Not Found
                        subscriber.next({} as AuthInfo);
                    }
                    else {
                        // URL returned some other error status
                        let msg = "Unexpected error during authorization: ";
                        msg += (resp.body['message']) ? resp.body['message'] : resp.statusText;
                        msg += " (" + resp.status.toString() + ")"
                        subscriber.error(new SystemCustomizationError(msg, resp.status))
                    }
                    subscriber.complete();
                },
                (err) => {
                    // Unable to successfully complete connection and close
                    subscriber.error(
                        new ConnectionCustomizationError("Authorization service connection error: "+err)
                    );
                    subscriber.complete();
                }
            );
        });
    }

    /**
     * redirect the browser to the authentication service, instructing it to return back to 
     * the current landing page.  
     * 
     * @return string   the authenticated user's identifier, or null if authentication was not 
     *                  successful.  
     */
    public loginUser() : void {
        let redirectURL = this.endpoint + "saml/login?redirectTo=" + window.location.href + "?editmode=true";
        console.log("Redirecting to "+redirectURL+" to authenticate user");
        window.location.replace(redirectURL);
    }
}

/**
 * An AuthService intended for development and testing purposes which simulates interaction 
 * with a authorization service.
 */
@Injectable()
export class MockAuthService extends AuthService {

    /**
     * the authenticated identifier for the current user.  Set this to null to trigger 
     * a simulated routing through an authentication service.  
     */
    get userID() { return this._userid; }
    // see https://stackoverflow.com/questions/38717725/why-cant-get-superclasss-property-by-getter-typescript
    
    set userID(id : string) { this._userid = id; }

    private resdata : {} = {};

    /**
     * construct the authorization service
     *
     * @param resmd      the original resource metadata 
     * @param userid     the ID of the user; default "anon"
     */
    constructor(userid ?: string) {
        super();
        if (userid === undefined) userid = "anon";
        this.userID = userid;

        if (! ngenv.testdata)
            throw new Error("No test data encoded into angular environment");
        if (Object.keys(ngenv.testdata).length < 0)
            console.warn("No NERDm records included in the angular environment");

        // load resource metadata lookup by ediid
        for (let key of Object.keys(ngenv.testdata)) {
            if (ngenv.testdata[key]['ediid']) 
                this.resdata[ngenv.testdata[key]['ediid']] = ngenv.testdata[key];
        }
    }

    /**
     * return true if the user is currently authorized to to edit the resource metadata.
     * If false, can attempt to gain authorization via a call to authorizeEditing();
     */
    public isAuthorized() : boolean {
        return Boolean(this.userID);
    }

    /**
     * create a CustomizationService that allows the user to edit the resource metadata 
     * associated with the given ID.
     */
    public authorizeEditing(resid : string) : Observable<CustomizationService> {
        // REMOVE THIS when MetadataService is available
        resid = "26DEA39AD677678AE0531A570681F32C1449";
        
        // simulate logging in with a redirect 
        if (! this.userID) this.loginUser();
        if (! this.resdata[resid])
            return of<CustomizationService>(null);

        return of<CustomizationService>(new InMemCustomizationService(this.resdata[resid]));
    }

    /**
     * redirect the browser to the authentication service, instructing it to return back to 
     * the current landing page.  
     */
    public loginUser() : void {
        let redirectURL = window.location.href + "?editmode=true";
        console.log("Bypassing authentication service; redirecting directly to "+redirectURL);
        if (! this._userid) this._userid = "anon";
        window.location.replace(redirectURL);
    }
}

/**
 * create an AuthService based on the runtime context.
 * 
 * This factory function determines whether the application has access to a customization 
 * web service (e.g. in production mode under oar-docker).  In this case, it will return 
 * a AuthService configured to use the service.  In a development runtime context, where 
 * the app is running standalone without such access, a mock service is returned.  
 * 
 * Which type of AuthService is returned is determined by the value of 
 * context.useCustomizationService from the angular environment (i.e. 
 * src/environments/environment.ts).  A value of false assumes a develoment context.
 */
export function createAuthService(config : AppConfig, httpClient : HttpClient, devmode ?: boolean)
    : AuthService
{
    if (devmode === undefined)
        devmode = Boolean(ngenv['context'] || ngenv['context']['useCustomizationService']);
        
    if (! devmode) {
        // production mode
        console.log("Will use configured customization web service");
        return new WebAuthService(config, httpClient);
    }

    // dev mode
    if (! ngenv['context'])
        console.warn("Warning: angular environment is missing context data");
    console.log("Using mock AuthService/CustomizationService");
    return new MockAuthService();
}

