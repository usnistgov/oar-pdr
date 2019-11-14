import { Injectable, EventEmitter } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Subject } from 'rxjs';

import { UserMessageService } from '../../frame/usermessage.service';
import { CustomizationService } from './customization.service';

/**
 * a service that receives updates to the resource metadata from update widgets.
 * 
 * This service mediates the updates between user-facing editing widgets, the 
 * CustomizationService (which saves updates in "draft" record stored on the server), 
 * and a controller object--namely, the EditControlPanel--that handles updating the 
 * resource metadata used to drive the landing page display.  In particular, editing
 * widgets send their metadata updates to this class (via update()); this class will 
 * then forward the changes to the CustomizationService and forward the full, updated 
 * record to the controller object.
 *
 * This class also works with a UserMessageService to alert the user with messages when 
 * things go wrong.  
 */
@Injectable()
export class MetadataUpdateService {

    private mdres : Subject<{}> = new Subject<{}>();
    private custsvc : CustomizationService = null;
    private originalRec : any = null;
    private origfields : {} = {};   // keeps track of orginal metadata so that they can be undone

    private _lastupdate : string = "";   // empty string means unknown
    get lastUpdate() { return this._lastupdate; }
    set lastUpdate(date : string) {
        this._lastupdate = date;
        this.updated.emit(this._lastupdate);
    }

    /**
     * any Observable that will send out the date of the last update each time the metadata
     * is updated via this service.  If the date is an empty string, there are no updates 
     * pending for submission.  
     */
    public updated : EventEmitter<string> = new EventEmitter<string>();

    /**
     * a flag that indicates that whether the landing page is in edit mode, i.e. displays 
     * buttons for editing individual bits of metadata.  
     *
     * Note that this flag should only be updated by the controller (i.e. EditControlComponent) 
     * that subscribes to this class (via _subscribe()).
     */
    private _editmode : boolean = false;
    get editMode() { return this._editmode; }
    set editMode(engage : boolean) { this._editmode = engage; } 

    /**
     * construct the service
     * 
     * @param custsvc   the CustomizationService to use to send updates to the 
     *                  server.  
     */ 
    constructor(private msgsvc  : UserMessageService,
                private datePipe: DatePipe)
    { } 

    /*
     * subscribe to updates to the metadata.  This is intended for connecting the 
     * service to the EditControlPanel.
     */
    _subscribe(controller) : void {
        this.mdres.subscribe(controller);
    }
    _setOriginalMetadata(md : any) {
        this.originalRec = md;
    }

    _setCustomizationService(svc : CustomizationService) : void {
        this.custsvc = svc;
    }

    /**
     * update the resource metadata.
     * 
     * The given object will be merged into the resource metadata.  The update will be 
     * sent to the server, and the full and updated version of the metadata will be 
     * sent to the metadata controller.
     *
     * To facilitate the undo capability, updates are associated with a name--the subsetname-- 
     * that is unique to the client component requesting the update.  When the client is 
     * updating a single property, the name is typically the name of the property; if a client
     * updates multiple property, some other name can be used.  A client can roll back the 
     * updates it requested via undo() by using the same name that identifies portion of the 
     * data to undo.  This framework assumes that no two clients update the same metadata 
     * property.  
     *
     * @param subsetname  a label that distinguishes the metadata properties being set 
     *             by this call.  Typically, this is the same name as the single property 
     *             being updated; however, if multiple properties are being updated, this 
     *             name can be an arbitrary label.  
     * @param md   an object containing the portion of the resource metadata that 
     *             should be updated.  
     * @return Promise<boolean>  -  result is true if the update was successful, false if 
     *             there was an issue.  Note that the underlying CustomizationService will
     *             take care of reporting the reason.  This allows the caller in charge of 
     *             getting updates to have its UI react accordingly.
     */
    public update(subsetname : string, md : {}) : Promise<boolean> {
        if (! this.custsvc) {
            console.error("Attempted to update without authorization!  Ignoring update.");
            return new Promise<boolean>((resolve, reject) => {
                resolve(false);
            });
        }

        // establish the original state for this subset of metadata (so that it this update
        // can be undone).
        if (this.originalRec) {
            if (! this.origfields[subsetname]) 
                this.origfields[subsetname] = {};
            for (let prop in md) {
                if (this.origfields[subsetname][prop] === undefined) {
                    if (this.originalRec[prop] === undefined)
                        this.origfields[subsetname][prop] = this.originalRec[prop]; 
                    else 
                        this.origfields[subsetname][prop] = null;   // TODO: problematic; need to clean-up nulls
                }
            }
        }
        
        this.stampUpdateDate();
        return new Promise<boolean>((resolve, reject) => {
            this.custsvc.updateMetadata(md).subscribe(
                (res) => {
                    // console.log("###DBG  Draft data returned from server:\n  ", res)
                    this.mdres.next(res);
                    resolve(true);
                },
                (err) => {
                    // err will be a subtype of CustomizationError
                    if (err.type == 'user') {
                        console.error("Failed to save metadata changes: user error:" + err);
                        this.msgsvc.error(err.message)
                    }
                    else {
                        console.error("Failed to save metadata changes: server/system error:" + err);
                        this.msgsvc.syserror(err.message)
                    }
                    resolve(false);
                }
            );
        });
    }

