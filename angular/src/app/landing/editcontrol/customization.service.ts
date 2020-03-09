import { HttpClient, HttpResponse } from '@angular/common/http';
import { Observable, of, throwError, Subscriber } from 'rxjs';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

/**
 * a service for commiting metadata changes to a draft version stored on the server.
 *
 * Normally, this service is created via the AuthService after the user has successfully 
 * logged in and the AuthService determines the user is authorized to edit the record.  
 *
 * This abstract class allows for different implementations for different execution 
 * contexts.  In particular, mock versions can be provided for development and testing 
 * contexts.
 */
export abstract class CustomizationService {

    private _resid : string = null;
    get resid() : string { return this._resid; }

    private _userID : string = null;
    get userId() : string { return this._userID; }

    /**
     * construct the service instance 
     * 
     * @param resId      the identifier for the resource metadata being updated.
     */
    constructor(resId : string, userID?: string) {
        this._resid = resId
        this._userID = userID;
    }

    /**
     * retrieve the latest draft resource metadata record from the server-side 
     * customization service.  
     */
    public abstract getDraftMetadata() : Observable<Object>;

    /**
     * update some portion of the resource metadata, and return the full modified 
     * draft.
     * 
     * @param md   an object containing resource properties to be updated.  
     */
    public abstract updateMetadata(md : Object) : Observable<Object>;

    /**
     * commit the changes in the draft to the saved version
     */
    public abstract saveDraft() : Observable<Object>;

    /**
     * discard the changes in the draft, reverting to the original metadata
     */
    public abstract discardDraft() : Observable<Object>;

    /**
     * Tell backend that the editing is done
     */
    public abstract doneEditing() : Observable<Object>;
}

/**
 * an implementation of the CustomizationService that caches metadata updates on the 
 * server via a web service.  
 *
 * This implementation is intended for use in production.  
 */
export class WebCustomizationService extends CustomizationService {

    readonly draftapi : string = "api/draft/";
    readonly saveapi : string = "api/savedrecord/";

    /**
     * construct the customization service
     *
     * @param resid      the identifier for the resource metadata being updated.
     * @param endpoint   the web service endpoint URL for saving changes.  This URL
     *                   should *not* include the identifier for the record being edited.
     * @param token      the authorization token that allows metadata edits to be 
     *                   submitted to the endpoint
     * @param httpcli    the HttpClient service to use to submit web service requests
     */
    constructor(resid : string, private endpoint : string, private token : string,
                private httpcli : HttpClient, userId: string)
    {
        super(resid, userId);
        if (! endpoint.endsWith('/')) endpoint += '/';
    }

    /**
     * retrieve the latest draft resource metadata record from the server-side 
     * customization service.  
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with a customized error object, one of 
     *                   AuthCustomizationError -- if the request is made without being 
     *                     authenticated or authorized.  This could happen if the user credentials
     *                     expire during the session. 
     *                   NotFoundCustomizationError -- if the ID for record that was requested 
     *                     cannot be found. This should not happen normally.  
     *                   ConnectionCustomizationError -- if it was not possible to connect to the 
     *                     customization server, even to get back an error response.  
     */
    public getDraftMetadata() : Observable<Object> {

        // To transform the output with proper error handling, we wrap the
        // HttpClient.get() Observable with our own Observable
        //
        return new Observable<Object>(subscriber => {
            let url = this.endpoint + this.draftapi + this.resid;
            let obs : Observable<Object> = 
                this.httpcli.get(url, { headers: { "Authorization": "Bearer " + this.token } });
            this._wrapRespObs(obs, subscriber);
        });
    }

    private _wrapRespObs(obs : Observable<Object>, subscriber : Subscriber<Object>) : void {
        obs.subscribe(
            (jsonbody) => {
                // if (!jsonbody || !jsonbody['@id'])
                //     console.warn("Data returned from customization service does not look like a "+
                //                  "NERDm resource: "+JSON.stringify(jsonbody));
                subscriber.next(jsonbody);
            },
            (httperr) => {   // this will be an HttpErrorResponse
                let msg = "";
                let err = null;
                console.log("httperr.status", httperr.status);
                if (httperr.status == 401) {
                    msg += "Authorization Error (401)";
                    // TODO: can we get at body of message when an error occurs?
                    // if (httperr.body['message']) msg += ": " + httperr.body['message'];
                    err = new AuthCustomizationError(msg, httperr.status);
                }
                else if (httperr.status == 404) {
                    msg += "Record Not Found (404)"
                    // TODO: can we get at body of message when an error occurs?
                    // if (httperr.body['message']) msg += ": " + httperr.body['message'];
                    msg += " (Is the service endpoint correct?)"
                    err = new NotFoundCustomizationError(msg, httperr.status);
                }
                else if (httperr.status < 100 && httperr.error) {
                    msg = httperr.error.message
                    err = new ConnectionCustomizationError("Service connection error: "+msg)
                }
                else {
                    msg += "Unexpected Customization Error";
                    if (httperr.status > 0) msg += "(" + httperr.status.toString() + ")";
                    // TODO: can we get at body of message when an error occurs?
                    // if (httperr.body['message']) msg += ": " + httperr.body['message'];
                    err = new SystemCustomizationError(msg, httperr.status);
                }
                subscriber.error(err);
            }
        );
    }

