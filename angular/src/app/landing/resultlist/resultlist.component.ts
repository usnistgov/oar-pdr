import { Component, OnInit, Input, SimpleChanges, ViewChild, ElementRef } from '@angular/core';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { SearchService } from '../../shared/search-service/index';
import { AppConfig } from '../../config/config';
import { timeout } from 'rxjs-compat/operator/timeout';
import { ThisReceiver } from '@angular/compiler';
import * as e from 'express';
import { connectableObservableDescriptor } from 'rxjs/internal/observable/ConnectableObservable';
import { GoogleAnalyticsService } from '../../shared/ga-service/google-analytics.service';
import { Themes, ThemesPrefs, Collections, Collection, ColorScheme, CollectionThemes } from '../../shared/globals/globals';
import * as CollectionData from '../../../assets/site-constants/collections.json';
import { CollectionService } from '../../shared/collection-service/collection.service';

@Component({
  selector: 'app-resultlist',
  templateUrl: './resultlist.component.html',
  styleUrls: ['../landing.component.css', './resultlist.component.css'],
  animations: [
        trigger('detailExpand', [
        state('void', style({height: '0px', minHeight: '0'})),
        state('collapsed', style({height: '0px', minHeight: '0'})),
        state('expanded', style({height: '*'})),
        transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
        transition('expanded <=> void', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
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
    searchResultsForDisplayOriginal: any[];
    searchResultsOriginal: any[];
    currentIndex: number = 0;
    resultCount: number = 0;
    options = [{name:'Title', value:'title'}, {name:'Description', value:'description'}, {name:'Last Modified Date (Default)', value:'modified'}, {name:'Keyword', value:'keyword'}];
    optionSelected: string;
    searchPhases: string = "";
    searchFields: string[] = ["title", "description", "keyword"];
    PDRAPIURL: string = "https://data.nist.gov/lps/";
    isEmail: boolean = false;
    homeBtnBackColor: string = "white";

    //Result display
    showResult: boolean = true;
    showResultList: boolean = false;
    noSearchResult: boolean = false;
    // expandButtonAlterText: string = "Open dataset details";

    //Pagination
    totalResultItems: number = 0;
    totalPages: number = 0;
    itemsPerPage: number = 10;
    pages = [{name:'Page 1', value:1},{name:'Page 2', value:2}];
    currentPage: any = {name:'Page 1', value:1};

    allCollections: any = {};

    //  Color
    colorScheme: ColorScheme;
    defaultColor: string;
    lightColor: string;  
    lighterColor: string;  

    @Input() md: NerdmRes = null;
    @Input() searchValue: string;
    @Input() searchTaxonomyKey: string;
    @Input() mobWidth: number = 1920;
    @Input() resultWidth: string = '400px';
    @Input() filterString: string = '';
    @Input() collection: string = Collections.FORENSICS;
    @Input() taxonomyURI: any = {};

    constructor(private searchService: SearchService, 
        private cfg: AppConfig,
        public collectionService: CollectionService,
        public gaService: GoogleAnalyticsService) { }

    ngOnInit(): void {
        this.colorScheme = this.collectionService.getColorScheme(this.collection);
        this.PDRAPIURL = this.cfg.get('locations.landingPageService',
                                   'https://data.nist.gov/od/id/');

        let that = this;
        let urls = (new NERDResource(this.md)).dynamicSearchUrls();

        for(let i=0; i < urls.length; i++){
            this.searchService.resolveSearchRequest(urls[i])
            .subscribe(
                searchResults => {
                    this.resultCount = searchResults['ResultCount'];
                    that.onSuccess(searchResults.ResultData);
                },
                error => that.onError(urls[i], error)
            );
        }

        this.allCollections = this.collectionService.loadAllCollections();
    }

    onPageChange(value: any){
        // console.log("this.currentPage", value.target.value);
    }

    ngOnChanges(changes: SimpleChanges): void {
        if(changes.filterString != null && changes.filterString != undefined) {
            this.filterResults();
        }
    }

    get resultWidthNum() {
        if(this.resultWidth == "100%")
            return 400;
        else {
            return this.resultWidth.substring(0, this.resultWidth.length-2)
        }
    }

    onSelected(event) {
        console.log("event", event.target.value);
        this.currentPage = this.pages.filter(p => p.name == event.target.value)[0];
        console.log("this.currentPage", this.currentPage);
    }

    /**
     * Processing search results
     * @param searchResults search results
     */
    onSuccess(searchResults: any[]) {
        searchResults.forEach((object) => {
            object['expandIcon'] = "faa faa-caret-right";
            object['isExpanded'] = false;
            object['active'] = true;
        })

        this.searchResultsOriginal = JSON.parse(JSON.stringify(searchResults));
        let srchResults = JSON.parse(JSON.stringify(searchResults));

        if(this.searchResults && this.searchResults.length > 0) 
            this.searchResults = [...this.searchResults, ...srchResults];
        else
            this.searchResults = srchResults;

        //Init searchResults
        for(let item of this.searchResults) {
            item.active = true;
        }

        this.filterResults();
        this.sortByDate();

        this.showResultList = true;
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
     *  Expand the row to display file details. It's little tricky when hiding the details. 
     *  We have to delay the action to let the animation to finish. 
     * @param fileNode       the TreeNode for the file to provide details for
     */
    toggleDetails(fileNode: any, index: number) {
        let currentFileNode = this.searchResultsForDisplay[this.currentIndex];
        //Close current details window if it's open
        if(index != this.currentIndex && currentFileNode != undefined) {
            currentFileNode.expandIcon = "faa faa-caret-right";
            currentFileNode.isExpanded = false;
        }

        this.currentIndex = index;

        if(fileNode.isExpanded){
            fileNode.isExpanded = false;
            fileNode.expandIcon = "faa faa-caret-right";
        }else{
            fileNode.isExpanded = true;
            fileNode.expandIcon = "faa faa-caret-down";            
        }
    }

    /**
     * This function returns alter text/tooltip text for the expand symbol next to the given treenode title
     * @param fileNode the TreeNode
     * @returns 
     */
    expandButtonAlterText(fileNode: any) {
        if(fileNode.isExpanded)
            return "Close dataset details";
        else
            return "Open dataset details";
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
    onError(url: string, error: any) {
        console.error("Search URL ("+url+") failed to resolve: "+error.message);
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
    resetResult(active: boolean = false) {
        if(this.searchResults) {
            this.searchResults.forEach((object) => {
                object.expandIcon = "faa faa-caret-right";
                object.isExpanded = false;
                object.active = active;
            })
        }
    }

    /**
     * Restore reserved chars. For example, change "aaamp" back to "&".
     * @param inputString 
     */
    restoreReservedChars(inputString: string) {
        if(!inputString || inputString.trim() == "")
            return "";
        else
            return inputString.replace(new RegExp("aaamp", "g"), "&"); 
    }

    /**
     * Apply filters from left side panel and the search word(s) from the search text box
     */
    filterResults() {
        if(this.searchResults == undefined) return;

        let filters: string[];
        
        // Reset the search result
        this.resetResult(this.filterString=="NoFilter");

        // Handle search text box first
        this.filterResultByPhase(this.searchPhases);

        // Handle filters
        if(this.filterString != "noFilter" && this.filterString != ""){
            filters = this.filterString.split("&");
            filters.forEach((filter) => {
                switch(filter.split("=")[0]){
                    case "@type":
                        this.searchResults.forEach((object) => {
                            if(!object.active){
                                // object.active = false;

                                object["@type"].forEach((oType) => {
                                    let types = filter.split("=")[1].split(",");
                                    types.forEach(type => {
                                        if(oType.toLowerCase().includes(this.restoreReservedChars(type).toLowerCase()))
                                            object.active = true;
                                    });
                                })
                            } 
                        });

                        break;
                    case "topic.tag":
                        let topics = filter.split("=")[1].split(",");
                        for(let resultItem of this.searchResults) {
                            
                            if(!resultItem.active){
                                // resultItem.active = false;

                                for(let oTopic of resultItem["topic"]) {
                                    for(let topic of topics) {
                                        let collection = topic.split("----")[0];
                                        let topicValue = this.restoreReservedChars(topic.split("----")[1]);

                                        if(oTopic['scheme'].indexOf(this.taxonomyURI[collection]) >= 0) {
                                            if(collection == Collections.DEFAULT) {
                                                if(oTopic["tag"].toLowerCase().includes(topicValue.toLowerCase()))
                                                    resultItem.active = true;
                                            }else {
                                                if(oTopic["tag"].toLowerCase() == (topicValue.toLowerCase()))
                                                    resultItem.active = true;
                                            }
                                        }
                                    };
                                };
                            }
                        };

                        break;
                    case "components.@type":
                        this.searchResults.forEach((object) => {
                            if(object["components"] != undefined) {
                                if(!object.active){
                                    // object.active = false;
    
                                    object["components"].forEach((component) => {
                                        component["@type"].forEach((cType) => {
                                            let types = filter.split("=")[1].split(",");
                                            types.forEach(type => {
                                                if(cType.toLowerCase().includes(this.restoreReservedChars(type).toLowerCase()))
                                                    object.active = true;
                                            });
                                        })
                                    })
                                }
                            }else {
                                object.active = false;
                            }
                        });

                        break;
                    case "contactPoint.fn":
                        this.searchResults.forEach((object) => {
                            if(!object.active){
                                // object.active = false;
                            
                                if(object["contactPoint"]["fn"].includes(filter.split("=")[1]))
                                    object.active = true;
                            }
                        });

                        break;
                    case "keyword":
                        // Loop through each keyword in each search result. Display those that match
                        // the keywords from keyword filter
                        this.searchResults.forEach((object) => {
                            if(!object.active){
                                // object.active = false;
                            
                                object["keyword"].forEach((keyword) => {
                                    //Loop through each search keyword from keyword filter
                                    filter.split("=")[1].split(",").forEach(kw => {
                                        if(keyword.toLowerCase().includes(this.restoreReservedChars(kw))){
                                            object.active = true;
                                        }
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

        this.searchResultsForDisplay = [];
        this.searchResults.forEach((object) => {
            if(object.active) this.searchResultsForDisplay.push(object);
        })

        this.searchResultsForDisplayOriginal = JSON.parse(JSON.stringify(this.searchResultsForDisplay));

        this.getTotalResultItems();
        this.currentPage = this.pages[0];
    }

    /**
     * Sort the search result
     * @param event sort item
     */
    onSortByChange(event: any) {
        // console.log("event", event.value);
        if(event.target.value == "none") {
            this.searchResultsForDisplay = JSON.parse(JSON.stringify(this.searchResultsForDisplayOriginal));

            this.refreshResult();
            event.target.value = "";
            return;
        }

        let key = this.options.filter(o => o.name == event.target.value)[0].value;

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

    /**
     * Determine if a given dataset has contact point email
     * @param dataset 
     * @returns 
     */
    hasEmail(dataset: any) {
        if(dataset['contactPoint'])
            return 'hasEmail' in dataset['contactPoint'];
        else
            return false;
    }

    /**
     * Get the doi url from the given dataset. If not available, return blank.
     * @param dataset 
     * @returns doi url. Return blank if not available.
     */
    doiUrl(dataset: any) {
        if (dataset['doi'] !== undefined && dataset['doi'] !== "")
            return "https://doi.org/" + dataset['doi'].substring(4);
        else    
            return "";
    }

    lastModified(dataset: any) {
        let lastDate: Date;
        if(dataset.modified) {
            lastDate = new Date(dataset.modified.slice(0,10));
            return lastDate.toLocaleDateString();
        }else{
            return "None";
        }
    }
}