    /**
     * undo a previously submitted update by its name
     * 
     * @param subsetname    the name for the metadata that was used in the call to update() which 
     *                      should be undone.
     * @return Promise<boolean>  -  result is true if the undo was successful, false if 
     *             there was an issue, including that there was nothing to undo.  Note that this 
     *             MetadataUpdateService instance will take care of reporting the reason.  This 
     *             response allows the caller in charge of getting updates to have its UI react
     *             accordingly.
     */
    public undo(subsetname : string) {
        if (this.origfields[subsetname] === undefined) {
            // Nothing to undo!
            console.warn("Undo called on "+subsetname+": nothing to undo");
            return new Promise<boolean>((resolve, reject) => {
                resolve(false);
            });
        }
        
        // if there are no other updates registered, we will just request that the the draft be
        // deleted on the server.  So is this the only update we have registered?
        let finalUndo = Object.keys(this.origfields).length == 1 &&
                        this.origfields[subsetname] !== undefined;

        if (finalUndo) {
            // Last set to be undone; just delete the draft on the server
            console.log("Last undo; discarding draft on server");
            return new Promise<boolean>((resolve, reject) => {
                this.custsvc.discardDraft().subscribe(
                    (res) => {
                        this.origfields = {};
                        this.forgetUpdateDate();
                        this.mdres.next(res);
                        resolve(true);
                    },
                    (err) => {
                        // err will be a subtype of CustomizationError
                        if (err.type == 'user') {
                            console.error("Failed to undo metadata changes: user error:" + err);
                            this.msgsvc.error(err.message)
                        }
                        else {
                            console.error("Failed to undo metadata changes: server/system error:" + err);
                            this.msgsvc.syserror(err.message)
                        }
                        resolve(false);
                    }
                );
            });
        }
        else {
            // Other updates are still registered; just undo the specified one
            console.log("Last undo; discarding draft on server");
            return new Promise<boolean>((resolve, reject) => {
                this.custsvc.updateMetadata(this.origfields[subsetname]).subscribe(
                    (res) => {
                        delete this.origfields[subsetname];
                        this.mdres.next(res);
                        resolve(true);
                    },
                    (err) => {
                        // err will be a subtype of CustomizationError
                        if (err.type == 'user') {
                            console.error("Failed to undo metadata changes: user error:" + err);
                            this.msgsvc.error(err.message)
                        }
                        else {
                            console.error("Failed to undo metadata changes: server/system error:" + err);
                            this.msgsvc.syserror(err.message)
                        }
                        resolve(false);
                    }
                );
            });
        }
    }

    /**
     * return true if metadata associated with a given name have been updated.  This will return 
     * false either if the metadata was never updated or if the update was previously undone via 
     * undo().
     * @param subsetname    the name for the set of metadata of interest.
     */
    public fieldUpdated(subsetname : string) : boolean {
        return this.origfields[subsetname] != undefined;
    }

    /**
     * load the latest draft of the resource metadata.
     * 
     * retrieve the latest draft of the resource metadata from the server and forward it
     * to the controller for display to the user.  
     */
    public loadDraft() : void {
        if (! this.custsvc) {
            console.error("Attempted to update without authorization!  Ignoring update.");
            return;
        }
        
        console.log("Loading draft metadata");
        this.custsvc.getDraftMetadata().subscribe(
            (res) => {
                // console.log("Draft data returned from server:\n  ", res)
                this.mdres.next(res);
            },
            (err) => {
                // err will be a subtype of CustomizationError
                if (err.type = 'user') {
                    console.error("Failed to retrieve draft metadata changes: user error:" + err);
                    this.msgsvc.error(err.message)
                }
                else {
                    console.error("Failed to retrieve draft metadata changes: server error:" + err);
                    this.msgsvc.syserror(err.message)
                }
            }
        );
    }

    /**
     * record the current date/time as the last time this data was updated.
     */
    public stampUpdateDate() : string {
        this.lastUpdate = this.datePipe.transform(new Date(), "MMM d, y, h:mm:ss a");
        return this.lastUpdate;
    }

    /**
     * erase the date of last update.  This might be done if the last update was undone. 
     */
    public forgetUpdateDate() : void {
        this.lastUpdate = "";
    }

    /**
     * Utility function for editing widgets that checks if any difference between the current metadata and 
     * its original 
     */
    public dataEdited(currentData: {}, Originaldata: {}) {
        if ((currentData == undefined || currentData == "") &&
            (Originaldata == undefined || Originaldata == ""))
        {
            return false;
        } else {
            return JSON.stringify(currentData) != JSON.stringify(Originaldata);
        }
    }
}
