import { Injectable } from '@angular/core';
import { HttpClient, HttpResponse } from '@angular/common/http';
import { Observable, of, throwError, Subscriber } from 'rxjs';

import { AppConfig } from '../../config/config';
import {
    CustomizationService, WebCustomizationService, InMemCustomizationService,
    SystemCustomizationError, ConnectionCustomizationError
} from './customization.service';
import * as ngenv from '../../../environments/environment';
import { UserDetails } from './interfaces';

/**
 * a container for authorization and authentication information that is obtained
 * from the customization service while authorizing the user to edit the metadata.
 * This interface is used for receiving this information from the customization 
 * web service. 
 */
export interface AuthInfo {
    /**
     * the user identifier
     */
    userDetails?: UserDetails,

    /**
     * the authorization token needed to edit metadata via the customization service
     */
    token?: string,

    [prop: string]: any;
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
    protected _authcred: AuthInfo = {
        userDetails: { userId: null },
        token: null
    };

    /**
     * the full set of user information obtained via the log-in process
     */
    get userDetails() { return this._authcred.userDetails; }

    /**
     * the user ID that the current authorization has been granted to.
     */
    get userID() { return this.userDetails.userId; }

    set userDetails(userDetails: UserDetails) { this._authcred.userDetails = userDetails; }

    /**
     * construct the service
     */
    constructor() { }

    /**
     * return the user details in a implementation-specific way
     */
    // protected abstract _getUserDetails(): UserDetails;

    /**
     * return true if the user is currently authorized to to edit the resource metadata.
     * If false, can attempt to gain authorization via a call to authorizeEditing();
     */
    public abstract isAuthorized(): boolean;

    /**
     * create a CustomizationService that allows the user to edit the resource metadata 
     * associated with the given ID.  Note that an implementation may need to redirect the browser 
     * to an authentication service to determine who the current user is.  
     *
     * @param resid     the identifier for the resource to edit
     * @param nologin   if false (default) and the user is not logged in, the browser will be redirected 
     *                  to the authentication service.  If true, redirection will not occur; instead, 
     *                  no user information is set and null is returned if the user is not logged in.  
     * @param Observable<CustomizationService>  an observable wrapped CustomizationService that should 
     *                  be used to send edits to the customization server.  The service will be null if 
     *                  the user is not authorized.  
     */
    public abstract authorizeEditing(resid: string, nologin?: boolean)
        : Observable<CustomizationService>;

    /**
     * redirect the browser to the authentication service, instructing it to return back to 
     * the current landing page.  
     */
    public abstract loginUser(): void;
}

/**
 * an implementation of the CustomizationService that caches metadata updates on the 
 * server via a web service.  
 *
 * This implementation is intended for use in production.  
 */
@Injectable()
export class WebAuthService extends AuthService {

    private _endpoint: string = null;
    private _authtok: string = null;


    /**
     * the endpoint URL for the customization web service 
     */
    get endpoint() { return this._endpoint; }

    /**
     * the authorization token that gives the user permission to edit the resource metadata
     */
    get authToken() { return this._authcred.token; }

    /**
     * create the AuthService according to the given configuration
     * @param config  the current app configuration which provides the customization service endpoint.
     *                (this is normally provided by the root injector).
     * @param httpcli an HttpClient for communicating with the customization web service
     */
    constructor(config: AppConfig, private httpcli: HttpClient) {
        super();
        this._endpoint = config.get('customizationAPI', '/customization/');
        if (!this._endpoint.endsWith('/')) this._endpoint += "/";
    }

