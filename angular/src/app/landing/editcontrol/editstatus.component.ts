import { Component, OnInit } from '@angular/core';

import { MetadataUpdateService } from './metadataupdate.service';
import { UpdateDetails } from './interfaces';
import { LandingConstants } from '../constants';

/**
 * A panel inside the EditControlComponent that displays information about the status of 
 * editing.
 *
 * Features:
 *  * If we know the date of the last update, it displays it
 *  * If we don't know the date, it recommends clicking the Edit button to see latest
 *    updates. 
 *  * During interactions with the customization web service, a spinner is displayed.
 */
@Component({
    selector: 'pdr-edit-status',
    templateUrl: 'editstatus.component.html',
    styleUrls: ['editstatus.component.css']
})
export class EditStatusComponent implements OnInit {

    private _updateDetails : UpdateDetails = null;
    get updateDetails() { return this._updateDetails; }
    
    message : string = "";
    messageColor : string = "black";
    editMode: string;
    EDIT_MODES: any;

    /**
     * construct the component
     *
     * @param mdupdsvc    the MetadataUpdateService that is receiving updates.  This will be 
     *                    used to be alerted when updates have been made.
     */
    constructor(public mdupdsvc : MetadataUpdateService) {

        this.EDIT_MODES = LandingConstants.editModes;
        this.editMode = this.EDIT_MODES.VIEWONLY_MODE;
        this.mdupdsvc.updated.subscribe((details) => { 
            this._updateDetails = details; 
            this.showLastUpdate(this.EDIT_MODES.EDIT_MODE);  //Once last updated date changed, refresh the status bar message
        });
    }

    /**
     * a flag for controlling the appearance of the spinner
     */
    private _isProcessing : boolean = false;
    get isProcessing() { return this._isProcessing; }

    /**
     * set the date of the last update.
     */
    public setLastUpdateDetails(updateDetails : UpdateDetails) {
        this._updateDetails = updateDetails;
    }

    /**
     * indicate whether the we are currently processing an edit
     */
    public setIsProcessing(onoff : boolean) {
        this._isProcessing = onoff;
    }

    _setEditMode(editMode: string){
        this.editMode = editMode;
    }

    ngOnInit() {
    }

    /**
     * Display an arbitrary message
     */
    public showMessage(msg : string, inprogress : boolean = false, color : string = "black") {
        this.message = msg;
        this.messageColor = color;
        this._isProcessing = inprogress;
    }

    /**
     * display the time of the last update, if known
     */
    public showLastUpdate(editmode : string, inprogress : boolean = false) {
      switch(editmode){
        case this.EDIT_MODES.EDIT_MODE:
            // We are editing the metadata (and are logged in)
            if (this._updateDetails)
                this.showMessage("This record was edited by " + this._updateDetails.userDetails.userName + " " + this._updateDetails.userDetails.userLastName + " on " + this._updateDetails._updateDate, inprogress);
            else
                this.showMessage('Click on the <i class="faa faa-pencil"></i> button to edit or <i class="faa faa-undo"></i> button to discard the change.', inprogress);
          break;
        case this.EDIT_MODES.PREVIEW_MODE:
            if (this._updateDetails)
                this.showMessage("There are un-submitted changes last edited on " + this._updateDetails._updateDate + ".  Click on the Edit button to continue editing.", 
                inprogress, "rgb(255, 115, 0)");
            else
                this.showMessage('To see any previously edited inputs or to otherwise edit this page, ' +
                                 'click on the "Edit" button.', inprogress);
          break;   
        case this.EDIT_MODES.DONE_MODE:
          this.showMessage('You can now close this window and go back to Midas to either accept or discard the changes.', false);
          break;
      }        
    }
}
