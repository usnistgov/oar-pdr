import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SearchTopicsComponent } from './topic-popup/search-topics.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';

@Component({
    selector: 'app-topic',
    templateUrl: './topic.component.html',
    styleUrls: ['../landing.component.css']
})
export class TopicComponent implements OnInit {
    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    //05-12-2020 Ray asked to read topic data from 'theme' instead of 'topic'
    fieldName = 'theme';

    constructor(public mdupdsvc: MetadataUpdateService,
        private ngbModal: NgbModal,
        private notificationService: NotificationService) {
    }

    /**
     * a field indicating if this data has beed edited
     */
    get updated() { return this.mdupdsvc.fieldUpdated(this.fieldName); }

    /**
     * a field indicating whether there are no keywords are set.  
     */
    get isEmpty() {
        if (!this.record[this.fieldName])
            return true;
        if (this.record[this.fieldName] instanceof Array &&
            this.record[this.fieldName].filter(topic => topic.length > 0).length == 0)
            return true;
        return false;
    }

    ngOnInit() {
    }

    /**
     * Open topic pop up window
     */
    openModal() {
        // Do nothing if it's not in edit mode. 
        // This should never happen because the edit button should be disabled.
        if (!this.mdupdsvc.isEditMode) return;

        // Pop up dialog set up
        // backdrop: 'static' - the pop up will not be closed 
        //                      when user click outside the dialog window.
        // windowClass: "myCustomModalClass" - pop up dialog styling defined in styles.scss
        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        const modalRef = this.ngbModal.open(SearchTopicsComponent, ngbModalOptions);

        let val: string[] = [];
        if (this.record[this.fieldName])
            val = JSON.parse(JSON.stringify(this.record[this.fieldName]));

        modalRef.componentInstance.inputValue = {};
        modalRef.componentInstance.inputValue[this.fieldName] = val;
        modalRef.componentInstance['field'] = this.fieldName;
        modalRef.componentInstance['title'] = "Research Topics";

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                var postMessage: any = {};
                postMessage[this.fieldName] = returnValue[this.fieldName];
                this.mdupdsvc.update(this.fieldName, postMessage).then((updateSuccess) => {
                    // console.log("###DBG  update sent; success: "+updateSuccess.toString());
                    if (updateSuccess)
                        this.notificationService.showSuccessWithTimeout("Research topics updated.", "", 3000);
                    else
                        console.error("acknowledge topic update failure");
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
                this.notificationService.showSuccessWithTimeout("Reverted changes to research topic.", "", 3000);
            else
                console.error("Failed to undo research topic")
        });
    }

    /**
     * Function to Check record has topics
     */
    checkTopics() {
        if (Array.isArray(this.record[this.fieldName])) {
            if (this.record[this.fieldName].length > 0)
                return true;
            else
                return false;
        }
        else {
            return false;
        }
    }
}