    /**
     * return true if the user is currently authorized to to edit the resource metadata.
     * If false, can attempt to gain authorization via a call to authorizeEditing();
     */
    public isAuthorized(): boolean {
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
     * @param resid     the identifier for the resource to edit
     * @param nologin   if false (default) and the user is not logged in, the browser will be redirected 
     *                  to the authentication service.  If true, redirection will not occur; instead, 
     *                  no user information is set and null is returned if the user is not logged in.  
     */
    public authorizeEditing(resid: string, nologin: boolean = false): Observable<CustomizationService> {
        if (this.authToken)
            return of(new WebCustomizationService(resid, this.endpoint, this.authToken,
                this.httpcli, this.userID));

        // we need an authorization token
        return new Observable<CustomizationService>(subscriber => {
            this.getAuthorization(resid).subscribe(
                (info) => {
                    this._authcred.token = info.token;
                    this._authcred.userDetails = _deepCopy(info.userDetails);
                    if (info.token) {
                        // the user is authenticated and authorized to edit!
                        subscriber.next(
                            new WebCustomizationService(resid, this.endpoint, this.authToken,
                                this.httpcli, info.userDetails.userId)
                        );
                        subscriber.complete();
                    }
                    else if (info.userDetails.userId) {
                        // the user is authenticated but not authorized
                        subscriber.next(null);
                        subscriber.complete();
                    }
                    else {
                        // the user is not authenticated!
                        subscriber.complete();

                        // redirect the browser to the authentication server
                        if (!nologin){
                            this.loginUser();
                        }else {
                            subscriber.next(null);
                            subscriber.complete();
                        }
                    }
                },
                (err) => {
                    if (err['statusCode'] && err.statusCode == 401) {
                        // User needs to log in; redirect the browser to the authentication server
                        if (!nologin){
                            this.loginUser();
                        }else {
                            subscriber.next(null);
                            subscriber.complete();
                        }
                    }
                    else
                        subscriber.error(err);
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
    public getAuthorization(resid: string): Observable<AuthInfo> {
        let url = this.endpoint + "auth/_perm/" + resid;
          // wrap the HttpClient Observable with our own so that we can manage errors
        return new Observable<AuthInfo>(subscriber => {
            this.httpcli.get(url, { headers: { 'Content-Type': 'application/json' } }).subscribe(
                (creds) => {
                    // URL returned OK
                    subscriber.next(creds as AuthInfo);
                },
                (httperr) => {
                  console.log('httperr', httperr);
                    if (httperr.status == 404) {
                        // URL returned Not Found
                        subscriber.next({} as AuthInfo);
                        subscriber.complete();
                    }
                    else if (httperr.status < 100 && httperr.error) {
                        let msg = "Service connection error"
                        if (httperr['message'])
                            msg += ": " + httperr.message
                        if (httperr.error.message)
                            msg += ": " + httperr.error.message
                        if (httperr.status == 0 && httperr.statusText.includes('Unknown'))
                            msg += " (possibly due to CORS restriction?)";
                        subscriber.error(new ConnectionCustomizationError(msg));
                    }
                    else {
                        // URL returned some other error status
                        let msg = "Unexpected error during authorization";
                        // TODO: can we get at body of message when an error occurs?
                        // msg += (httperr.body['message']) ? httperr.body['message'] : httperr.statusText;
                        msg += " (" + httperr.status.toString() + " " + httperr.statusText + ")"
                        subscriber.error(new SystemCustomizationError(msg, httperr.status))
                    }
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
    public loginUser(): void {
        let redirectURL = this.endpoint + "saml/login?redirectTo=" + window.location.href;
        // let redirectURL = this.endpoint + "saml/login?redirectTo=" + window.location.href + "?editmode=true";
        console.log("Redirecting to " + redirectURL + " to authenticate user");
        window.location.assign(redirectURL);
    }
}

/**
 * An AuthService intended for development and testing purposes which simulates interaction 
 * with a authorization service.
 */
@Injectable()
export class MockAuthService extends AuthService {
    private resdata: {} = {};

    /**
     * construct the authorization service
     *
     * @param resmd      the original resource metadata 
     * @param userid     the ID of the user; default "anon"
     */
    constructor(userDetails?: UserDetails) {
        super();
        if (userDetails === undefined) {
            this._authcred = {
                userDetails: {
                userId: "anon",
                userName: "Anon",
                userLastName: "Lee",
                userEmail: "Anon.Lee@nist.gov"
                },
                token: 'fake jwt token'
            }
        }else{
            this._authcred = {
                userDetails: userDetails,
                token: 'fake jwt token'
            }
        }
        
        if (!ngenv.testdata)
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
    public isAuthorized(): boolean {
        return Boolean(this.userDetails);
    }

    /**
     * create a CustomizationService that allows the user to edit the resource metadata 
     * associated with the given ID.
     *
     * @param resid     the identifier for the resource to edit
     * @param nologin   if false (default) and the user is not logged in, the browser will be redirected 
     *                  to the authentication service.  If true, redirection will not occur; instead, 
     *                  no user information is set and null is returned if the user is not logged in.  
     * @param Observable<CustomizationService>  an observable wrapped CustomizationService that should 
     *                  be used to send edits to the customization server.  The service will be null if 
     *                  the user is not authorized.  
     */
    public authorizeEditing(resid: string, nologin: boolean = false): Observable<CustomizationService> {
        // simulate logging in with a redirect 
        if (!this.userDetails){ 
          this.loginUser();}
        if (!this.resdata[resid]){
            return of<CustomizationService>(null);
        }
        return of<CustomizationService>(new InMemCustomizationService(this.resdata[resid]));
    }

    /**
     * redirect the browser to the authentication service, instructing it to return back to 
     * the current landing page.  
     */
    public loginUser(): void {
        let redirectURL = window.location.href + "?editmode=true";
        console.log("Bypassing authentication service; redirecting directly to " + redirectURL);
        if (!this._authcred.userDetails){
            this._authcred = {
                userDetails: {
                userId: "anon",
                userName: "Anon",
                userLastName: "Lee",
                userEmail: "Anon.Lee@nist.gov"
                },
                token: 'fake jwt token'
            }
        } 
        window.location.assign(redirectURL);
    }
}

function _deepCopy(obj) {
    return JSON.parse(JSON.stringify(obj));
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
export function createAuthService(config: AppConfig, httpClient: HttpClient, devmode?: boolean)
    : AuthService {
    if (devmode === undefined)
        devmode = Boolean(ngenv['context'] && ngenv['context']['useCustomizationService']) === false;

    if (!devmode) {
        // production mode
        console.log("Will use configured customization web service");
        return new WebAuthService(config, httpClient);
    }

    // dev mode
    if (!ngenv['context'])
        console.warn("Warning: angular environment is missing context data");
    console.log("Using mock AuthService/CustomizationService");
    return new MockAuthService();
}

