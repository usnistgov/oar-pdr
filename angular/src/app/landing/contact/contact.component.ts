import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SharedService } from '../../shared/shared';
import { ContactPopupComponent } from './contact-popup/contact-popup.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';

@Component({
    selector: 'app-contact',
    templateUrl: './contact.component.html',
    styleUrls: ['../landing.component.css']
})
export class ContactComponent implements OnInit {
    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    fieldName = 'contactPoint';

    tempInput: any = {};
    isEmail = false;
    enableEdit = false; // Temprorarily disable edit mode for now. Can set it true to enable in the furure.

    constructor(public mdupdsvc : MetadataUpdateService,        
                private ngbModal: NgbModal,
                private gaService: GoogleAnalyticsService,
                private notificationService: NotificationService)
    { }

    /**
     * a field indicating if this data has beed edited
     */
    get updated() { return this.mdupdsvc.fieldUpdated(this.fieldName); }

    ngOnInit() {
        if ("hasEmail" in this.record['contactPoint'])
            this.isEmail = true;
        console.log("record.contactPoint.hasEmail",this.record['contactPoint'].hasEmail);
    }

    getFieldStyle() {
        if (this.mdupdsvc.editMode && this.enableEdit) {
            if (this.mdupdsvc.fieldUpdated(this.fieldName)) {
                return { 'border': '1px solid lightgrey', 'background-color': '#FCF9CD', 'padding-right': '1em' };
            } else {
                return { 'border': '1px solid lightgrey', 'background-color': 'white', 'padding-right': '1em' };
            }
        } else {
            return { 'border': '0px solid white', 'background-color': 'white', 'padding-right': '1em' };
        }
    }
    
    openModal() {
        if (! this.mdupdsvc.editMode) return;

        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        if (this.record[this.fieldName] != undefined && this.record[this.fieldName] != "") {
            this.tempInput[this.fieldName] = JSON.parse(JSON.stringify(this.record[this.fieldName]));
        } else {
            this.tempInput[this.fieldName] = [];
            this.tempInput[this.fieldName].push(this._getBlankField());
        }

        const modalRef = this.ngbModal.open(ContactPopupComponent, ngbModalOptions);

        modalRef.componentInstance.inputValue = this.tempInput;
        modalRef.componentInstance['field'] = this.fieldName;
        modalRef.componentInstance['title'] = this.fieldName.toUpperCase();

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                var postMessage: any = {};
                postMessage[this.fieldName] = returnValue[this.fieldName];
                console.log("postMessage", JSON.stringify(postMessage));

                this.mdupdsvc.update(this.fieldName, postMessage).then((updateSuccess) => {
                    // console.log("###DBG  update sent; success: "+updateSuccess.toString());
                    if (updateSuccess)
                        this.notificationService.showSuccessWithTimeout("Contact updated.", "", 3000);
                    else
                        console.error("acknowledge contact update failure");
                });
            }
        })
    }

    protected _getBlankField() {
        return {
            "fn": "",
            "hasEmail": "",
            "address": [ "" ]
        }
    }

    /*
     *  Undo editing. If no more field was edited, delete the record in staging area.
     */
    undoEditing() {
        this.mdupdsvc.undo(this.fieldName).then((success) => {
            if (success)
                this.notificationService.showSuccessWithTimeout("Reverted changes to keywords.", "", 3000);
            else
                console.error("Failed to undo keywords metadata")
        });
    }

    clickContact = false;
    expandContact() {
        this.clickContact = !this.clickContact;
        return this.clickContact;
    }
}
