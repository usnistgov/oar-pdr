import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { DescriptionPopupComponent } from './description-popup/description-popup.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';

@Component({
    selector: 'app-description',
    templateUrl: './description.component.html',
    styleUrls: ['../landing.component.css', './description.component.css']
})
export class DescriptionComponent implements OnInit {
    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    fieldName: string = 'description';

    constructor(public mdupdsvc : MetadataUpdateService,        
                private ngbModal: NgbModal,                      
                private notificationService: NotificationService)
    { }

    get updated() { return this.mdupdsvc.fieldUpdated(this.fieldName); }

    ngOnInit() {
    }

    getFieldStyle() {
        if (this.mdupdsvc.editMode) {
            if (this.mdupdsvc.fieldUpdated(this.fieldName)) {
                return { 'background-color': '#FCF9CD' };
            } else {
                return {  };
            }
        } else {
            return {  };
        }
    }

    openModal() {
        if (!this.mdupdsvc.editMode) return;

        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        const modalRef = this.ngbModal.open(DescriptionPopupComponent, ngbModalOptions);

        let val = "";
        if (this.record[this.fieldName])
            val = this.record[this.fieldName].join('\n\n');

        modalRef.componentInstance.inputValue = { };
        modalRef.componentInstance.inputValue[this.fieldName] = val;
        modalRef.componentInstance['field'] = this.fieldName;
        modalRef.componentInstance['title'] = 'Description';

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                // console.log("###DBG  receiving editing output: " +
                //             returnValue[this.fieldName].substring(0,20) + "....");
                let updmd = {};
                updmd[this.fieldName] = returnValue[this.fieldName].split(/\n\s*\n/).filter(desc => desc != '');
                this.mdupdsvc.update(this.fieldName, updmd).then((updateSuccess) => {
                    // console.log("###DBG  update sent; success: "+updateSuccess.toString());
                    if (updateSuccess)
                        this.notificationService.showSuccessWithTimeout("Description updated.", "", 3000);
                    else
                        console.error("acknowledge description update failure");
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
                this.notificationService.showSuccessWithTimeout("Reverted changes to description.", "", 3000);
            else
                console.error("Failed to undo description metadata")
        });
    }

}
