import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SearchTopicsComponent } from './topic-popup/search-topics.component';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { TreeNode } from 'primeng/primeng';
import { TaxonomyListService } from '../../shared/taxonomy-list';
import { MetadataUpdateService } from '../editcontrol/metadataupdate.service';
import { UserMessageService } from '../../frame/usermessage.service';

@Component({
    selector: 'app-topic',
    templateUrl: './topic.component.html',
    styleUrls: ['../landing.component.css']
})
export class TopicComponent implements OnInit {
    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    fieldName = 'topic';

    taxonomyTree: TreeNode[] = [];
    taxonomyList: any[];

    constructor(public mdupdsvc: MetadataUpdateService,
        private taxonomyListService: TaxonomyListService,
        private ngbModal: NgbModal,
        private msgsvc: UserMessageService,
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
            this.record[this.fieldName].map(topic => {
                return topic.tag;
            }).filter(topic => topic.length > 0).length == 0)
            return true;
        return false;
    }

    ngOnInit() {
        this.taxonomyListService.get(0).subscribe((result) => {
            if (result != null && result != undefined)
                this.buildTaxonomyTree(result);

            this.taxonomyList = [];
            for (var i = 0; i < result.length; i++) {
                this.taxonomyList.push({ "taxonomy": result[i].label });
            }
        }, (err) => {
            this.msgsvc.syserror(err.toString());
        });
    }

    /*
     *   build taxonomy tree
     */
    buildTaxonomyTree(result: any) {
        let allTaxonomy: any = result;
        var tempTaxonomyTree = {}
        if (result != null && result != undefined) {
            tempTaxonomyTree["data"] = this.arrangeIntoTaxonomyTree(result);
            this.taxonomyTree.push(tempTaxonomyTree);
        }

        this.taxonomyTree = <TreeNode[]>this.taxonomyTree[0].data;
    }

    private arrangeIntoTaxonomyTree(paths) {
        const tree = [];
        paths.forEach((path) => {
            var fullpath: string;
            if (path.parent != null && path.parent != undefined && path.parent != "")
                fullpath = path.parent + ":" + path.label;
            else
                fullpath = path.label;

            const pathParts = fullpath.split(':');
            let currentLevel = tree; // initialize currentLevel to root

            for (var j = 0; j < pathParts.length; j++) {
                let tempId: string = '';
                for (var k = 0; k < j + 1; k++) {
                    tempId = tempId + pathParts[k];
                    // tempId = tempId + pathParts[k].replace(/ /g, "");
                    if (k < j) {
                        tempId = tempId + ": ";
                    }
                }

                // check to see if the path already exists.
                const existingPath = currentLevel.filter(level => level.data.treeId === tempId);
                if (existingPath.length > 0) {
                    // The path to this item was already in the tree, so don't add it again.
                    // Set the current level to this path's children  
                    currentLevel = existingPath[0].children;
                } else {
                    let newPart = null;
                    newPart = {
                        data: {
                            treeId: tempId,
                            name: pathParts[j],
                            researchTopic: tempId,
                            bkcolor: 'white'
                        }, children: [],
                        expanded: false
                    };
                    currentLevel.push(newPart);
                    currentLevel = newPart.children;
                }
            };
        });
        return tree;
    }

    /**
     *  Return style based on edit mode and data update status
     */
    getFieldStyle() {
        if (this.mdupdsvc.editMode) {
            if (this.mdupdsvc.fieldUpdated(this.fieldName)) {
                return { 'border': '1px solid lightgrey', 'background-color': '#FCF9CD', 'padding-right': '1em' };
            } else {
                return { 'border': '1px solid lightgrey', 'background-color': 'white', 'padding-right': '1em' };
            }
        } else {
            return { 'border': '0px solid white', 'background-color': 'white', 'padding-right': '1em' };
        }
    }

    /**
     * Open topic pop up window
     */
    openModal() {
        // Do nothing if it's not in edit mode. 
        // This should never happen because the edit button should be disabled.
        if (!this.mdupdsvc.editMode) return;

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
            val = this.record[this.fieldName].map((topic) => { return topic.tag; });

        modalRef.componentInstance.inputValue = {};
        modalRef.componentInstance.inputValue[this.fieldName] = val;
        modalRef.componentInstance['field'] = this.fieldName;
        modalRef.componentInstance['title'] = "Research Topics";
        modalRef.componentInstance.taxonomyTree = this.taxonomyTree;

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                var postMessage: any = {};
                postMessage[this.fieldName] = returnValue[this.fieldName].map((topic) => {
                    return {
                        '@type': 'Concept',
                        'scheme': 'https://www.nist.gov/od/dm/nist-themes/v1.0',
                        'tag': topic,
                    };
                });

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
                this.notificationService.showSuccessWithTimeout("Reverted changes to keywords.", "", 3000);
            else
                console.error("Failed to undo keywords metadata")
        });
    }

    /**
     * Function to Check record has topics
     */
    checkTopics() {
        if (Array.isArray(this.record['topic'])) {
            if (this.record['topic'].length > 0)
                return true;
            else
                return false;
        }
        else {
            return false;
        }
    }
}
