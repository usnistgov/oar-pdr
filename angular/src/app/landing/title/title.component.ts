import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CustomizationService } from '../../shared/customization-service/customization-service.service';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SharedService } from '../../shared/shared';
import { DescriptionPopupComponent } from '../description/description-popup/description-popup.component';
import { EditControlService } from '../edit-control-bar/edit-control.service';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { DatePipe } from '@angular/common';
import { ErrorHandlingService } from '../../shared/error-handling-service/error-handling.service';

@Component({
    selector: 'app-title',
    templateUrl: './title.component.html',
    styleUrls: ['../landing.component.css']
})
export class TitleComponent implements OnInit {
    @Input() record: any[];
    @Input() originalRecord: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    @Input() fieldObject: any;

    recordEditmode: boolean = false;
    tempInput: any = {};

    constructor(
        private customizationService: CustomizationService,
        private ngbModal: NgbModal,
        private editControlService: EditControlService,
        private notificationService: NotificationService,
        private datePipe: DatePipe,
        private errorHandlingService: ErrorHandlingService,
        private sharedService: SharedService
    ) {
        this.editControlService.watchEditMode().subscribe(value => {
            this.recordEditmode = value;
        });
    }

    ngOnInit() {
    }

    getFieldStyle() {
        if (this.recordEditmode) {
            if (this.customizationService.dataEdited(this.record['title'], this.originalRecord['title'])) {
                return { 'border': '1px solid lightgrey', 'background-color': '#FCF9CD' };
            } else {
                return { 'border': '1px solid lightgrey', 'background-color': 'white' };
            }
        } else {
            return { 'border': '0px solid white', 'background-color': 'white' };
        }
    }

    openModal() {
        if (!this.recordEditmode) return;

        let i: number;
        let tempDecription: string = "";

        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        this.tempInput['title'] = this.sharedService.getBlankField('title');
        if (this.record['title'] != undefined && this.record['title'] != "") {
            this.tempInput['title'] = this.sharedService.deepCopy(this.record['title']);
        } else {
            this.tempInput['title'] = [];
            this.tempInput['title'].push(this.sharedService.getBlankField('title'));
        }

        const modalRef = this.ngbModal.open(DescriptionPopupComponent, ngbModalOptions);

        modalRef.componentInstance.inputValue = this.tempInput;
        modalRef.componentInstance['field'] = 'title';
        modalRef.componentInstance['title'] = 'TITLE';

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                var postMessage: any = {};
                postMessage['title'] = returnValue['title'];
                console.log("postMessage", JSON.stringify(postMessage));

                this.customizationService.update(JSON.stringify(postMessage)).subscribe(
                    result => {
                        this.record['title'] = this.sharedService.deepCopy(returnValue['title']);
                        this.editControlService.setDataChanged(true);
                        this.onUpdateSuccess();
                    },
                    err => {
                        this.onUpdateError(err, "Error updating title", "Update title");
                    });
            }
        })
    }

    /*
     * When update successful
     */
    onUpdateSuccess() {
        this.fieldObject['title']["edited"] = (JSON.stringify(this.record['title']) != JSON.stringify(this.originalRecord['title']));
        var updateDate = this.datePipe.transform(new Date(), "MMM d, y, h:mm:ss a");
        this.customizationService.checkDataChanges(this.record, this.originalRecord, this.fieldObject, updateDate);
        this.notificationService.showSuccessWithTimeout("Title updated.", "", 3000);
    }

    /*
     * When update failed
     */
    onUpdateError(err: any, message: string, action: string) {
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
            if ('title' != fld && this.fieldObject[fld].edited) {
                noMoreEdited = false;
                break;
            }
        }

        if (noMoreEdited) {
            console.log("Deleting...");
            this.customizationService.delete().subscribe(
                (res) => {
                    if (this.originalRecord['title'] == undefined)
                        delete this.record['title'];
                    else
                        this.record['title'] = this.sharedService.deepCopy(this.originalRecord['title']);

                    this.onUpdateSuccess();
                },
                (err) => {
                    this.onUpdateError(err, "Error undo editing", "Undo editing - delete");
                }
            );
        } else {
            var body: string;
            if (this.originalRecord['title'] == undefined) {
                body = '{"title":""}';
            } else {
                body = '{"title":' + JSON.stringify(this.originalRecord['title']) + '}';
            }

            this.customizationService.update(body).subscribe(
                result => {
                    if (this.originalRecord['title'] == undefined)
                        delete this.record['title'];
                    else
                        this.record['title'] = this.sharedService.deepCopy(this.originalRecord['title']);

                    this.onUpdateSuccess();
                },
                err => {
                    this.onUpdateError(err, "Error undo editing", "Undo editing");
                });
        }
    }

}
