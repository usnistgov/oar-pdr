import { Component, OnInit, Input, SimpleChanges, ViewChild, ElementRef } from '@angular/core';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { SearchService } from '../../shared/search-service/index';
import { timeout } from 'rxjs-compat/operator/timeout';
import { ThisReceiver } from '@angular/compiler';
import * as e from 'express';
import { connectableObservableDescriptor } from 'rxjs/internal/observable/ConnectableObservable';

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
    searchResultsForDisplay: any[];
    searchResultsOriginal: any[];
    currentIndex: number = 0;
    resultCount: number = 0;
    options = [{name:'Title', value:'title'}, {name:'Description', value:'description'}, {name:'Last Modified Date (Default)', value:'modified'}, {name:'Keyword', value:'keyword'}];
    optionSelected: string;
    searchPhases: string = "";
    searchFields: string[] = ["title", "description", "keyword"];
    showResult: boolean = true;
    PDRAPIURL: string = "https://data.nist.gov/od/id/";
    noSearchResult: boolean = false;

    //Pagination
    totalResultItems: number = 0;
    totalPages: number = 0;
    itemsPerPage: number = 20;
    pages = [{name:'Page 1', value:1},{name:'Page 2', value:2}];
    currentPage: number = 1;

    @Input() md: NerdmRes = null;
    @Input() searchValue: string;
    @Input() searchTaxonomyKey: string;
    @Input() mobWidth: number = 1920;
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

    /**
     * Processing search results
     * @param searchResults search results
     */
    onSuccess(searchResults: any[]) {
        searchResults.forEach((object) => {
            object['active'] = true;
        })

        this.searchResultsOriginal = JSON.parse(JSON.stringify(searchResults));
        this.searchResults = JSON.parse(JSON.stringify(searchResults));

        //Init searchResults
        for(let item of this.searchResults) {
            item.DetailsDisplayed = false;
            item.active = true;
        }

        this.filterResults();
        this.sortByDate();
    }

    /**
     * Calculate total pages and total result items
     * @returns 
     */
    getTotalResultItems() {
        if(!this.searchResultsForDisplay) return;

        let totalItems: number = 0;

        this.totalResultItems = this.searchResultsForDisplay.length;
        this.noSearchResult = this.totalResultItems == 0;

        if(this.totalResultItems % this.itemsPerPage == 0)
            this.totalPages = Math.trunc(this.totalResultItems / this.itemsPerPage);
        else
            this.totalPages = Math.trunc(this.totalResultItems / this.itemsPerPage) + 1;

        this.pages = [];
        for(let i=1; i <= this.totalPages; i++) {
            this.pages.push({name:'Page '+i+' of '+this.totalPages, value:i})
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
            this.searchResultsForDisplay[this.currentIndex]['DetailsDisplayed'] = false;
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
     * Rules: 
     *     A B -- A or B
     *     A,B -- A or B
     *     "A B" -- Search for "A B"
     * @param searchString search text from the search box
     */
    filterResultByPhase(searchString: string) {
        if(!this.searchResults) return;

        if(!searchString || searchString.trim() == "") {
            searchString = "";
            this.searchResults = this.searchResultsOriginal;
            return;
        }

        let filteredResults: any;;
        let finalFilteredResults: any[] = [];

        // Reserve everything in quotes
        let quotes = searchString.match(/\"(.*?)\"/g);

        if(quotes){
            for(let i = 0; i < quotes.length; i++){
                if(quotes[i].match(/\"(.*?)\"/)[1].trim() != '')
                    searchString = searchString.replace(new RegExp(quotes[i].match(/\"(.*?)\"/)[1], 'g'), 'Quooooote'+i);
                else
                    searchString = searchString.replace(quotes[i], 'Quooooote'+i);
            }
        }

        // Treat "," the same as " "
        let tempValue = searchString.replace(/,/g, " ").replace(/  /g, " ");

        let lSearchPhases = tempValue.split(" ");
        
        lSearchPhases.forEach((searchPhase: string) => {
            let searchWord: string = "";

            if(searchPhase != ""){
                filteredResults = JSON.parse(JSON.stringify(this.searchResultsOriginal));

                // Restore the contents in quotes
                if(searchPhase.indexOf('Quooooote') >= 0) {
                    searchPhase = searchPhase.replace(/"/g, '');
                    let index = searchPhase.substring(searchPhase.indexOf('Quooooote')+9);
                    searchWord = quotes[index].replace(/"/g, '');
                }else{
                    searchWord = searchPhase.replace(/"/g, '');
                }

                // Do search
                filteredResults = this.filterResultByWord(filteredResults, searchWord);

                filteredResults.forEach((object)=>{
                    finalFilteredResults.push(object);
                })
                
                finalFilteredResults.map(item => item["@id"])
                    .filter((value, index, self) => self.indexOf(value) === index);
            }
        })
        
        this.searchResults = finalFilteredResults;
    }

    /**
     * Filter search result using searchString
     * @param searchResults The result list to be searched
     * @param searchString search string
     * @returns filtered result list
     */
    filterResultByWord(searchResults:any[], searchString: string) {
        let retuenVal: any[] = [];
        let found: boolean = false;

        for(let object of searchResults) {
            found = false;
            for(let key of this.searchFields) {
                if(Array.isArray(object[key])) {
                    for(let val of object[key]) {
                        if(val.toLowerCase().includes(searchString.trim().toLowerCase())) {
                            retuenVal.push(object);
                            found = true;
                            break;
                        }
                    }
                }else{
                    if(object[key].toLowerCase().includes(searchString.toLowerCase())) {
                        retuenVal.push(object);
                        found = true;
                        break;
                    }
                }

                if(found) break;
            };
        }

        // Remove items with duplicated @id
        retuenVal.map(item => item["@id"])
                .filter((value, index, self) => self.indexOf(value) === index);

        return retuenVal;
    }

    /**
     * Reset active flags of all search result items to true (default)
     */
    resetResult() {
        if(this.searchResults) {
            this.searchResults.forEach((object) => {
                object.active = true;
            })
        }
    }

    /**
     * Apply filters from left side panel and the search word(s) from the search text box
     */
    filterResults() {
        if(this.searchResults == undefined) return;

        let filters: string[];
        
        // Reset the search result
        this.resetResult();

        // Handle search text box first
        this.filterResultByPhase(this.searchPhases);

        // Handle filters
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
                                    let topics = filter.split("=")[1].split(",");
                                    topics.forEach(topic => {
                                        if(oTopic["tag"].includes(topic))
                                        object.active = true;
                                    });
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
                    case "contactPoint.fn":
                        this.searchResults.forEach((object) => {
                            if(object.active == true){
                                object.active = false;
                            
                                // object["contactPoint"].forEach((contactPoint) => {
                                    if(object["contactPoint"]["fn"].includes(filter.split("=")[1]))
                                        object.active = true;
                                // })
                            }
                        });

                        break;
                    case "keyword":
                        this.searchResults.forEach((object) => {
                            if(object.active == true){
                                object.active = false;
                            
                                object["keyword"].forEach((keyword) => {
                                        if(keyword.includes(filter.split("=")[1]))
                                        object.active = true;
                                })
                            }
                        });

                        break;
                    default:
                        break;
                }
            })
        }

        this.searchResultsForDisplay = [];
        this.searchResults.forEach((object) => {
            if(object.active) this.searchResultsForDisplay.push(object);
        })

        this.getTotalResultItems();
    }

    /**
     * Sort the search result
     * @param event sort item
     */
    onSortByChange(event: any) {
        let key = event.value.value;

        if(key == "modified"){
            this.sortByDate();
        }else{
            this.searchResultsForDisplay.sort((a, b)=> {
                if(Array.isArray(a[key])){
                    if(key == "modified")
                        return b[key][0].localeCompare(a[key][0]);
                    else
                        return a[key][0].localeCompare(b[key][0]);
                }else{
                    if(key == "modified")
                        return b[key].localeCompare(a[key]);
                    else
                        return a[key].localeCompare(b[key]);
                }
            });
    
            this.refreshResult();
        }
    }

    /**
     * Sort the result by date
     */
    sortByDate(){
        if(!this.searchResultsForDisplay) return;

        this.searchResultsForDisplay.sort((a, b)=> {
            return b["modified"].localeCompare(a["modified"]);
        });

        this.refreshResult();
    }

    /**
     * Refresh the search result list
     */
    refreshResult() {
        this.showResult = false;
        setTimeout(() => {
            this.showResult = true;
        }, 0);
    }
}
