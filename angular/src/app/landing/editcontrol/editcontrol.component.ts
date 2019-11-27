import { Component, OnInit, OnChanges, ViewChild, Input, Output, EventEmitter } from '@angular/core';
import { Observable, of, BehaviorSubject } from 'rxjs';

import { ConfirmationDialogService } from '../../shared/confirmation-dialog/confirmation-dialog.service';
import { ConfirmationDialogComponent } from '../../shared/confirmation-dialog/confirmation-dialog.component';
import { UserMessageService } from '../../frame/usermessage.service';
import { MessageBarComponent } from '../../frame/messagebar.component';
import { EditStatusComponent } from './editstatus.component';
import { MetadataUpdateService } from './metadataupdate.service';
import { EditStatusService } from './editstatus.service';
import { AuthService, WebAuthService } from './auth.service';
import { CustomizationService } from './customization.service';
import { NerdmRes } from '../../nerdm/nerdm';

/**
 * a panel that serves as a control center for editing metadata displayed in the 
 * landing page.  Features include:
 *  * a bar of buttons for turning on editing, saving changes, and discarding changes
 *  * a bar for displaying the current status of the editing
 *  * a bar for displaying error messages.  
 * 
 * This component also houses the business logic for managing metadata editing, including 
 * orchestrating authentication and authorization.  
 */
@Component({
    selector: 'pdr-edit-control',
    templateUrl: './editcontrol.component.html',
    styleUrls: ['./editcontrol.component.css']
})
export class EditControlComponent implements OnInit, OnChanges {

    private _custsvc : CustomizationService = null;
    private originalRecord : NerdmRes = null;
    private _editmode : boolean = false;

    /**
     * a flag indicating whether editing mode is turned on (true=yes).  This parameter is 
     * available to a parent template via (editModeChanged).  
     */
    get editMode() { return this._editmode; }
    set editMode(engage : boolean) {
        if (this._editmode != engage) {
            this._editmode = engage;
            this.mdupdsvc.editMode = this._editmode;
            this.edstatsvc._setEditMode(engage);
            this.editModeChanged.emit(engage);
        }
    }
    @Output() editModeChanged : EventEmitter<boolean> = new EventEmitter<boolean>();

    /**
     * the local copy of the draft (updated) metadata.  This parameter is available to a parent
     * template via [(mdrec)].
     */
    @Input() mdrec : NerdmRes;
    @Output() mdrecChange = new EventEmitter<NerdmRes>();

    /**
     * the ID that was used to request the landing page
     */
    @Input() requestID : string;

    /**
     * the original resource identifier
     */
    private _resid : string = null;
    get resID() { return this._resid; }

    @Input() inBrowser : boolean = false;

    // injected as ViewChilds so that this class can send messages to it with a synchronous method call.
    @ViewChild(EditStatusComponent)
    private statusbar : EditStatusComponent;

    @ViewChild(MessageBarComponent)
    private msgbar : MessageBarComponent;
    
    /**
     * create the component
     *
     * @param mdupdsvc           a MetadataUpdateService used to receive updates from editing widgets
     * @param authsvc            a AuthService used for interacting with the customization web service
     *                           (this service will provide the CustomizationService for updating 
     *                           metadata).
     * @param confirmDialogSvc   a ConfirmationDialogService for displaying pop-up confirmation windows 
     *                           (provided by local injector)
     * @param msgsvc             a UserMessageService used to receive messages for display in the error 
     *                           message bar
     */
    public constructor(private mdupdsvc : MetadataUpdateService,
                       private edstatsvc : EditStatusService,
                       private authsvc : AuthService,
                       private confirmDialogSvc : ConfirmationDialogService,
                       private msgsvc : UserMessageService)
    {
        this.mdupdsvc._subscribe(
            (md) => {
                if (md && md != this.mdrec) {
                    this.mdrec = md as NerdmRes;
                    this.edstatsvc._setLastUpdated(this.mdupdsvc.lastUpdate);
                    this.mdrecChange.emit(md as NerdmRes);
                }
            }
        );
        
        this.edstatsvc._setLastUpdated(this.mdupdsvc.lastUpdate);
        this.edstatsvc._setEditMode(this.editMode);
        this.edstatsvc._setAuthorized(this.isAuthorized());
        this.edstatsvc._setUserID(this.authsvc.userID);
    }

