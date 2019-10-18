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
    customizationApi: string;
    baseApiUrl: string = "https://pn110559.nist.gov/saml-sp/api/mycontroller";
    // loginURL: string = "https://pn110559.nist.gov/saml-sp/auth/token";
    // loginURL: string = "Https://oardev.nist.gov/customization/saml/login";
    loginAPI: string = "https://oardev.nist.gov/customization/auth/_perm/";
    loginRedirectURL: string = 'https://datapub.nist.gov/customization/saml/login?redirectTo=';
    landingPageService: string = "/od/id/";
    useridSub = new BehaviorSubject<string>('');
    inBrowser: boolean = false;
    Landingpageurl: string;
    isAuthenticated: boolean = false;

    httpOptions = {
        headers: new HttpHeaders({ 'Content-Type': 'application/json' }),
        withCredentials: true,
    };

    constructor(
        private http: HttpClient,
        private commonVarService: CommonVarService,
        private router: Router,
        private cfg: AppConfig,
        @Inject(PLATFORM_ID) private platformId: Object) {
        this.inBrowser = isPlatformBrowser(platformId);
        this.customizationApi = this.cfg.get("customizationApi", "/customization");
        // this.customizationApi = "https://oardev.nist.gov/customization/";
        if (!(this.customizationApi.endsWith('/'))) this.customizationApi = this.customizationApi + '/';
        this.loginAPI = this.customizationApi + "auth/_perm/";
        this.loginRedirectURL = this.customizationApi + "saml/login?redirectTo=";
        this.landingPageService = cfg.get('landingPageService', '/od/id/');
        // this.landingPageService = "https://oardev.nist.gov/od/id/";
    }

    ngOnInit() {
        this.ediid = this.commonVarService.getEdiid();
        this.Landingpageurl = this.landingPageService + this.ediid;
        console.log('this.Landingpageurl', this.Landingpageurl);
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
        var loginUrl = this.loginAPI + this.commonVarService.getEdiid();
        console.log("Login URL:", loginUrl)
        return this.http.get(loginUrl, this.httpOptions);
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
    * If login succeed, set the token and user id
    */
    handleTokenSuccess(apiToken: any) {
        console.log("response:", apiToken);
        this.authToken = apiToken.token;
        this.setUserId(apiToken.userId);
        this.setAuthenticateStatus(true);

    }

    /*
    * If login failed, display error message
    */
    handleTokenError(error: any) {
        console.log("pased Error", error.status);
        const JsonParseError = 'Http failure during parsing for';
        const matches = error.message.match(new RegExp(JsonParseError, 'ig'));
        if (error.status === 200 && matches.length === 1) {
            console.log("Test :" + error.message);
            var samlurl = error.message.replace("Http failure during parsing for", "");
            window.location.replace(samlurl);
        }

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
    loginUserRedirect(): Observable<any> {
        
        // var redirectURL = this.loginRedirectURL + this.landingPageService + this.commonVarService.getEdiid();
        var redirectURL = this.loginRedirectURL + window.location.href;
        console.log("redirectURL:", redirectURL);
        // this.router.navigate([redirectURL]);
        return this.http.get(redirectURL);
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
    getToken() {
        return this.authToken;
    }

    /*
     * Remove stored token
     */
    removeToken() {
        this.authToken = "";
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
        return this.userId;
    }

    /*
     * Remove stored token
     */
    removeUserId() {
        this.userId = "";
    }

    /*
     * Determine if the user is logged in by checking the existence of the token
     */
    authorized() {
        return (this.authToken != "")
    }

    authenticated() {
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
        this.userId = value;
        this.useridSub.next(value);
    }

    /**
    * Watching User ID
    **/
    watchUserId(): Observable<string> {
        return this.useridSub.asObservable();
    }
}
