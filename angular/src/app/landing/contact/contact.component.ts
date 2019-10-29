import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CustomizationService } from '../../shared/customization-service/customization-service.service';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SharedService } from '../../shared/shared';
import { ContactPopupComponent } from './contact-popup/contact-popup.component';
import { EditControlService } from '../edit-control-bar/edit-control.service';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { DatePipe } from '@angular/common';
import { ErrorHandlingService } from '../../shared/error-handling-service/error-handling.service';

@Component({
    selector: 'app-contact',
    templateUrl: './contact.component.html',
    styleUrls: ['../landing.component.css']
})
export class ContactComponent implements OnInit {
    @Input() record: any[];
    @Input() originalRecord: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    @Input() fieldObject: any;

    recordEditmode: boolean = false;
    tempInput: any = {};
    fieldName = 'contactPoint';
    isEmail = false;

    constructor(
        private customizationService: CustomizationService,
        private ngbModal: NgbModal,
        private editControlService: EditControlService,
        private notificationService: NotificationService,
        private gaService: GoogleAnalyticsService,
        private datePipe: DatePipe,
        private errorHandlingService: ErrorHandlingService,
        private sharedService: SharedService
    ) { 
        this.editControlService.watchEditMode().subscribe(value => {
            this.recordEditmode = value;
        });
    }

    ngOnInit() {
        if ("hasEmail" in this.record['contactPoint'])
            this.isEmail = true;
        console.log("record.contactPoint.hasEmail",this.record['contactPoint'].hasEmail);
    }

    getFieldStyle() {
        if (this.recordEditmode) {
            if (this.customizationService.dataEdited(this.record[this.fieldName], this.originalRecord[this.fieldName])) {
                return { 'border': '1px solid lightgrey', 'background-color': '#FCF9CD', 'padding-right': '1em' };
            } else {
                return { 'border': '1px solid lightgrey', 'background-color': 'white', 'padding-right': '1em' };
            }
        } else {
            return { 'border': '0px solid white', 'background-color': 'white', 'padding-right': '1em' };
        }
    }
    
    openModal() {
        if (!this.recordEditmode) return;

        let i: number;
        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        if (this.record[this.fieldName] != undefined && this.record[this.fieldName] != "") {
            this.tempInput[this.fieldName] = this.sharedService.deepCopy(this.record[this.fieldName]);
        } else {
            this.tempInput[this.fieldName] = [];
            this.tempInput[this.fieldName].push(this.sharedService.getBlankField(this.fieldName));
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

                this.customizationService.update(JSON.stringify(postMessage)).subscribe(
                    result => {
                        this.record[this.fieldName] = this.sharedService.deepCopy(returnValue[this.fieldName]);
                        this.editControlService.setDataChanged(true);
                        this.onUpdateSuccess();
                    },
                    err => {
                        this.onUpdateError(err, "Error updating contact", "Update contact");
                    });
            }
        })
    }

    /*
     * When update successful
     */
    onUpdateSuccess() {
        this.fieldObject[this.fieldName]["edited"] = (JSON.stringify(this.record[this.fieldName]) != JSON.stringify(this.originalRecord[this.fieldName]));
        var updateDate = this.datePipe.transform(new Date(), "MMM d, y, h:mm:ss a");
        this.customizationService.checkDataChanges(this.record, this.originalRecord, this.fieldObject, updateDate);
        this.notificationService.showSuccessWithTimeout("Contact updated.", "", 3000);
    }

    /*
     * When update failed
     */
    onUpdateError(err: any, message:string, action: string) {
        this.errorHandlingService.setErrMessage({ message: message, messageDetail: err.message, action: action, display: true });
        // this.setErrorMessage.emit({ error: err, displayError: true, action: action });
    }

    /*
     *  Undo editing. If no more field was edited, delete the record in staging area.
     */
    undoEditing() {
        var noMoreEdited = true;
        console.log("this.fieldObject", this.fieldObject);
        for (var fld in this.fieldObject) {
            if (this.fieldName != fld && this.fieldObject[fld].edited) {
                noMoreEdited = false;
                break;
            }
        }

        if (noMoreEdited) {
            console.log("Deleting...");
            this.customizationService.delete().subscribe(
                (res) => {
                    if (this.originalRecord[this.fieldName] == undefined)
                        delete this.record[this.fieldName];
                    else
                        this.record[this.fieldName] = this.sharedService.deepCopy(this.originalRecord[this.fieldName]);

                    this.onUpdateSuccess();
                },
                (err) => {
                    this.onUpdateError(err, "Error undo editing", "Undo editing - delete");
                }
            );
        } else {
            var body: string;
            if (this.originalRecord[this.fieldName] == undefined) {
                body = '{"' + this.fieldName + '":""}';
            } else {
                body = '{"' + this.fieldName + '":' + JSON.stringify(this.originalRecord[this.fieldName]) + '}';
            }

            this.customizationService.update(body).subscribe(
                result => {
                    if (this.originalRecord[this.fieldName] == undefined)
                        delete this.record[this.fieldName];
                    else
                        this.record[this.fieldName] = this.sharedService.deepCopy(this.originalRecord[this.fieldName]);

                    this.onUpdateSuccess();
                },
                err => {
                    this.onUpdateError(err, "Error undo editing", "Undo editing");
                });
        }
    }

    clickContact = false;
    expandContact() {
        this.clickContact = !this.clickContact;
        return this.clickContact;
    }
}