    ngOnInit() {
        this.ngOnChanges();
        this.statusbar.showLastUpdate(this.editMode)
        this.edstatsvc._watchRemoteStart((start) => {
            if (start)
                this.startEditing(true);
        });
    }
    ngOnChanges() {
        if (this.mdrec instanceof Object && Object.keys(this.mdrec).length > 0) {
            if (! this.resID)
                this._resid = this.mdrec['ediid'];
            if (this.originalRecord === null) {
                this.originalRecord = this._deepCopy(this.mdrec) as NerdmRes;
                this.mdupdsvc._setOriginalMetadata(this.originalRecord)
            }
        }
    }

    /**
     * start (or resume) editing of the resource metadata.  Calling this will cause editing widgets to 
     * appear on the landing page, allowing the user to edit various fields.
     * 
     * @param nologin   if false (default) and the user is not logged in, the browser will be redirected 
     *                  to the authentication service.  If true, redirection will not occur; instead, 
     *                  the app will remain with editing turned off if the user is not logged in.  
     */
    public startEditing(nologin : boolean = false) : void {
        // console.log("start editing...");
        if (this._custsvc) {
            // already authorized
            console.log("start editing... already authorized!");
            this.editMode = true;
            return;
        }
        
        console.log("start editing... need authorization...");
        this.authorizeEditing(nologin).subscribe(
            (successful) => {
                this.mdupdsvc.loadDraft(() => {
                    this.editMode = successful;
                });
            }
        );
    }

    /**
     * discard the edits made so far
     */
    public discardEdits() : void {
        if (this._custsvc) {
            this._custsvc.discardDraft().subscribe(
                (md) => {
                    this.mdupdsvc.forgetUpdateDate();
                    this.mdupdsvc.fieldReset();
                    this.editMode = false;
                    if (md && md['@id']) {
                        // assume a NerdmRes object was returned
                        this.mdrec = md as NerdmRes;
                        this.mdrecChange.emit(md as NerdmRes);
                    }

                    this.mdupdsvc.showOriginalMetadata();

                    // reload this page from the source
                    // window.location.replace("/od/id/"+this.requestID);
                },
                (err) => {
                    if (err.type == "user")
                        this.msgsvc.error(err.message);
                    else {
                        console.error("error during discard: "+err.message)
                        this.msgsvc.syserror("error during discard: "+err.message)
                    }
                }
            );
        }
        else
            console.warn("Warning: requested edit discard without authorization");
    }

    /**
     * discard the latest changes after receiving confirmation via a modal pop-up.  This will revert 
     * the data to its previous state.
     */
    public confirmDiscardEdits() : void {
        this.confirmDialogSvc.confirm('Edited data will be lost',  'Do you want to erase changes?', true)
            .then( (confirmed) => {
                if (confirmed)
                    this.discardEdits()
                else
                    console.log("User canceled discard request");
            })
            .catch( () => {
                console.log("User canceled discard request (indirectly)");
            });
    }

    /**
     * commit the latest changes to the metadata.  
     */
    public saveEdits() : void {
        if (this._custsvc) {
            this.statusbar.showMessage("Submitting changes...", true);
            this._custsvc.saveDraft().subscribe( 
                (md) => { 
                    this.mdupdsvc.forgetUpdateDate();
                    this.mdupdsvc.fieldReset();
                    this.mdrec = md as NerdmRes;
                    this.mdrecChange.emit(md as NerdmRes);
                    this.editMode = false;
                    this.statusbar.showLastUpdate(this.editMode)

                    // reload this page from the source
                    // window.location.replace("/od/id/"+this.requestID);
                },
                (err) => {
                    if (err.type == "user")
                        this.msgsvc.error(err.message);
                    else {
                        this.msgsvc.syserror("error during save: "+err.message);
                    }
                    this.statusbar.showLastUpdate(this.editMode)
                }
            );
        }
        else
            console.warn("Warning: requested edit discard without authorization");
    }

    /**
     * pause the editing process: remove the editing widgets from the page so that the user can see how 
     * the changes will appear.  This function is called when the "Preview" button is clicked.
     */
    public preview() : void {
        this.editMode = false;
        if (this.editsPending())
            this.statusbar.showMessage('Click "Submit" to commit your changes '+
                                       'or "Edit" to make more changes.');
        else
            this.statusbar.showLastUpdate(this.editMode);
    }  

