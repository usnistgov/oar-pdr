import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

import { AppConfig } from '../../config/config';
import { UpdateDetails } from './interfaces';

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

    /**
     * construct the service
     */
    constructor(private cfg : AppConfig) {
    }

    /**
     * the date of the last update to the draft landing page.  
     */
    get lastUpdated() : UpdateDetails { return this._lastupdate; }
    private _lastupdate : UpdateDetails = null;   // null object means unknown
    _setLastUpdated(updateDetails : UpdateDetails) { this._lastupdate = updateDetails; }

    /**
     * flag indicating whether the landing page is currently being edited.  
     * Make editMode observable so any component that subscribe to it will
     * get an update once the mode changed.
     */
    // private _editMode : BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
    // _setEditMode(val : boolean) { 
    //     this._editMode.next(val); 
    // }
    // _watchEditMode(subscriber) {
    //     this._editMode.subscribe(subscriber);
    // }

    /**
     * flag indicating whether the landing page is currently being edited.  
     */
    get editMode() : boolean { return this._editmode; }
    private _editmode : boolean = false;
    _setEditMode(val : boolean) { this._editmode = val; }

    /**
     * Behavior subject to remotely start the edit function. This is used when user login
     * and the page was redirected to current page with parameter 'editmode' set to true.
     */
    private _remoteStart : BehaviorSubject<string> = new BehaviorSubject<string>("");
    _watchRemoteStart(subscriber) {
        this._remoteStart.subscribe(subscriber);
    }

    /**
     * BehaviorSubject that force datacart to init data file tree
     */
    private _forceDataFileTreeInit : BehaviorSubject<boolean> = new BehaviorSubject<boolean>(false);
    _watchForceDataFileTreeInit(subscriber) {
        this._forceDataFileTreeInit.subscribe(subscriber);
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
    public startEditing(resID: string = "") : void {
        this._remoteStart.next(resID);
    }

    /**
     * Force datacart to init data file tree
     */
    public forceDataFileTreeInit() : void {
        this._forceDataFileTreeInit.next(true);
    }
}
