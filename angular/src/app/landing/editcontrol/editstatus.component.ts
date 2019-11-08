import { Component, OnInit } from '@angular/core';

import { MetadataUpdateService } from './metadataupdate.service';

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
    template: `
<div class="ec-status-bar">
    <span [ngStyle]="{'color': messageColor}">{{message}}</span>
    <div [hidden]="!isProcessing" style="width: 2em;height:2em; float: right;">
        <i class="faa faa-spinner faa-spin faa-stack-1x ec-status-spinner"
            style="width:2em;position: inherit;"></i>
    </div>
</div>
`,
    styles: [`
.ec-status-bar {
    width: 100%;
    height: 2em; 
    font-size: 15px; 
    text-align:right; 
    background-color: #FCF9CD;
    padding-right: 2em;
    padding-top: .3em;
}

.ec-status-spinner {
    color: rgb(22, 20, 59);
}
`]
})
export class EditStatusComponent implements OnInit {

    private _updateDate : string = "";
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
        this.mdupdsvc.updated.subscribe((date) => { this._updateDate = date; });
    }

    /**
     * a flag for controlling the appearance of the spinner
     */
    private _isProcessing : boolean = false;
    get isProcessing() { return this._isProcessing; }

    /**
     * set the date of the last update.
     */
    public setLastUpdateDate(date : string) {
        this._updateDate = date;
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
                this.showMessage("This record was edited on " + this._updateDate, inprogress);
            else
                this.showMessage('Click on the "Quit Edit" button to exit edit mode.', inprogress);
        }
        else {
            if (this._updateDate)
                this.showMessage("You have un-submitted changes last edited on " + this._updateDate +
                                 ".  Click on the Edit button to continue editing.", 
                                 inprogress, "rgb(255, 115, 0)");
            else
                this.showMessage('To see any previously edited inputs or to otherwise edit this page, ' +
                                 'click on the "Edit" button.', inprogress);
        }            
    }
}