    /**
     * pause the editing process and hide unsaved changes.  This function is called when the 
     * "Quit Edit" button is clicked.
     */
    public pauseEditing() : void {
        this.editMode = false;

        if (this.editsPending())
            this.statusbar.showMessage('Click "Submit" to commit your changes '+
                                       'or "Edit" to make more changes.');
        else
            this.statusbar.showLastUpdate(this.editMode);

        this.mdupdsvc.showOriginalMetadata();
    }

    /**
     * return true if there are edits saved that have not be submitted
     */
    public editsPending() : boolean { return Boolean(this.mdupdsvc.lastUpdate); }

    /**
     * return true if the user is currently authorized to to edit the resource metadata.
     * If false, can attempt to gain authorization via a call to authorizeEditing();
     */
    public isAuthorized() : boolean {
        return Boolean(this._custsvc);
    }

    /**
     * obtain authorization to edit the metadata and pass that authorization to the editing widgets.
     *
     * Authorization in this context mean a CustomizationService with a valid authorization token 
     * embedded in it.  The CustomizationService will be passed to the MetadataUpdateService so 
     * that it can send updates from the editing widgets to the remote customization web service.  
     *
     * Note that calling this method may cause the browser to redirect to an authorization server, 
     * and, thus, this function would not return to its caller.  The authorization server should 
     * return the browser to the landing page which should trigger calling this function again.  
     * 
     * @param nologin   if false (default) and the user is not logged in, the browser will be redirected 
     *                  to the authentication service.  If true, redirection will not occur; instead, 
     *                  false is returned if the user is not logged in.  
     * @return Observable<boolean>   this will resolve to true if the application is authorized; 
     *                               false, if either the user could not authenticate or is otherwise 
     *                               not allowed to edit this record.  
     */
    public authorizeEditing(nologin : boolean = false) : Observable<boolean> {
        if (this._custsvc) return of<boolean>(true);   // We're already authorized
        if (! this.resID) {
            console.warn("Warning: Initial metadata record not established yet in EditControlComponent");
            return of<boolean>(false);
        }

        return new Observable<boolean>(subscriber => {
            console.log("obtaining editing authorization");
            this.statusbar.showMessage("Authenticating/authorizing access...", true)
            
            this.authsvc.authorizeEditing(this.resID, nologin).subscribe(  // might cause redirect (see above)
                (custsvc) => {
                    this._custsvc = custsvc;    // could be null, indicating user is not authorized.
                    this.mdupdsvc._setCustomizationService(custsvc);
                    if (! this.authsvc.userID) {
                        console.log("authentication failed");
                        this.msgsvc.error("User log in cancelled or failed.  To edit, please log in " +
                                          'by clicking the "Edit" button above.')
                    }
                    else if (! custsvc) {
                        console.log("authorization denied for user "+this.authsvc.userID);
                        this.msgsvc.error("Sorry, you are not authorized to edit this submission.")
                    }
                    else
                        console.log("authorization granted for user "+this.authsvc.userID);
                    subscriber.next(Boolean(this._custsvc));
                    subscriber.complete();
                    this.statusbar.showLastUpdate(this.editMode)
                    this.edstatsvc._setUserID(this.authsvc.userID);
                    this.edstatsvc._setAuthorized(true);
                },
                (err) => {
                    let msg = "Failure during authorization: "+err.message
                    console.error(msg);
                    this.msgsvc.syserror(msg);
                    subscriber.next(false);
                    subscriber.complete();
                    this.statusbar.showLastUpdate(this.editMode)
                    this.edstatsvc._setAuthorized(false);
                }
            );
        });
    }

    /**
     * send a message to the message bar.  This is provided (currently) mainly for testing purposes.
     * @param msg    the text of the message
     * @param type   the type of message it is (tip, error, syserror, information, instruction, 
     *               warning, or celebration)
     */
    public showMessage(msg : string, mtype = "information") {
        this.msgbar._addMessage(msg, mtype);
    }

    private _deepCopy(obj : {}|[]|string|boolean|number) : {}|[]|string|boolean|number {
        return JSON.parse(JSON.stringify(obj));
    }
    
}