    /**
     * update some portion of the resource metadata, and return the full modified 
     * draft.
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with a customized error object, one of 
     *                   AuthCustomizationError -- if the request is made without being 
     *                     authenticated or authorized.  This could happen if the user credentials
     *                     expire during the session. 
     *                   NotFoundCustomizationError -- if the ID for record that was requested 
     *                     cannot be found. This should not happen normally.  
     *                   ConnectionCustomizationError -- if it was not possible to connect to the 
     *                     customization server, even to get back an error response.  
     */
    public updateMetadata(md : Object) : Observable<Object> {
        // To transform the output with proper error handling, we wrap the
        // HttpClient.patch() Observable with our own Observable
        //
        return new Observable<Object>(subscriber => {
            let url = this.endpoint + this.draftapi + this.resid;
            let body = JSON.stringify(md);
            let obs : Observable<Object> = 
                this.httpcli.patch(url, body, { headers: { "Authorization": "Bearer " + this.token } });
            this._wrapRespObs(obs, subscriber);
        });
    }
  
    /**
     * commit the changes in the draft to the saved version
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with a customized error object, one of 
     *                   AuthCustomizationError -- if the request is made without being 
     *                     authenticated or authorized.  This could happen if the user credentials
     *                     expire during the session. 
     *                   NotFoundCustomizationError -- if the ID for record that was requested 
     *                     cannot be found. This should not happen normally.  
     *                   ConnectionCustomizationError -- if it was not possible to connect to the 
     *                     customization server, even to get back an error response.  
     */
    public saveDraft() : Observable<Object> {

        // To transform the output with proper error handling, we wrap the
        // HttpClient.put() Observable with our own Observable
        //
        return new Observable<Object>(subscriber => {
            let url = this.endpoint + this.saveapi + this.resid;
            let obs : Observable<Object> = 
                this.httpcli.put(url, {}, { headers: { "Authorization": "Bearer " + this.token } });
            this._wrapRespObs(obs, subscriber);
        });
    }

    /**
     * discard the changes in the draft, reverting to the original metadata
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with a customized error object, one of 
     *                   AuthCustomizationError -- if the request is made without being 
     *                     authenticated or authorized.  This could happen if the user credentials
     *                     expire during the session. 
     *                   NotFoundCustomizationError -- if the ID for record that was requested 
     *                     cannot be found. This should not happen normally.  
     *                   ConnectionCustomizationError -- if it was not possible to connect to the 
     *                     customization server, even to get back an error response.  
     */
    public discardDraft() : Observable<Object> {

        // To transform the output with proper error handling, we wrap the
        // HttpClient.delete() Observable with our own Observable
        //
        return new Observable<Object>(subscriber => {
            let url = this.endpoint + this.draftapi + this.resid;
            let obs : Observable<Object> = 
                this.httpcli.delete(url, { headers: { "Authorization": "Bearer " + this.token } });
            this._wrapRespObs(obs, subscriber);
        });
    }

    /**
     * Ends the editing session
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with a customized error object, one of 
     *                   AuthCustomizationError -- if the request is made without being 
     *                     authenticated or authorized.  This could happen if the user credentials
     *                     expire during the session. 
     *                   NotFoundCustomizationError -- if the ID for record that was requested 
     *                     cannot be found. This should not happen normally.  
     *                   ConnectionCustomizationError -- if it was not possible to connect to the 
     *                     customization server, even to get back an error response.  
     */
    public doneEditing() : Observable<Object> {
      // To transform the output with proper error handling, we wrap the
      // HttpClient.patch() Observable with our own Observable
      //
      return new Observable<Object>(subscriber => {
          let url = this.endpoint + this.draftapi + this.resid;
          let body = { "_editStatus": "done" };
          let obs : Observable<Object> = 
              this.httpcli.patch(url, body, { headers: { "Authorization": "Bearer " + this.token } });
          this._wrapRespObs(obs, subscriber);
      });
  }
}

