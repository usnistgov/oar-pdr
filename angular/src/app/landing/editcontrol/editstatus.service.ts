import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

import { AppConfig } from '../../config/config';
import { UpdateDetails } from './interfaces';
import { LandingConstants } from '../constants';

/**
 * a service that can be used to monitor the editing status of the landing page.
 *
 * With this service, one can...
 *  * monitor when the landing page is being edited
 *  * learn the ID of the user that is currently logged in
 *  * get the date of the last edit to the draft page
 */
@Injectable({
    providedIn: 'root'
})
export class EditStatusService {
    public EDIT_MODES: any = LandingConstants.editModes;

    /**
     * construct the service
     */
    constructor(private cfg : AppConfig) { }

    /**
     * the date of the last update to the draft landing page.  
     */
    get lastUpdated() : UpdateDetails { return this._lastupdate; }
    private _lastupdate : UpdateDetails = null;   // null object means unknown
    _setLastUpdated(updateDetails : UpdateDetails) { this._lastupdate = updateDetails; }

    /**
     * flag indicating the current edit mode.  
     * Make editMode observable so any component that subscribe to it will
     * get an update once the mode changed.
     */
    _editMode : BehaviorSubject<string> =
        new BehaviorSubject<string>(LandingConstants.editModes.VIEWONLY_MODE);
    _setEditMode(val : string) { 
        this._editMode.next(val); 
    }
    public watchEditMode(subscriber) {
        this._editMode.subscribe(subscriber);
    }

    /**
     * Flag to tell the app to hide the content display or not. 
     * Usecase: to hide server side rendering content while in edit mode and display the content when 
     * browser side rendering is ready.
     */
    _showLPContent: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
    setShowLPContent(val: boolean){
        this._showLPContent.next(val);
    }
    public watchShowLPContent(subscriber) {
        this._showLPContent.subscribe(subscriber);
    }

    /**
     * flag indicating whether we get an error.
     * This flag is used to reset UI display - push the footer to the bottom of the page  
     */
    get hasError() : boolean { return this._error; }
    private _error : boolean = false;
    _setError(val : boolean) { this._error = val; }

    /**
     * Behavior subject to remotely start the edit function. This is used when user login
     * and the page was redirected to current page with parameter 'editmode' set to true.
     */
    private _remoteStart : BehaviorSubject<object> = new BehaviorSubject<object>({resID: "", nologin: false});
    _watchRemoteStart(subscriber) {
        this._remoteStart.subscribe(subscriber);
    }

    /**
     * the ID of the user currently logged in.  
     */
    get userID() : string { return this._userid; }
    private _userid : string = null;
    _setUserID(id : string) { this._userid = id; }
    
    /**
     * a flag indicating whether the current user has been authenticated.
     */
    get authenticated() : boolean { return Boolean(this._userid); }

    /**
     * a flag indicating whether the current user has been authorized to edit the landing page.  
     */
    get authorized() : boolean { return this._authzd; }
    private _authzd : boolean = false;
    _setAuthorized(val : boolean) { this._authzd = val; }

    /**
     * return true if it is possible to edit the landing page.  This will return false 
     * when running as part of the public side of the PDR.
     */
    public editingEnabled() : boolean {
        return this.cfg.get("editEnabled", false);
    }

    /**
     * turn on editing controls allowing the user to edit the metadata
     */
    public startEditing(resID: string = "", nologin: boolean = false) : void {
        this._remoteStart.next({'resID':resID, 'nologin':nologin});
    }
}
