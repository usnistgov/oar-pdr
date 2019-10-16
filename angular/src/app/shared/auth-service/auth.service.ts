import { Injectable, OnInit } from '@angular/core';
import { HttpHeaders, HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { Router } from '@angular/router';
import { CommonVarService } from '../../shared/common-var';
import { ApiToken } from "./ApiToken";
import { isPlatformBrowser } from '@angular/common';
import { PLATFORM_ID, APP_ID, Inject } from '@angular/core';
import { AppConfig } from '../../config/config';

@Injectable({
    providedIn: 'root'
})
export class AuthService implements OnInit {
    authenticatedSub = new BehaviorSubject<boolean>(false);
    _tokenName = "authToken";
    userId: string;
    userIdFieldName = "userid";
    ediid: string;
    authToken: string;
    baseApiUrl: string = "https://pn110559.nist.gov/saml-sp/api/mycontroller";
    // loginURL: string = "https://pn110559.nist.gov/saml-sp/auth/token";
    // loginURL: string = "Https://oardev.nist.gov/customization/saml/login";
    loginAPI: string = "https://datapub.nist.gov/customization/auth/_perm/";
    tokenAPI: string = "Https://oardev.nist.gov/customization/auth/token/";
    loginRedirectURL: string = 'https://datapub.nist.gov/customization/saml/login?redirectTo=';
    useridSub = new BehaviorSubject<string>('');
    inBrowser: boolean = false;
    Landingpageurl: string;
    isAuthenticated: boolean = false;

    httpOptions = {
        headers: new HttpHeaders({ 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': 'https://datapub.nist.gov' }),
        withCredentials: true,
    };

    constructor(
        private http: HttpClient,
        private commonVarService: CommonVarService,
        private router: Router,
        private cfg: AppConfig,
        @Inject(PLATFORM_ID) private platformId: Object) {
        this.inBrowser = isPlatformBrowser(platformId);
        this.loginAPI = this.cfg.get("loginAPI", "/customization/auth/_perm/");
        this.tokenAPI = this.cfg.get("tokenAPI", "/customization/auth/token/");
        this.loginRedirectURL = this.cfg.get("loginRedirectURL", "/customization/saml/login?redirectTo=");
    }

    ngOnInit() {
        this.ediid = this.commonVarService.getEdiid();
        this.Landingpageurl = 'od/id/' + this.ediid;
    }

    /**
      * Watch authenticate status
      **/
    watchAuthenticateStatus(): Observable<any> {
        return this.authenticatedSub.asObservable();
    }

    /**
     * Set authenticate status
     **/
    setAuthenticateStatus(value: boolean) {
        this.isAuthenticated = value;
        this.authenticatedSub.next(value);
    }

    /*
    *  Send http login request
    */
    loginUser(): Observable<any> {
        // return this.http.get(this.loginURL, this.httpOptions);
        return this.http.get(this.loginAPI + this.commonVarService.getEdiid(), this.httpOptions);
    }

    /*
    *  Handle login
    */
    login() {
        this.loginUser()
            .subscribe(
                res => {
                    this.handleTokenSuccess(res as ApiToken);
                },
                err => {
                    this.handleTokenError(err);
                }
            )
    }


    /*
    *  Request token
    */
    requestToken(): Observable<any> {
        return this.http.get(this.tokenAPI);
    }

    /*
    * If login succeed, set the token and user id
    */
    handleTokenSuccess(apiToken: any) {
        console.log("response:", apiToken);
        this.authToken = apiToken.token;
        var commonVarService = this.commonVarService;
        this.setToken(apiToken.token).then((result) => {
            this.setUserId(apiToken.userId);
            this.setAuthenticateStatus(true);
        })
    }

    /*
    * If login failed, display error message
    */
    handleTokenError(error: any) {
        console.log("pased Error", error);
        if (error.error instanceof ErrorEvent) {
            // A client-side or network error occurred. Handle it accordingly.
            console.error('An error occurred:', error.error.message);
        } else {
            // The backend returned an unsuccessful response code.
            // The response body may contain clues as to what went wrong,
            console.error(
                `Backend returned code ${error.status}, ` +
                `body was: ${error.error}`);
        }
        // return an observable with a user-facing error message

        if (error.status === 401) {
            if (error.message.indexOf("Unauthorizeduser") > -1) {
                // Authenticated but not authorized
                this.setUserId(error.Userid);
                this.setAuthenticateStatus(true);
            }
            if (error.message.indexOf("UnAuthenticated") > -1) {
                // not authenticated
                this.setAuthenticateStatus(false);
                this.loginUserRedirect();
            }
            // setTimeout(() => window.location.replace('https://pn110559.nist.gov/saml-sp/saml/login'), 4000);
        }
    }

    /*
     * Redirect login
     */
    loginUserRedirect() {
        this.router.navigate([this.loginRedirectURL + this.Landingpageurl]);
    }

    /*
     * Logout user, reload pdr landing page
     * If refresh set to true, reload the page
     */
    logoutUser(noRefresh?: boolean) {
        this.removeToken();
        this.removeUserId();
        this.setAuthenticateStatus(false);
        if (!noRefresh || noRefresh == undefined) {
            console.log("Refresh page...");
            this.router.navigate(['/od/id/', this.commonVarService.getEdiid()], { fragment: '' });
        }
    }

    /*
     * Get stored token
     */
    setToken(token: any) {
        console.log("this._tokenName", this._tokenName);
        if (this.inBrowser)
            return Promise.resolve(localStorage.setItem(this._tokenName, token));
        else
            return Promise.resolve();
    }

    /*
     * Get stored token
     */
    getToken() {
        if (this.inBrowser)
            return localStorage.getItem(this._tokenName);
        else
            return null;
    }

    /*
     * Remove stored token
     */
    removeToken() {
        if (this.inBrowser)
            localStorage.removeItem(this._tokenName);
    }

    /*
   * Get stored token
   */
    setUserIdLocalStorage(userid: any) {
        console.log("this.userIdFieldName", this.userIdFieldName);
        if (this.inBrowser)
            return Promise.resolve(localStorage.setItem(this.userIdFieldName, userid));
        else
            return Promise.resolve();
    }

    /*
     * Get stored token
     */
    getUserId() {
        if (this.inBrowser)
            return localStorage.getItem(this.userIdFieldName)
        else
            return "";
    }

    /*
     * Remove stored token
     */
    removeUserId() {
        if (this.inBrowser)
            localStorage.removeItem(this.userIdFieldName);
    }

    /*
     * Determine if the user is logged in by checking the existence of the token
     */
    authorized() {
        if (this.inBrowser)
            return !!this.getToken();
        else
            return false;
    }

    authenticated(){
        return this.isAuthenticated;
    }
    /*
     * Return JWT name
     */
    getJWTName() {
        return this._tokenName;
    }

    getBaseApiUrl() {
        return this.baseApiUrl;
    }


    /**
     * Set user ID
     **/
    setUserId(value: string) {
        this.setUserIdLocalStorage(value).then((res) => {
            this.useridSub.next(value);
        });
    }

    /**
    * Watching User ID
    **/
    watchUserId(): Observable<string> {
        return this.useridSub.asObservable();
    }
}
