import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { DescriptionPopupComponent } from '../description/description-popup/description-popup.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';

@Component({
    selector: 'app-keyword',
    templateUrl: './keyword.component.html',
    styleUrls: ['../landing.component.css']
})
export class KeywordComponent implements OnInit {
    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    fieldName: string = 'keyword';

    constructor(public mdupdsvc : MetadataUpdateService,        
                private ngbModal: NgbModal,     
                private notificationService: NotificationService)
    { }

    /**
     * a field indicating if this data has beed edited
     */
    get updated() { return this.mdupdsvc.fieldUpdated(this.fieldName); }

    /**
     * a field indicating whether there are no keywords are set.  
     */
    get isEmpty() {
        if (! this.record[this.fieldName])
            return true;
        if (this.record[this.fieldName] instanceof Array &&
            this.record[this.fieldName].filter(kw => Boolean(kw)).length == 0)
            return true;
        return false;
    }

    ngOnInit() {
    }

    getFieldStyle() {
        if (this.mdupdsvc.isEditMode) {
            if (this.mdupdsvc.fieldUpdated(this.fieldName)) {
                return { 'border': '1px solid lightgrey', 'background-color': '#FCF9CD' };
            } else {
                return { 'border': '1px solid lightgrey', 'background-color': 'white' };
            }
        } else {
            return { 'border': '0px solid white', 'background-color': 'white' };
        }
    }

    openModal() {
        if (! this.mdupdsvc.isEditMode) return;

        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        const modalRef = this.ngbModal.open(DescriptionPopupComponent, ngbModalOptions);

        let val = "";
        if (this.record[this.fieldName])
            val = this.record[this.fieldName].join(', ');

        modalRef.componentInstance.inputValue = { };
        modalRef.componentInstance.inputValue[this.fieldName] = val;
        modalRef.componentInstance['field'] = this.fieldName;
        modalRef.componentInstance['title'] = 'Keywords';
        modalRef.componentInstance.message = "Please enter keywords separated by comma (* required).";

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                // console.log("###DBG  receiving editing output: " +
                //             returnValue[this.fieldName].substring(0,20) + "....");
                let updmd = {};
                updmd[this.fieldName] = returnValue[this.fieldName].split(/\s*,\s*/).filter(kw => kw != '');
                this.mdupdsvc.update(this.fieldName, updmd).then((updateSuccess) => {
                    // console.log("###DBG  update sent; success: "+updateSuccess.toString());
                    if (updateSuccess)
                        this.notificationService.showSuccessWithTimeout("Keywords updated.", "", 3000);
                    else
                        console.error("acknowledge keywords update failure");
                });
            }
        })
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

}