/**
 * a CustomizationService that tracks updates to the metadata record in memory
 * 
 * This implementation exists primarily for testing and development purposes.
 */
export class InMemCustomizationService extends CustomizationService {

    private origmd : Object = null;
    private resmd : Object = null;

    /**
     * construct the customization service
     *
     * @param resmd      the original resource metadata 
     */
    constructor(resmd : Object) {
        super((resmd && resmd['ediid']) ? resmd['ediid'] : "resmd");
        this.origmd= resmd;
        this.resmd = (resmd == null) ? null : JSON.parse(JSON.stringify(resmd))
    }

    /**
     * retrieve the latest draft resource metadata record from the server-side 
     * customization service.  
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with an instance of a CustomizationError.
     *                   In this implementation, failure is not possible.
     */
    public getDraftMetadata() : Observable<Object> {
        return of<Object>(this.resmd);
    }


    /**
     * Ends the editing session
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with an instance of a CustomizationError.
     */
    public doneEditing() : Observable<Object> {
        return of<Object>(this.resmd);
    }    

    /**
     * commit the changes in the draft to the saved version
     */
    public saveDraft() : Observable<Object> {
        this.origmd = JSON.parse(JSON.stringify(this.resmd));
        return of<Object>(this.resmd);
    }

    /**
     * discard the changes in the draft, reverting to the original metadata
     */
    public discardDraft() : Observable<Object> {
        this.resmd = JSON.parse(JSON.stringify(this.origmd));
        return of<Object>(this.resmd);
    }

    /**
     * update some portion of the resource metadata, and return the full modified 
     * draft.
     *
     * @return Observable<Object> -- on success, the subscriber's success (next) function is 
     *                   passed the Object representing the full draft metadata record.  On 
     *                   failure, error function is called with an instance of a CustomizationError.
     */
    public updateMetadata(md : Object) : Observable<Object> {
      if (! md)
          return throwError(new SystemCustomizationError("No update data provided"));

      for(let prop in md) {
          this.resmd[prop] = JSON.parse(JSON.stringify(md[prop]));
      }
      return of<Object>(this.resmd);
  }    
}


/**
 * an error interacting with the CustomizationService.  This serves as a base class 
 * for different error types resulting from service interactions.
 */
export class CustomizationError {

    /**
     * a label identifying the type of error
     */
    private _type
    get type() { return this._type; }

    /**
     * create the error
     * 
     * @param type     a label that idenfifies the type of the error (which parallels 
     *                 the class type.
     * @param message  a description of the specific error
     * @param statusCode  a numerical qualifier for the particular error; this is used 
     *                 to hold an HTTP status code which should be 0 no such service is 
     *                 involved, and 1 when the attempt to connect to an underlying fails.
     *                 Other values less than 100 can be used for errors associated with 
     *                 connecting to an underlying service that is not web-based.  
     */
    constructor(type : string, public message : string, public statusCode : number = 0) {
        this._type = type;
    }
}

/**
 * a CustomizationError that indicates a failure connecting to a remote service.  
 * For example, this error would be raised if the remote service is down.  This 
 * error would normally not be raised if the service is up and capable of returning 
 * an error response.  
 */
export class ConnectionCustomizationError extends CustomizationError {

    /**
     * create the error instance
     */
    constructor(message : string) {
        super("conn", message, 1);
    }
}

/**
 * a CustomizationError that indicates an authorization failure, including attempting 
 * to update metadata without authentication or authorization.  In particular, this 
 * error should be raised if an authorization credential times out.  
 */
export class AuthCustomizationError extends CustomizationError {

    /**
     * create the error instance
     */
    constructor(message : string, statusCode = 401) {
        super("auth", message, statusCode);
    }
}

/**
 * an CustomizationError reflecting an unexpected condition or result while 
 * using the CustomizationService.
 */
export class SystemCustomizationError extends CustomizationError {

    /**
     * create the error instance
     */
    constructor(message : string, statusCode = 2) {
        super("sys", message, statusCode);
    }
}

/**
 * a CustomizationError that is a result of a incorrect user action or input.  The error message
 * should be instructive to a user about what was done incorrectly.  
 */
export class UserInputCustomizationError extends CustomizationError {

    /**
     * create the error instance
     */
    constructor(message : string, statusCode = 3) {
        super("user", message, statusCode);
    }
}

/**
 * a CustomizationError that indicates that the metadata record cannot be found using the handle
 * provided.  This reflect either a non-existent identifier or an incorrect service endpoint.
 */
export class NotFoundCustomizationError extends CustomizationError {

    /**
     * create the error instance
     */
    constructor(message : string, statusCode = 4) {
        super("notfound", message, statusCode);
    }
}

