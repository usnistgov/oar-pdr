import { Injectable, EventEmitter, ViewChild } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Subject } from 'rxjs';

import { UserMessageService } from '../../frame/usermessage.service';
import { CustomizationService } from './customization.service';
import { NerdmRes } from '../../nerdm/nerdm';
import { Observable, of, throwError, Subscriber } from 'rxjs';
import { UpdateDetails } from './interfaces';
import { AuthService, WebAuthService } from './auth.service';
import { LandingConstants } from '../constants';
import { EditStatusService } from './editstatus.service';

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

    private mdres: Subject<NerdmRes> = new Subject<NerdmRes>();
    private custsvc: CustomizationService = null;
    private originalRec: NerdmRes = null;
    private origfields: {} = {};   // keeps track of orginal metadata so that they can be undone
    public  EDIT_MODES: any;

    private _lastupdate: UpdateDetails = {} as UpdateDetails;   // null object means unknown
    get lastUpdate() { return this._lastupdate; }
    set lastUpdate(updateDetails: UpdateDetails) {
        this._lastupdate = updateDetails;
        this.updated.emit(this._lastupdate);
    }

    /**
     * any Observable that will send out the date of the last update each time the metadata
     * is updated via this service.  If the date is an empty string, there are no updates 
     * pending for submission.  
     */
    public updated: EventEmitter<UpdateDetails> = new EventEmitter<UpdateDetails>();

    /**
     * a flag that indicates that whether the landing page is in edit mode, i.e. displays 
     * buttons for editing individual bits of metadata.  
     *
     * Note that this flag should only be updated by the controller (i.e. EditControlComponent) 
     * that subscribes to this class (via _subscribe()).
     */
    private editMode: string;
    // get editMode() { return this.editMode; }
    // set editMode(engage: string) { this.editMode = engage; }

    /**
     * construct the service
     * 
     * @param custsvc   the CustomizationService to use to send updates to the 
     *                  server.  
     */
    constructor(private msgsvc: UserMessageService,
        private edstatsvc: EditStatusService,
        private authsvc: AuthService,
        private datePipe: DatePipe) { 
          this.EDIT_MODES = LandingConstants.editModes;

          this.edstatsvc.watchEditMode((editMode) => {
            this.editMode = editMode;
          });
        }

    /*
     * subscribe to updates to the metadata.  This is intended for connecting the 
     * service to the EditControlPanel.
     */
    public subscribe(controller): void {
        this.mdres.subscribe(controller);
    }

    public setOriginalMetadata(md: NerdmRes) {
        this.originalRec = JSON.parse(JSON.stringify(md));
        this.mdres.next(md as NerdmRes);
    }

    public resetOriginal() {
      this.mdres.next(this.originalRec as NerdmRes);
    }

    _setCustomizationService(svc: CustomizationService): void {
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
    public update(subsetname: string, md: {}, fullRec: NerdmRes = {} as NerdmRes): Promise<boolean> {
        if (!this.custsvc) {
            console.error("Attempted to update without authorization!  Ignoring update.");
            return new Promise<boolean>((resolve, reject) => {
                resolve(false);
            });
        }
        // establish the original state for this subset of metadata (so that it this update
        // can be undone).
        if (this.originalRec) {
            if (!this.origfields[subsetname])
                this.origfields[subsetname] = {};

            for (let prop in md) {
                let realProp = prop.split("-")[0];
                if (this.origfields[subsetname][realProp] === undefined) {
                    if (this.originalRec[realProp] !== undefined) {
                        this.origfields[subsetname][realProp] = this.originalRec[realProp];
                    } else {
                        this.origfields[subsetname][realProp] = null;   // TODO: problematic; need to clean-up nulls
                    }
                }
            }
        }

        let fieldName = subsetname.split("-")[0];
        // If current data is the same as original (user changed the data back to original), call undo instead. Otherwise do normal update
        if (JSON.stringify(md[subsetname]) == JSON.stringify(this.origfields[subsetname])) {
            this.undo(subsetname);
        } else {
            return new Promise<boolean>((resolve, reject) => {
                let mdUpdate = {};
                //Use real field name for updating
                mdUpdate[fieldName] = md[subsetname];

                this.custsvc.updateMetadata(mdUpdate).subscribe(
                    (res) => {
                        // console.log("###DBG  Draft data returned from server:\n  ", res)
                        this.stampUpdateDate();
                        // this.mdres.next(res as NerdmRes);
                        this.mdres.next(fullRec as NerdmRes);
                        resolve(true);
                    },
                    (err) => {
                        // err will be a subtype of CustomizationError
                        if (err.type == 'user') {
                            console.error("Failed to save metadata changes: user error:" + err.message);
                            this.msgsvc.error(err.message);
                        }
                        else {
                            console.error("Failed to save metadata changes: server/system error:" + err.message);
                            this.msgsvc.syserror(err.message,
                                "There was an problem while updating the " + subsetname + ". ");
                        }
                        resolve(false);
                    }
                );
            });
        }
    }

    /**
     * undo a previously submitted update by its name
     * 
     * @param subsetname    the name for the metadata that was used in the call to update() which 
     *                      should be undone.
     * @param subsetValue   Specifically for topic field. Because there are multiple collections,
     *                      It's hard to keep track on collection here. The caller should keep track on 
     *                      changes and provides the whole topic field to update.
     * 
     * @return Promise<boolean>  -  result is true if the undo was successful, false if 
     *             there was an issue, including that there was nothing to undo.  Note that this 
     *             MetadataUpdateService instance will take care of reporting the reason.  This 
     *             response allows the caller in charge of getting updates to have its UI react
     *             accordingly.
     */
    public undo(subsetname: string, subsetValue: any = null) {
        if (this.origfields[subsetname] === undefined) {
            // Nothing to undo!
            console.warn("Undo called on " + subsetname + ": nothing to undo");
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
                        this.mdres.next(this.originalRec as NerdmRes);
                        resolve(true);
                    },
                    (err) => {
                        // err will be a subtype of CustomizationError
                        if (err.type == 'user') {
                            console.error("Failed to undo metadata changes: user error:" + err.message);
                            this.msgsvc.error(err.message)
                        }
                        else {
                            console.error("Failed to undo metadata changes: server/system error:" +
                                err.message);
                            this.msgsvc.syserror(err.message,
                                "There was an problem while undoing changes to the " + subsetname + ". ")
                        }
                        resolve(false);
                    }
                );
            });
        }
        else {
            // Other updates are still registered; just undo the specified one
            return new Promise<boolean>((resolve, reject) => {
                //If subset value provided, use it. Otherwise, use origfields.
                let updateValue: any;
                if(subsetValue){
                    updateValue = subsetValue;
                }else{
                    updateValue = this.origfields[subsetname];
                }

                this.custsvc.updateMetadata(updateValue).subscribe(
                    (res) => {
                        // Better remove this line for production. But it's ok to leave it
                        res[subsetname.split("-")[0]] = updateValue[subsetname.split("-")[0]];

                        delete this.origfields[subsetname];

                        this.mdres.next(res as NerdmRes);
                        resolve(true);
                    },
                    (err) => {
                        // err will be a subtype of CustomizationError
                        if (err.type == 'user') {
                            console.error("Failed to undo metadata changes: user error:" + err.message);
                            this.msgsvc.error(err.message)
                        }
                        else {
                            console.error("Failed to undo metadata changes: server/system error:" +
                                err.message);
                            this.msgsvc.syserror(err.message,
                                "There was an problem while undoing changes to the " + subsetname + ". ")
                        }
                        resolve(false);
                    }
                );
            });
        }
    }

    /**
     * Compare the subset of the given Nerdm record with original copy. If any subset is different, meaning the data has been changed, the original copy of the subset will be assigned to origfields object. The origfields object is used to set the field state in UI, i.e., the modified field will be in yellow background color.
     * This function also checks the update details of the given record which will be displayed in the status bar at the top.
     * @param mdrec The Nerdm record to be checked.
     */
    public checkUpdatedFields(mdrec: NerdmRes) {
        if (mdrec != undefined && this.originalRec != undefined) {
            for (let subset in mdrec) {
                if (this.originalRec[subset] != undefined && JSON.stringify(mdrec[subset]) != JSON.stringify(this.originalRec[subset])) {
                    this.origfields[subset] = {};
                    this.origfields[subset][subset] = this.originalRec[subset];
                }
            }
        }

        //Set updated date here so the submit button will lit up if we have something to submit
        let newdate: any;

        if (mdrec._updateDetails != undefined) {
            newdate = new Date(mdrec._updateDetails[mdrec._updateDetails.length - 1]._updateDate);

            this.lastUpdate = {
                'userDetails': this.authsvc.userDetails,
                '_updateDate': newdate.toLocaleString()
            }
        } else {
            this.lastUpdate = null;
        }
    }

    /**
     * return true if metadata associated with a given name have been updated.  This will return 
     * false either if the metadata was never updated or if the update was previously undone via 
     * undo().
     * @param subsetname    the name for the set of metadata of interest.
     */
    public fieldUpdated(subsetname: string): boolean {
        return this.origfields[subsetname];
    }

    /**
     * Reset the update status of a given field or all fields so fieldUpdated() will return false
     * @param subsetname - optional - the name for the set of metadata of interest.
     */
    public fieldReset(subsetname?: string) {
        if (subsetname) {
            this.origfields[subsetname] = null;
        } else {
            this.origfields = {};
        }
    }

    /**
     * load the latest draft of the resource metadata.
     * 
     * retrieve the latest draft of the resource metadata from the server and forward it
     * to the controller for display to the user.  
     */
    public loadDraft(onSuccess?: () => void): Observable<Object> {
        return new Observable<Object>(subscriber => {
            if (!this.custsvc) {
                console.error("Attempted to update without authorization!  Ignoring update.");
                return;
            }
            this.custsvc.getDraftMetadata().subscribe(
                (res) => {
                  this.mdres.next(res as NerdmRes);
                  subscriber.next(res as NerdmRes);
                  subscriber.complete();
                  if (onSuccess) onSuccess();
                },
                (err) => {
                  console.log("err", err);
                  this.edstatsvc.setShowLPContent(true);
                  
                  if(err.statusCode == 404)
                  {
                    this.resetOriginal();
                    this.edstatsvc._setEditMode(this.EDIT_MODES.OUTSIDE_MIDAS_MODE);
                  }else{
                    // err will be a subtype of CustomizationError
                    if (err.type == 'user') 
                    {
                        console.error("Failed to retrieve draft metadata changes: user error:" + err.message);
                        this.msgsvc.error(err.message);
                    }
                    else 
                    {
                        console.error("Failed to retrieve draft metadata changes: server error:" + err.message);
                        this.msgsvc.syserror(err.message);
                    }
                  }

                  subscriber.next(null);
                  subscriber.complete();
                }
            );
        });
    }

    /**
     * record the current date/time as the last time this data was updated.
     */
    public stampUpdateDate(): UpdateDetails {
        this.lastUpdate = {
            'userDetails': this.authsvc.userDetails,
            '_updateDate': this.datePipe.transform(new Date(), "MMM d, y, h:mm:ss a")
        }
        return this.lastUpdate;
    }

    /**
     * erase the date of last update.  This might be done if the last update was undone. 
     */
    public forgetUpdateDate(): void {
        this.lastUpdate = null;
    }

    /**
     * update the local (browser-side) metadata with the the original metadata from the last
     * time the metadata was committed.  This will not update the draft that exists in the 
     * customization service.  
     */
    public showOriginalMetadata() {
        this.mdres.next(this.originalRec);
    }

    /**
     * Tell whether we are in edit mode
     */
    get isEditMode(): boolean{
      return this.editMode == this.EDIT_MODES.EDIT_MODE;
    }

    /**
     *  Return field style based on edit mode and data update status
     */
    getFieldStyle(fieldName : string) {
      if (this.isEditMode) {
          if (this.fieldUpdated(fieldName)) {
              return { 'border': '1px solid lightgrey', 'background-color': '#FCF9CD', 'padding-right': '1em', 'cursor': 'pointer' };
          } else {
              return { 'border': '1px solid lightgrey', 'background-color': '#e6f2ff', 'padding-right': '1em', 'cursor': 'pointer' };
          }
      } else {
          return { 'border': '0px solid white', 'background-color': 'white', 'padding-right': '1em', 'cursor': 'default' };
      }
  }
}
