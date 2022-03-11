import { Component, OnInit, Input, SimpleChanges } from '@angular/core';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { SearchService } from '../../shared/search-service/index';
import { timeout } from 'rxjs-compat/operator/timeout';

@Component({
  selector: 'app-resultlist',
  templateUrl: './resultlist.component.html',
  styleUrls: ['./resultlist.component.css'],
  animations: [
        trigger('detailExpand', [
        state('collapsed', style({height: '0px', minHeight: '0'})),
        state('expanded', style({height: '*'})),
        transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
        ]),
        trigger('detailExpand2', [
            state('collapsed', style({opacity: 0})),
            state('expanded', style({opacity: 1})),
            transition('expanded <=> collapsed', animate('625ms')),
        ]),
        trigger(
            'enterAnimation', [
                transition(':enter', [
                    style({height: '0px', opacity: 0}),
                    animate('700ms', style({height: '100%', opacity: 1}))
                ]),
                transition(':leave', [
                    style({height: '100%', opacity: 1}),
                    animate('700ms', style({height: 0, opacity: 0}))
                ])
            ]
        )
    ]
})
export class ResultlistComponent implements OnInit {
    searchResults: any[];
    searchResultsOriginal: any[];
    currentIndex: number = 0;
    resultCount: number = 0;
    options = [{name:'Title', value:'title'}, {name:'Description', value:'description'}, {name:'Last Modified Date', value:'modified'}, {name:'Keyword', value:'keyword'}];
    optionSelected: string;
    searchPhases: string = "";
    searchFields: string[] = ["title", "description", "keyword"];
    showResult: boolean = true;
    PDRAPIURL: string = "https://data.nist.gov/od/id/";

    @Input() md: NerdmRes = null;
    @Input() searchValue: string;
    @Input() searchTaxonomyKey: string;
    @Input() currentPage: number = 1;
    @Input() mobWidth: number = 1920;
    @Input() theme: string = 'nist';
    @Input() filterString: string = '';

    constructor(private searchService: SearchService) { }

    ngOnInit(): void {
        let that = this;
        this.searchService.searchPhrase()
        .subscribe(
            searchResults => {
                this.resultCount = searchResults['ResultCount'];
                that.onSuccess(searchResults.ResultData);
            },
            error => that.onError(error)
        );
    }

    ngOnChanges(changes: SimpleChanges): void {
        if(changes.filterString != null && changes.filterString != undefined) {
            this.filterResults();
        }
    }

    onSuccess(searchResults: any[]) {
        this.searchResultsOriginal = JSON.parse(JSON.stringify(searchResults));
        this.searchResults = JSON.parse(JSON.stringify(searchResults));

        //Init searchResults
        for(let item of this.searchResults) {
            item.DetailsDisplayed = false;
            item.active = true;
        }

    }

    /**
     * Return the class of the arrow next to the file name.
     * If the details is hidden, display the "right" arrow. Otherwise "down" arrow.
     * @returns 
     */
    fileDetailsDisplayClass(resultItem: any) {
        if(resultItem.DetailsDisplayed){
            return 'faa faa-caret-down nist-blue-fc';
        }else{
            return 'faa faa-caret-right nist-blue-fc';
        }
    }

    /**
     *  Expand the row to display file details. It's little tricky when hiding the details. 
     *  We have to delay the action to let the animation to finish. 
     * @param fileNode       the TreeNode for the file to provide details for
     */
    openDetails(fileNode: any, index: number) {
        //Close current details window if it's open
        if(index != this.currentIndex) {
            this.searchResults[this.currentIndex]['DetailsDisplayed'] = false;
        }
        this.currentIndex = index;

        if(fileNode.DetailsDisplayed){
            fileNode.DetailsDisplayed = false;
            // setTimeout(() => {
            //     fileNode.DetailsDisplayed02 = false;
            // }, 600);
        }else{
            fileNode.DetailsDisplayed = true;
            // fileNode.DetailsDisplayed02 = true;
        }
    }

    /**
     * Determine if the file details need be displayed
     * @param fileNode file node in the tree
     * @returns boolean
     *      true: display details
     *      false: hide details
     */
    showFileDetails(fileNode: any) {
        return fileNode.DetailsDisplayed;
    }
    
    /**
     * Return class name based on given column number and window size
     * @param column 
     */
    flexgrow(column: number){
        let lclass: string = "full-width";

        if(this.mobWidth > 1024 ) lclass = "flex-grow" + column;
        else lclass = "full-width";

        return lclass;
    }

    /**
     * Return the class for the top bar (total result, pagination and Customize View button)
     */
    resultTopBarClass(){
        if(this.mobWidth > 1024 ) return "flex-container";
        else return "";
    }

    /**
     * If search is unsuccessful push the error message
     */
    onError(error: any[]) {

    }

    /**
     * Filter the search result with search text
     * @param value search text from the search box
     */
    filterResultByPhase(value) {
        if(!this.searchResults) return;

        if(!value) value = "";

        let lSearchPhases = value.split(",");
        let found: boolean = false;

        this.searchResults.forEach((object) => {
            object.active = false;
            this.searchFields.forEach((key) => {
                if(Array.isArray(object[key])) {
                    object[key].forEach( (val) => {
                        lSearchPhases.forEach((searchVal) => {
                            if(val.toLowerCase().includes(searchVal.trim().toLowerCase())) {
                                object.active = true;
                            }
                        })
                    })
                }else{
                    lSearchPhases.forEach((searchVal) => {
                        if(object[key].toLowerCase().includes(searchVal.toLowerCase())) {
                            object.active = true;
                        }
                    })
                }
                
            });
        });
    }

    resetResult() {
        if(this.searchResults) {
            this.searchResults.forEach((object) => {
                object.active = true;
            })
        }
    }

    filterResults() {
        let filters: string[];
        
        this.resetResult();

        if(this.searchPhases != "")
            this.filterResultByPhase(this.searchPhases);

        if(this.filterString != "noFilter" && this.filterString != ""){
            filters = this.filterString.split("&");
            
            filters.forEach((filter) => {
                switch(filter.split("=")[0]){
                    case "@type":
                        this.searchResults.forEach((object) => {
                            if(object.active == true){
                                object.active = false;

                                object["@type"].forEach((oType) => {
                                    if(oType.includes(filter.split("=")[1]))
                                        object.active = true;
                                })
                            } 
                        });

                        break;
                    case "topic.tag":
                        this.searchResults.forEach((object) => {
                            if(object.active == true){
                                object.active = false;
                            
                                object["topic"].forEach((oTopic) => {
                                    if(oTopic["tag"].includes(filter.split("=")[1]))
                                        object.active = true;
                                })
                            }
                        });

                        break;
                    case "components.@type":
                        this.searchResults.forEach((object) => {
                            if(object.active == true){
                                object.active = false;
                            
                                object["components"].forEach((component) => {
                                    component["@type"].forEach((cType) => {
                                        if(cType.includes(filter.split("=")[1]))
                                        object.active = true;
                                    })
                                })
                            }
                        });

                        break;
                    default:
                        break;
                }
            })
        }
    }

    onSortByChange(event: any) {
        let key = event.value.value;
        this.searchResults.sort((a, b)=> {
            if(Array.isArray(a[key])){
                return a[key][0].localeCompare(b[key][0]);
            }else{
                return a[key].localeCompare(b[key]);
            }
        });

        this.refreshResult();
    }

    refreshResult() {
        this.showResult = false;
        setTimeout(() => {
            this.showResult = true;
        }, 0);
    }
}
