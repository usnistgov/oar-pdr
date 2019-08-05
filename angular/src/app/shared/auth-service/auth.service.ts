import { Injectable } from '@angular/core';
import { HttpHeaders, HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';
import { Router } from '@angular/router';
import { CommonVarService } from '../../shared/common-var';
import { ApiToken } from "./ApiToken";

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  authenticatedSub = new BehaviorSubject<boolean>(false);
  _tokenName = "authToken";
  _userid = this.commonVarService._userid;
  ediid: string;
  authToken: string;

  httpOptions = {
    headers: new HttpHeaders({ 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': 'https://pn110559.nist.gov' }),
    withCredentials: true,
  };

  constructor(
    private http: HttpClient,
    private commonVarService: CommonVarService,
    private router: Router) {
    this.ediid = this.commonVarService.getEdiid();
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
    this.authenticatedSub.next(value);
  }

  /*
  *  Send http login request
  */
  loginUser() {
    return this.http.get(this.commonVarService.getLoginURL(), this.httpOptions);
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
  handleTokenSuccess(apiToken: ApiToken) {
    this.authToken = apiToken.token;
    var commonVarService = this.commonVarService;
    this.setToken(apiToken.token).then((result) => {
      this.setUserId(apiToken.userId).then((res) => {
        this.setUserId(apiToken.userId);
      })
    })
  }

  /*
  * If login failed, display error message
  */
  handleTokenError(error: HttpErrorResponse) {

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

    // console.log(error.status);
    // console.log(error.message);
    if (error.status === 401) {
      console.log(error.status);
      // this.showUnauthorizedMessage = true;
      setTimeout(() => window.location.replace('https://pn110559.nist.gov/saml-sp/saml/login'), 4000);
    }
  }

  /*
   * Logout user, reload pdr landing page
   */
  logoutUser() {
    this.removeToken(); 
    this.removeUserId();
    this.router.navigate(['/od/id/', this.commonVarService.getEdiid()], { fragment: '' });
  }

  /*
   * Get stored token
   */
  setToken(token: any) {
    return Promise.resolve(localStorage.setItem(this._tokenName, token));
  }

  /*
   * Get stored token
   */
  getToken() {
    return localStorage.getItem(this._tokenName)
  }

  /*
   * Remove stored token
   */
  removeToken() {
    localStorage.removeItem(this._tokenName);
  }

    /*
   * Get stored token
   */
  setUserId(userid: any) {
    return Promise.resolve(localStorage.setItem(this._userid, userid));
  }

  /*
   * Get stored token
   */
  getUserId() {
    return localStorage.getItem(this._userid)
  }

  /*
   * Remove stored token
   */
  removeUserId() {
    localStorage.removeItem(this._userid);
  }

  /*
   * Determine if the user is logged in by checking the existence of the token
   */
  loggedIn() {
    return !!this.getToken();
  }
}
