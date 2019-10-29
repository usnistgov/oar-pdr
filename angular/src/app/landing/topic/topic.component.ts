import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CustomizationService } from '../../shared/customization-service/customization-service.service';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { SharedService } from '../../shared/shared';
import { SearchTopicsComponent } from './topic-popup/search-topics.component';
import { EditControlService } from '../edit-control-bar/edit-control.service';
import { NotificationService } from '../../shared/notification-service/notification.service';
import { TreeNode } from 'primeng/primeng';
import { TaxonomyListService } from '../../shared/taxonomy-list';
import { DatePipe } from '@angular/common';
import { ErrorHandlingService } from '../../shared/error-handling-service/error-handling.service';

@Component({
    selector: 'app-topic',
    templateUrl: './topic.component.html',
    styleUrls: ['../landing.component.css']
})
export class TopicComponent implements OnInit {
    @Input() record: any[];
    @Input() originalRecord: any[];
    @Input() inBrowser: boolean;   // false if running server-side
    @Input() fieldObject: any;

    recordEditmode: boolean = false;
    tempInput: any = {};
    fieldName = 'topic';
    taxonomyTree: TreeNode[] = [];
    taxonomyList: any[];

    constructor(
        private customizationService: CustomizationService,
        private ngbModal: NgbModal,
        private editControlService: EditControlService,
        private notificationService: NotificationService,
        private taxonomyListService: TaxonomyListService,
        private datePipe: DatePipe,
        private errorHandlingService: ErrorHandlingService,
        private sharedService: SharedService
    ) {
        this.editControlService.watchEditMode().subscribe(value => {
            this.recordEditmode = value;
        });
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
            this.onUpdateError(err, "Error Laoding taxonomy list", "Laod taxonomy list");
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
                            // name: pathParts[j].replace(/ /g, ""),
                            researchTopic: tempId,
                            bkcolor: 'white'
                        }, children: [],
                        expanded: false
                    };
                    currentLevel.push(newPart);
                    currentLevel = newPart.children;
                    // }
                }
            };
        });
        return tree;
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

        this.tempInput[this.fieldName] = this.sharedService.getBlankField(this.fieldName);
        var tempTopics = [];
        if (this.record['topic'] != null && this.record['topic'].length > 0) {
            for (i = 0; i < this.record['topic'].length; i++) {
                tempTopics.push(this.record['topic'][i].tag);
            }
        }
        this.tempInput[this.fieldName] = tempTopics;

        const modalRef = this.ngbModal.open(SearchTopicsComponent, ngbModalOptions);

        modalRef.componentInstance.inputValue = this.tempInput;
        modalRef.componentInstance['field'] = this.fieldName;
        modalRef.componentInstance['title'] = this.fieldName.toUpperCase();
        // console.log("this.taxonomyTree @@@", this.taxonomyTree);
        modalRef.componentInstance.taxonomyTree = this.taxonomyTree;

        modalRef.componentInstance.returnValue.subscribe((returnValue) => {
            if (returnValue) {
                var strtempTopics: string = '';
                var tempTopicsForUpdate: any = [];
                var lTempTopics: any[] = [];

                for (var i = 0; i < returnValue["topic"].length; ++i) {
                    strtempTopics = strtempTopics + returnValue["topic"][i];
                    lTempTopics.push({ '@type': 'Concept', 'scheme': 'https://www.nist.gov/od/dm/nist-themes/v1.0', 'tag': returnValue["topic"][i] });
                }
                returnValue["topic"] = this.sharedService.deepCopy(lTempTopics);

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
                        this.onUpdateError(err, "Error updating topic", "Update topic");
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
        this.notificationService.showSuccessWithTimeout("Author updated.", "", 3000);
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
