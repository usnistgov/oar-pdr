import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { DescriptionPopupComponent } from '../description/description-popup/description-popup.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';

@Component({
    selector: 'app-title',
    templateUrl: './title.component.html',
    styleUrls: ['./title.component.css', '../landing.component.css']
})
export class TitleComponent implements OnInit {
    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    fieldName: string = 'title';

    constructor(public mdupdsvc: MetadataUpdateService,
        private ngbModal: NgbModal,
        private notificationService: NotificationService) {
    }

    get updated() { return this.mdupdsvc.fieldUpdated(this.fieldName); }

    ngOnInit() {
    }

    openModal() {
        if (!this.mdupdsvc.isEditMode) return;

        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        let val = "";
        if (this.record['title'])
            val = this.record['title'];

        const modalRef = this.ngbModal.open(DescriptionPopupComponent, ngbModalOptions);

        modalRef.componentInstance.inputValue = {}
        modalRef.componentInstance.inputValue[this.fieldName] = val;
        modalRef.componentInstance['field'] = 'title';
        modalRef.componentInstance['title'] = 'Title';

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                var postMessage: any = {};
                postMessage[this.fieldName] = returnValue[this.fieldName];
                // console.log("###DBG updating title: ", JSON.stringify(postMessage));

                this.mdupdsvc.update(this.fieldName, postMessage).then((updateSuccess) => {
                    if (updateSuccess)
                        this.notificationService.showSuccessWithTimeout("Title updated.", "", 3000);
                    else
                        console.error("acknowledge title update failure");
                });
            }
        });
    }

    /*
     *  Undo editing. If no more field was edited, delete the record in staging area.
     */
    undoEditing() {
        this.mdupdsvc.undo(this.fieldName).then((success) => {
            if (success)
                this.notificationService.showSuccessWithTimeout("Reverted changes to title.", "", 3000);
            else
                console.error("Failed to undo title metadata")
        });
    }
}
