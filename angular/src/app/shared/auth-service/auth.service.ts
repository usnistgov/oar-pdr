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
    baseApiUrl: string;
    loginAPI: string;
    loginRedirectURL: string;
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
        this.customizationApi = this.cfg.get("customizationAPI", "/unconfigured");

        if (this.customizationApi == "/unconfigured")
            throw new Error("Customization api not configured!");

        if (!(this.customizationApi.endsWith('/'))) this.customizationApi = this.customizationApi + '/';
        this.loginAPI = this.customizationApi + "auth/_perm/";
        this.loginRedirectURL = this.customizationApi + "saml/login?redirectTo=";
        this.landingPageService = cfg.get('landingPageService', '/od/id/');
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
        if (apiToken.token != null && apiToken.token != "" && apiToken.userId != null && apiToken.userId != "") {
            this.authToken = apiToken.token;
            console.log("token &&&&&&&&&&&&&&", this.authToken);
            this.setUserId(apiToken.userId);
            this.setAuthenticateStatus(true);
            return "";
        } else if (apiToken.userId != null && apiToken.userId != "") {
            return "You are not authorized.";
        }
    }

    /*
    * If login failed, display error message
    */
    handleTokenError(error: any) {
        var returnMessage: string = "";
        console.log("Error @@@@@@@@@@@@@@@@", error);
        console.log("Error", error.error);
        const JsonParseError = 'Http failure during parsing for';
        const matches = error.message.match(new RegExp(JsonParseError, 'ig'));
        if (error.status === 200 && matches.length === 1) {
            console.log("Test :" + error.message);
            console.log("error.status :" + error.status);
            returnMessage = "200";
        } else if (error.status === 401 || error.status === 0) {
            if (error.error.message.indexOf("UnauthorizedUser") > -1) {
                // Authenticated but not authorized
                this.setUserId(error.Userid);
                this.setAuthenticateStatus(true);
                returnMessage = "You are not authorized.";
            }
            if (error.error.message.indexOf("UnAuthenticated") > -1) {
                // not authenticated
                this.setAuthenticateStatus(false);
                returnMessage = "You are not authenticated.";
            }
        } else if (error.error instanceof ErrorEvent) {
            // A client-side or network error occurred. Handle it accordingly.
            console.error('An error occurred:', error.error.message);
            returnMessage = error.error.message;
        } else {
            // The backend returned an unsuccessful response code.
            // The response body may contain clues as to what went wrong,
            console.error(
                `Backend returned code ${error.status}, ` +
                `body was: ${error.error}`);
            returnMessage = "Error";
        }
        // return an observable with a user-facing error message

        return returnMessage;
    }

    /*
     * Redirect login
     */
    loginUserRedirect() {

        // var redirectURL = this.loginRedirectURL + this.landingPageService + this.commonVarService.getEdiid();
        var redirectURL = this.loginRedirectURL + window.location.href + "?editmode=true";
        console.log("redirectURL:", redirectURL);
        // return this.http.get(redirectURL);
        window.location.replace(redirectURL);
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
        console.log("this.authToken", this.authToken);
        return (this.authToken != "" && this.authToken != undefined && this.authToken != null);
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
