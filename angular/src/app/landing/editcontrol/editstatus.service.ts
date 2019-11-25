import { Injectable, EventEmitter } from '@angular/core';

import { AppConfig } from '../../config/config';

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
    get lastUpdated() : string { return this._lastupdate; }
    private _lastupdate : string = "";   // empty string means unknown
    _setLastUpdated(date : string) { this._lastupdate = date; }

    /**
     * flag indicating whether the landing page is currently being edited.  
     */
    get editMode() : boolean { return this._editmode; }
    private _editmode : boolean = false;
    _setEditMode(val : boolean) { this._editmode = val; }

    private _remoteStart : EventEmitter<any> = new EventEmitter<any>();
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
    public startEditing() : void {
        this._remoteStart.emit(true);
    }
}
