import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SearchTopicsComponent } from './topic-popup/search-topics.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { AppConfig } from '../../config/config';
import { deepCopy } from '../../utils';
import { CollectionService } from '../../shared/collection-service/collection.service';
import { Themes, ThemesPrefs, Collections, Collection, CollectionThemes, FilterTreeNode } from '../../shared/globals/globals';

@Component({
    selector: 'app-topic',
    templateUrl: './topic.component.html',
    styleUrls: ['../landing.component.css']
})
export class TopicComponent implements OnInit {
    nistTaxonomyTopics: any[] = [];
    scienceThemeTopics: any[] = [];
    recordType: string = "";
    // standardNISTTaxonomyURI: string = "https://data.nist.gov/od/dm/nist-themes/";
    allCollections: any = {};
    //  Array to define the collection order
    collectionOrder: string[] = [Collections.DEFAULT];
    topics: any = {};
    originalTopics: any = {};   // For undo purpose
    fieldName = 'topic';

    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean;   // false if running server-side
    //05-12-2020 Ray asked to read topic data from 'theme' instead of 'topic'
    @Input() collection: string = Collections.DEFAULT;

    constructor(public mdupdsvc: MetadataUpdateService,
                private ngbModal: NgbModal,
                private cfg: AppConfig,
                public collectionService: CollectionService,
                private notificationService: NotificationService) {

            // this.standardNISTTaxonomyURI = this.cfg.get("standardNISTTaxonomyURI", "https://data.nist.gov/od/dm/nist-themes/");

            this.collectionOrder = this.collectionService.getCollectionOrder();
            this.allCollections = this.collectionService.loadAllCollections();
    }

    /**
     * a field indicating if this data has beed edited
     */
    // get updated() { return this.mdupdsvc.fieldUpdated(this.fieldName); }
    updated(collection: string = Collections.DEFAULT) { 
        return this.mdupdsvc.fieldUpdated(this.fieldName + "-" + collection); 
    }

    /**
     * a field indicating whether there are no keywords are set.  
     */
    get hasTopics() {
        let hasTopic: boolean = false;

        for(let col of this.collectionOrder) {
            if(this.topics[col] && this.topics[col].length > 0) {
                hasTopic = true;
                break;
            }
        }

        return hasTopic;
    }

    ngOnInit() {
        this.updateResearchTopics();
        this.originalTopics = JSON.parse(JSON.stringify(this.topics));
    }

    /**
     * Once input record changed, refresh the topic list 
     * @param changes 
     */
    ngOnChanges(changes: SimpleChanges): void {
        this.updateResearchTopics();
    }

    hasTopic(collection: string = Collections.DEFAULT) {
        return this.topics[collection] && this.topics[collection].length > 0; 
    }

    /**
     * Update the research topic lists
     */
    updateResearchTopics() {
        this.topics = {};
        if(this.record) {
            if (this.record[this.fieldName]) {
                this.record[this.fieldName].forEach(topic => {
                    if (topic['scheme'] && topic.tag) {
                        for(let col of this.collectionOrder) {
                            if(topic['scheme'].indexOf(this.allCollections[col].taxonomyURI) >= 0){
                                if(!this.topics[col]) {
                                    this.topics[col] = [topic];
                                }else if(this.topics[col].indexOf(topic) < 0) {
                                    this.topics[col].push(topic);
                                }
                            }
                        }

                    }
                });
            }
        }
    }

    /**
     * Restore topics to Nerdm format
     */
    restoreTopics(inputTopics: any) {
        let topics: any[] = [];

        for(let col of this.collectionOrder) {
            if(inputTopics[col] && inputTopics[col].length > 0) {
                for(let topic of inputTopics[col]) {
                    topics.push(topic);
                }
            }
        }

        return topics;
    }

    /**
     * Open topic pop up window
     */
    openModal(collection: string = Collections.DEFAULT) {
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

        let val: any[] = [];
        // if (this.record[this.fieldName])
            // val = JSON.parse(JSON.stringify(this.nistTaxonomyTopics));
        val = this.topics[collection];
        let field = this.fieldName + "-" + collection;

        modalRef.componentInstance.inputTopics = {};
        modalRef.componentInstance.inputTopics[field] = val;
        modalRef.componentInstance['field'] = field;
        modalRef.componentInstance['title'] = this.allCollections[collection].tag;
        modalRef.componentInstance['scheme'] = this.allCollections[collection].taxonomyURI + "v1.0";
        modalRef.componentInstance['type'] = "Concept";

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            console.log("returnValue", returnValue);
            if (returnValue) {
                var postMessage: any = {};

                this.topics[collection] = returnValue[field];
                
                postMessage[field] = this.restoreTopics(this.topics);
                let newRec = JSON.parse(JSON.stringify(this.record));
                newRec[this.fieldName] = postMessage[field];

                this.mdupdsvc.update(field, postMessage, newRec).then((updateSuccess) => {
                    // console.log("###DBG  update sent; success: "+updateSuccess.toString());
                    if (updateSuccess) {
                        this.notificationService.showSuccessWithTimeout("Research topics updated.", "", 3000);
                        this.record[this.fieldName] = postMessage[field];
                        this.updateResearchTopics();
                    } else
                        console.error("acknowledge topic update failure");
                });
            }
        })
    }

    /*
     *  Undo editing. If no more field was edited, delete the record in staging area.
     */
    undoEditing(collection: string) {
        let topics: any = this.topics;
        topics[collection] = this.originalTopics[collection];
        let subsetValue: any = {}; 
        subsetValue[this.fieldName]= this.restoreTopics(topics);

        this.mdupdsvc.undo(this.fieldName+"-"+collection, subsetValue).then((success) => {
            if (success) {
                this.notificationService.showSuccessWithTimeout("Reverted changes to research topic.", "", 3000);

                this.updateResearchTopics();
            } else
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
