import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { AuthorPopupComponent } from './author-popup/author-popup.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { AuthorService } from './author.service';

@Component({
    selector: 'app-author',
    templateUrl: './author.component.html',
    styleUrls: ['../landing.component.css']
})
export class AuthorComponent implements OnInit {
    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    fieldName = 'authors';
    tempInput: any = {};

    constructor(public mdupdsvc : MetadataUpdateService,        
                private ngbModal: NgbModal,
                private notificationService: NotificationService,
                private authorService: AuthorService)
    { }

    /**
     * a field indicating if this data has beed edited
     */
    get updated() { return this.mdupdsvc.fieldUpdated(this.fieldName); }

    ngOnInit() {
    }
    
    openModal() {
        if (! this.mdupdsvc.isEditMode) return;

        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass"
        };

        var tempauthors = [];
        if (this.record[this.fieldName] != undefined && this.record[this.fieldName].length > 0)
            this.tempInput[this.fieldName] = JSON.parse(JSON.stringify(this.record[this.fieldName]));
        else {
            tempauthors.push(this.authorService.getBlankAuthor());
            this.tempInput[this.fieldName] = tempauthors;
        }

        for (var author in this.tempInput[this.fieldName]) 
        {
            this.tempInput.authors[author]['isCollapsed'] = false;
            this.tempInput.authors[author]['fnLocked'] = false;
            this.tempInput.authors[author]['originalIndex'] = author;
            this.tempInput.authors[author]['dataChanged'] = false;
            // For affiliation, we will convert subunits into a string for editing purpose.
            // After the value return, we will convert it back to array
            if(this.tempInput.authors[author]['affiliation'])
            {
                for(let i in this.tempInput.authors[author]['affiliation'])
                {
                    if(this.tempInput.authors[author]['affiliation'][i]['subunits'])
                    {
                        if(this.tempInput.authors[author]['affiliation'][i]['subunits'] instanceof Array)
                        {
                            this.tempInput.authors[author]['affiliation'][i]['subunits'] = this.tempInput.authors[author]['affiliation'][i]['subunits'].join(',');
                        }
                    }                    
                }

            }
        }

        const modalRef = this.ngbModal.open(AuthorPopupComponent, ngbModalOptions);

        modalRef.componentInstance.inputValue = this.tempInput;
        modalRef.componentInstance['field'] = this.fieldName;
        modalRef.componentInstance['title'] = this.fieldName.toUpperCase();

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                // console.log("returnValue", returnValue);
                var authors: any[] = [];
                var postMessageDetail: any = {};
                var postMessage: any = {};
                var properties = ['affiliation', 'familyName', 'fn', 'givenName', 'middleName', 'orcid'];
                var reyurnAuthors = returnValue[this.fieldName];

                for(let author of reyurnAuthors) {
                    for(let prop in author)
                    {
                        if(properties.indexOf(prop) > -1)
                        {
                            if(properties.indexOf('affiliation') > -1) // Convert subunits back to array
                            {
                                if(author['affiliation'])
                                {
                                    for(let j in author['affiliation'])
                                    {
                                        if(author['affiliation'][j]['subunits'])
                                        {
                                            if(!(author['affiliation'][j]['subunits'] instanceof Array))
                                                author['affiliation'][j]['subunits'] = JSON.parse(JSON.stringify(author['affiliation'][j]['subunits'].split(/\s*,\s*/).filter(su => su != '')));
                                        }
                                    }
                                }
                            }
                                
                            postMessageDetail[prop] = JSON.parse(JSON.stringify(author[prop]));

                        }
                    }

                    authors.push(postMessageDetail);
                }

                postMessage[this.fieldName] = JSON.parse(JSON.stringify(authors));
                console.log("postMessage", postMessage);

                this.mdupdsvc.update(this.fieldName, postMessage).then((updateSuccess) => {
                    // console.log("###DBG  update sent; success: "+updateSuccess.toString());
                    if (updateSuccess)
                        this.notificationService.showSuccessWithTimeout("Authors updated.", "", 3000);
                    else
                        console.error("acknowledge author update failure");
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


    clicked = false;
    expandClick() {
        this.clicked = !this.clicked;
        return this.clicked;
    }

    getSubunites(subunites)
    {
        if(subunites instanceof Array)
        {
            return subunites.join(',');
        }else{
            return subunites;
        }
    }
}
