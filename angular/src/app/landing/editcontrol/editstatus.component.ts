import { Component, OnInit } from '@angular/core';

import { MetadataUpdateService } from './metadataupdate.service';
import { UpdateDetails } from './interfaces';

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

    private _updateDate : UpdateDetails = null;
    get updateDate() { return this._updateDate; }
    
    message : string = "";
    messageColor : string = "black";

    /**
     * construct the component
     *
     * @param mdupdsvc    the MetadataUpdateService that is receiving updates.  This will be 
     *                    used to be alerted when updates have been made.
     */
    constructor(private mdupdsvc : MetadataUpdateService) {
        this.mdupdsvc.updated.subscribe((date) => { 
            this._updateDate = date; 
            this.showLastUpdate(true);  //Once last updated date changed, refresh the status bar message
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
    public setLastUpdateDate(updateDetails : UpdateDetails) {
        this._updateDate = updateDetails;
    }

    /**
     * indicate whether the we are currently processing an edit
     */
    public setIsProcessing(onoff : boolean) {
        this._isProcessing = onoff;
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
    public showLastUpdate(editmode : boolean, inprogress : boolean = false) {
        if (editmode) {
            // We are editing the metadata (and are logged in)
            if (this._updateDate)
                this.showMessage("This record was edited by " + this._updateDate.userDetails.userName + " " + this._updateDate.userDetails.userLastName + " on " + this._updateDate._updateDate, inprogress);
            else
                this.showMessage('Click on the <i class="faa faa-pencil"></i> button to edit or <i class="faa faa-undo"></i> button to discard the change.', inprogress);
        }
        else {
            if (this._updateDate)
                this.showMessage("There are un-submitted changes last edited on " + this._updateDate._updateDate + ".  Click on the Edit button to continue editing.", 
                inprogress, "rgb(255, 115, 0)");
            else
                this.showMessage('To see any previously edited inputs or to otherwise edit this page, ' +
                                 'click on the "Edit" button.', inprogress);
        }            
    }
}
