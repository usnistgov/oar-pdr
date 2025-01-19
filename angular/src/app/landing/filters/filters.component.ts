import { Component, OnInit, Inject, Input, AfterViewInit, Output, EventEmitter, SimpleChanges } from '@angular/core';
import { SelectItem } from 'primeng/api';
import { TreeNode } from 'primeng/api';
// import { Message } from 'primeng/components/common/api';
import { Message } from 'primeng/api';
import { TaxonomyListService, SearchfieldsListService } from '../../shared/index';
import * as _ from 'lodash-es';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { SearchService } from '../../shared/search-service';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { AppConfig } from '../../config/config';
import { Themes, ThemesPrefs, Collections, Collection, CollectionThemes, FilterTreeNode, ColorScheme } from '../../shared/globals/globals';
import { CollectionService } from '../../shared/collection-service/collection.service';

const SEARCH_SERVICE = 'SEARCH_SERVICE';

@Component({
    selector: 'app-filters',
    templateUrl: './filters.component.html',
    styleUrls: ['./filters.component.css'],
    providers: [TaxonomyListService, SearchfieldsListService],
    animations: [
        trigger('expand', [
            state('closed', style({height: '50px'})),
            state('collapsed', style({height: '183px'})),
            state('expanded', style({height: '*'})),
            transition('expanded <=> collapsed', animate('625ms')),
            transition('expanded <=> closed', animate('625ms')),
            transition('closed <=> collapsed', animate('625ms'))
        ]),
        trigger('expandOptions', [
            state('collapsed', style({height: '0px'})),
            state('expanded', style({height: '*'})),
            transition('expanded <=> collapsed', animate('625ms'))
        ]),
        trigger('filterExpand', [
            state('collapsed', style({width: '40px'})),
            state('expanded', style({height: '*'})),
            transition('expanded <=> collapsed', animate('625ms'))
        ])
    ]
})
export class FiltersComponent implements OnInit {
    searchResults: any[] = [];
    suggestedThemes: string[] = [];
    suggestedKeywords: string[] = [];
    suggestedKeywordsLkup: any = {};
    suggestedAuthors: string[] = [];
    selectedAuthor: any[] = [];
    selectedKeywords: any[] = [];;
    selectedThemes: any[] = [];
    selectedComponents: any[] = [];
    selectedComponentsNode: any[] = [];
    selectedResourceType: any[] = [];
    selectedResourceTypeNode: any[] = [];
    selectedAuthorDropdown: boolean = false;
    resourceTypes: SelectItem[] = [];
    resourceTypesAllArray: string[] = [];
    uniqueRes: string[] = [];
    resourceTypesWithCount: FilterTreeNode[] = [];
    authors: string[] = [];
    components: SelectItem[] = [];
    componentsAllArray: string[] = [];
    componentsWithCount: FilterTreeNode[] = [];
    showComponents: string[] = ["Data File", "Access Page", "Subcollection"];
    MoreOptionsDisplayed: boolean = false;
    moreOptionsText: string = "Show More Options...";

    allUnspecifiedCount: any = {};
    unspecifiedCount: number = 0;
    showMoreLink: boolean = true;
    clearAllCheckbox: boolean = false;

    collectionThemesWithCount: FilterTreeNode[] = [];
    filterObjs = {};

//  Object that hold all themes: Forensics, NIST, ...
    allCollections: any = {};

//  Array to define the collection order
    collectionOrder: string[] = [Collections.DEFAULT];

//  Color
    colorScheme: ColorScheme;
    collapedFilerColor: string;  //For collaped filter

    componentsTree: TreeNode[] = [];
    resourceTypeTree: TreeNode[] = [];
    resultStatus: string;
    RESULT_STATUS = {
        'success': 'SUCCESS',
        'noResult': 'NO RESULT',
        'userError': 'USER ERROR',
        'sysError': 'SYS ERROR'
    }
    keywords: string[];
    searchResultsError: Message[] = [];
    searching: boolean = false;
    msgs: Message[] = [];
    status: string;
    fieldsArray: any[];
    fields: SelectItem[] = [];
    searchResType: string;
    searchResTopics: string;
    searchRecord: string;
    searchAuthors: string;
    searchKeywords: string;
    displayFields: string[] = [];
    queryAdvSearch: string;
    page: number = 1;
    isActive: boolean = true;
    filterClass: string;
    resultsClass: string;
    nodeExpanded: boolean = false;
    collectionNodeExpanded: boolean = true;
    comheight: string = '50px'; // parent div height
    comwidth: string;  // parent div width
    dropdownLabelLengthLimit: number = 30;

    filterStyle = {'width':'100%', 'background-color': '#FFFFFF','font-weight': '400','font-style': 'italic'};

    ResourceTypeStyle = {'width':'auto','padding-top': '.5em','padding-right': '.5em',
    'padding-bottom': '.5em','background-color': 'var(--science-theme-background-light)','border-width':'0'};

    researchTopicStyle = {'width':'100%','padding-top': '.5em', 'padding-bottom': '.5em', 'background-color': 'var(--science-theme-background-light)', 'overflow':'hidden','border-width':'0'};

    recordHasStyle = {'width':'auto','padding-top': '.5em','padding-right': '.5em',
    'padding-bottom': '.5em','background-color': 'var(--science-theme-background-light)','border-width':'0'}

    //Error handling
    queryStringErrorMessage: string = "";
    queryStringError: boolean = false;
    errorMessage: string;
    exception: string;
    errorMsg: string;

    @Input() md: NerdmRes = null;
    @Input() searchValue: string;
    @Input() searchTaxonomyKey: string;
    @Input() parent: HTMLElement; // parent div
    @Input() filterWidthNum: number;
    @Input() mobileMode: boolean = false;
    @Input() theme: string;
    @Input() collection: string = Collections.FORENSICS;
    @Input() taxonomyURI: any = {};
    @Output() filterMode = new EventEmitter<string>();  // normal or collapsed
    @Output() filterObjsOut = new EventEmitter<any[]>();  

    constructor(
        public taxonomyListService: TaxonomyListService,
        public searchFieldsListService: SearchfieldsListService,
        public searchService: SearchService,
        public collectionService: CollectionService,
        private cfg: AppConfig
    ) { 

    }

    ngOnInit(): void {
        // this.collectionService.loadAllCollections();

        this.collectionOrder = this.collectionService.getCollectionOrder();
        this.msgs = [];
        this.searchResultsError = [];
        this.MoreOptionsDisplayed = (this.theme == 'ScienceTheme');
        this.setFilterWidth();

        this.allCollections = this.collectionService.loadAllCollections();
        this.colorScheme = this.collectionService.getColorScheme(this.collection);

        // Set colors
        this.setColor();
    }

    setColor() {
        this.collapedFilerColor = "linear-gradient(" +  this.colorScheme.default + ", white)";
    }

    /**
     * Update the filter string object based on the input filter string
     * @param $event filter string returned from app-taxonomy
     */
    updateFilterObj(event, collection: string) {
        let _filterObj = event;
        if(!event) _filterObj = null;

        this.filterObjs[collection] = _filterObj;

        this.createFilterObj();
    }

    /**
     * Form the filter string and refresh the result page
     */
    createFilterObj() {
        let lFilterObjs: any[] = [];

        // Resource type        
        if(this.filterObjs["@type"] && this.filterObjs["@type"].value.length>0) {
            lFilterObjs.push(this.filterObjs["@type"]);
        }

        // Collections
        for(let col of this.collectionOrder) {
            if(this.filterObjs[col] && this.filterObjs[col].value && this.filterObjs[col].value.length>0) {
                lFilterObjs.push(this.filterObjs[col]);
            }   
        }

        // Record has
        if(this.filterObjs["components.@type"] && this.filterObjs["components.@type"].value.length>0) {
            lFilterObjs.push(this.filterObjs["components.@type"]);
        }

        // Authors and contributors
        if (this.selectedAuthor.length > 0) {
            let authors: string[] = [];
            
            for (let author of this.selectedAuthor) {
                authors.push(author);
            }

            lFilterObjs.push({
                "type": "contactPoint.fn",
                "value": authors
            })
        }

        // Keywords
        if (this.selectedKeywords.length > 0) {
            let keywords: string[] = [];

            for (let keyword of this.selectedKeywords) {
                keywords.push(this.suggestedKeywordsLkup[keyword]);
            }

            lFilterObjs.push({
                "type": "keyword",
                "value": keywords
            })
        }

        if(!lFilterObjs || lFilterObjs.length == 0) {
            lFilterObjs.push({
                "type": "NoFilter",
                "value": ""
            })
        }

        this.filterObjsOut.emit(lFilterObjs);
    }

    /**
     * If search value changed, clear the filters and refresh the search result.
     * @param changes - changed detected
     */
    ngOnChanges(changes: SimpleChanges) {
        if(changes.filterWidthNum != undefined && changes.filterWidthNum != null){
            if (changes.filterWidthNum.currentValue != changes.filterWidthNum.previousValue) {
                if(changes.filterWidthNum.currentValue < 40)
                    this.isActive = false;
                else
                    this.isActive = true;
            }
        }

        if(changes.searchValue != undefined && changes.searchValue != null){

            if (changes.searchValue.currentValue != changes.searchValue.previousValue || 
                changes.searchTaxonomyKey.currentValue != changes.searchTaxonomyKey.previousValue) {

                //Clear filters when we conduct a new search
                this.clearFilters();
                this.getFields();
            }
        }
    }

    get isForensics() {
        return this.collection == Collections.FORENSICS;
    }

    get isSemiconductors() {
        return this.collection == Collections.SEMICONDUCTORS;
    }

    toggleMoreOptions() {
        this.MoreOptionsDisplayed = !this.MoreOptionsDisplayed;
        if(this.MoreOptionsDisplayed)
            this.moreOptionsText = "Show More Options...";
        else
            this.moreOptionsText = "Hide Options...";
    }   
    
    /**
     * After view init, make the filter width the same as parent div in the parent component
     * Default width is 400px.
     */
    ngAfterViewInit() {
        if(this.parent)
            this.comwidth = this.parent.clientWidth + 'px';
        else
            this.comwidth = '400px';
    }

    /**
     * Get the filterable fields and then do the search
     */
    getFields() {
        this.searchFieldsListService.get().subscribe(
            fields => {
                this.toSortItems(fields);
                if(! this.queryStringErrorMessage){ 
                    this.queryStringError = true;
                }

                this.doSearch();
            },
            error => {
                this.errorMessage = <any>error
            }
        );
    }

    /**
     * Do the search
     * @param query - search query
     * @param searchTaxonomyKey - Taxonomy keys if any
     */
    // doSearch(query: SDPQuery, searchTaxonomyKey?: string) {

    doSearch() {
            this.msgs = [];
        this.searchResultsError = [];
        this.search();

        this.selectedResourceTypeNode = [];
        this.selectedComponentsNode = [];

        // Turn spinner off after 60 seconds (if still waiting for the result)
        setTimeout(() => {
            this.searching = false;
        }, 60000)
    }

    /**
     * Sort the given fields and populate this.fields
     * @param fields 
     */
    toSortItems(fields: any[]) {
        this.fieldsArray = fields;
        let sortItems: SelectItem[] = [];
        this.fields = [];
        let dupFound: boolean = false;

        for (let field of fields) {
            if (_.includes(field.tags, 'filterable')) {
                if (field.type !== 'object') {
                    if (field.name !== 'component.topic.tag') {
                        dupFound = false;
                        for(let item of sortItems){
                            if(item.label==field.label && item.value==field.name){
                                dupFound = true;
                                break;
                            }
                        }
                        if(!dupFound)
                            sortItems.push({ label: field.label, value: field.name });
                    }
                }
            }

            if (_.includes(field.tags, 'searchable')) {
                let lValue = field.name.replace('component.', 'components.');

                dupFound = false;
                for(let item of this.fields){
                    if(item.label==field.label && item.value==lValue){
                        dupFound = true;
                        break;
                    }
                }
                if(!dupFound)
                    this.fields.push({ label: field.label, value: lValue });
            }
        }

        this.fields = _.sortBy(this.fields, ['label','value']);
    }

    /**
     * call the Search service with parameters
     */
    //  search(query: SDPQuery, searchTaxonomyKey?: string) {
    search() {
        this.searching = true;
        let that = this;
        let urls = (new NERDResource(this.md)).dynamicSearchUrls();
        for(let i=0; i < urls.length; i++){
            return this.searchService.resolveSearchRequest(urls[i])
            .subscribe(
                searchResults => {
                    that.onSuccess(searchResults.ResultData);
                },
                error => that.onError(error)
            );
        }
    }

    /**
     * If Search is successful, populate list of keywords themes and authors
     * @param searchResults 
     */
    onSuccess(searchResults: any[]) {
        this.resultStatus = this.RESULT_STATUS.success;
        // this.themesWithCount = [];
        this.componentsWithCount = [];
        this.searchResults = searchResults;

        this.keywords = this.collectKeywords(searchResults);
        this.collectThemes(searchResults);
        this.resourceTypes = this.collectResourceTypes(searchResults);

        let compNoData: boolean = false;
        this.searchResultsError = [];

        if (searchResults.length === 0) {
            this.resultStatus = this.RESULT_STATUS.noResult;
        }

        for(let col of this.collectionOrder) {
            this.collectThemesWithCount(col, searchResults);
        }

        this.components = this.collectComponents(searchResults);

        // collect Resource features with count
        this.collectComponentsWithCount();
        this.collectResourceTypesWithCount();

        if (this.componentsWithCount.length == 0) {
            compNoData = true;
            this.componentsWithCount = [];
            this.componentsTree = [{
                label: 'Record has',
                "expanded": true,
                children: this.componentsWithCount,
            }];

            this.componentsWithCount.push(new FilterTreeNode("DataFile - 0", false, "DataFile", "DataFile", 0));
            this.componentsWithCount.push(new FilterTreeNode("AccessPage - 0", false, "AccessPage", "AccessPage", 0));
            this.componentsWithCount.push(new FilterTreeNode("SubCollection - 0", false, "SubCollection", "SubCollection", 0));

            this.componentsTree[0].selectable = false;

            for (var i = 0; i < this.componentsWithCount.length; i++) {
                this.componentsTree[0].children[i].selectable = false;
            }
        }

        if(!this.allCollections[Collections.DEFAULT]) {
            this.allCollections[Collections.DEFAULT] = {} as Collection;
        }

        if(!this.allCollections[Collections.DEFAULT].theme) {
            this.allCollections[Collections.DEFAULT].theme = {} as CollectionThemes;
        }
        
        if(!this.allCollections[this.collection]) {
            this.allCollections[this.collection] = {} as Collection;
        }

        if(!this.allCollections[this.collection].theme) {
            this.allCollections[this.collection].theme = {} as CollectionThemes;
        }

        for(let col of this.collectionOrder) {
            if(this.collectionThemesWithCount[col].children.length > 0) {
                this.allCollections[col].theme.collectionThemesTree = [{
                    label: this.allCollections[col].tag,
                    "expanded": (col != Collections.DEFAULT),
                    level: 1,
                    children: this.collectionThemesWithCount[col].children
                }];
            }
        }

        this.resourceTypeTree = [{
            label: 'Type of Resource',
            "expanded": false,
            children: this.resourceTypesWithCount
        }];

        if (!compNoData) {
            this.componentsTree = [{
                label: 'Record has',
                "expanded": false,
                children: this.componentsWithCount,
            }];
        }
        this.authors = this.collectAuthors(searchResults);

        this.searching = false;
    }

    /**
     * If search is unsuccessful push the error message
     */
    onError(error: any[]) {
        this.searchResults = [];
        this.keywords = [];
        this.msgs = [];

        if((<any>error).status == 400){
            this.resultStatus = this.RESULT_STATUS.userError;
        }else{
            this.resultStatus = this.RESULT_STATUS.sysError;
        }

        this.exception = (<any>error).ex;
        this.errorMsg = (<any>error).message;
        this.status = (<any>error).httpStatus;
        this.msgs.push({ severity: 'error', summary: this.errorMsg + ':', detail: this.status + ' - ' + this.exception });
        this.searching = false;
    }

    /**
     * Remove the ending comma of the given string
     * @param inputrString 
     */
    removeEndingComma(inputrString: string): string{
        if(!inputrString) return "";

        if(inputrString[inputrString.length-1] == ",")
            return inputrString.substr(0, inputrString.length-1);
        else    
            return inputrString;
    }

    /**
     * Create a list of suggested authors based on given search query
     * @param event - search query that user typed into the filter box
     */
    filterAuthors(event) {
        //in a real application, make a request to a remote url with the query and return filtered results, for demo we filter at client side
        let author = event.query;
        let filtered: any[] = [];
        let query = event.query;
        for (let i = 0; i < this.authors.length; i++) {
          let auth = this.authors[i];
          if (auth.toLowerCase().indexOf(author.toLowerCase()) >= 0) {
            filtered.push(auth);
          }
        }
    
        this.suggestedAuthors = filtered;
    }

    /**
     * Create a list of suggested keywords based on given search query
     * Because some keywords might be very long, for display purpose we only show the first few words in
     * the dropdown list.
     * suggestedKeywords - for display
     * suggestedKeywordsLkup - stores the real ketwords
     * @param event - search query that user typed into the keyword filter box
     */
     updateSuggestedKeywords(event: any) {
        let keyword = event.query.toLowerCase();
        this.suggestedKeywords = [];
        this.suggestedKeywordsLkup = {};

        // Handle current keyword: update suggested keywords and lookup
        for (let i = 0; i < this.keywords.length; i++) {
            let keyw = this.keywords[i].trim().toLowerCase();
            if (keyw.indexOf(keyword) >= 0) {
                //Avoid duplicate
                if(this.suggestedKeywordsLkup[this.shortenKeyword(keyw)] == undefined) {
                    this.suggestedKeywords.push(this.shortenKeyword(keyw));
                    this.suggestedKeywordsLkup[this.shortenKeyword(keyw)] = keyw;
                }
            }
        }

        // Handle selected keyword: update suggested keywords lookup. Lookup array must cover all selected keywords.
        this.selectedKeywords.forEach(kw => {
            for (let i = 0; i < this.keywords.length; i++) {
                let keyw = this.keywords[i].trim().toLowerCase();
                if (keyw.indexOf(kw.toLowerCase()) >= 0) {
                    if(this.suggestedKeywordsLkup[this.shortenKeyword(keyw)] == undefined) {
                        this.suggestedKeywordsLkup[this.shortenKeyword(keyw)] = keyw;
                    }
                }
            }
        })

        this.suggestedKeywords = this.sortAlphabetically(this.suggestedKeywords);
    }

    /**
     * Some keywords are very long. They cause problem when display both in suggested keyword list or 
     * selected keyword list. This function returns the first few words of the input keyword. The length 
     * of the return string is based on this.dropdownLabelLengthLimit but not exactly. 
     * If the length of the input keyword is less than dropdownLabelLengthLimit, the input keyword will be returned.
     * Otherwise, It selects the first few words whose total length is just exceed the length limit followed by "...".
     * @param keyword 
     * @returns Keyword abbreviate
     */
     shortenKeyword(keyword: string) {
        let keywordAbbr: string;

        //If the keyword length is greater than the maximum length, we want to truncate
        //it so that the length is close the maximum length.

        if(keyword.length > this.dropdownLabelLengthLimit){
            let wordCount = 1;
            while(keyword.split(' ', wordCount).join(' ').length < this.dropdownLabelLengthLimit) {
                wordCount++;
            }

            keywordAbbr = keyword.substring(0, keyword.split(' ', wordCount).join(' ').length);
            if(keywordAbbr.trim().length < keyword.length) keywordAbbr = keywordAbbr + "...";

            let i = 1;
            let tmpKeyword = keywordAbbr;
            while(Object.keys(this.suggestedKeywordsLkup).indexOf(tmpKeyword) >= 0 
                    && this.suggestedKeywordsLkup[tmpKeyword] != keyword && i < 100){
                tmpKeyword = keywordAbbr + "(" + i + ")";
                i++;
            }
            keywordAbbr = tmpKeyword;
        }else    
            keywordAbbr = keyword;

        return keywordAbbr;
    }

    /**
     * Sort arrays alphabetically
     * @param array - array to be sorted
     */
    sortAlphabetically(array: string[]) {
        var sortedArray: string[] = array.sort((n1, n2) => {
            if (n1 > n2) 
                return 1;

            if (n1 < n2) 
                return -1;

            return 0;
        });

        return sortedArray;
    }

    /**
     * Return filter icon image class based on filter status
     */
    getFilterImgClass(){
        if(this.isActive){
            if(this.mobileMode){
               return "faa faa-angle-double-up"; 
            }else{
                return "faa faa-angle-double-left";
            }
        }else{
            if(this.mobileMode){
                return "faa faa-angle-double-down";
            }else{
                return "faa faa-angle-double-right";
            }
        }
    }

    /**
     * clear filters
     */
    clearFilters() {
        this.searchService.setClearAll(true);
        setTimeout(() => {
            this.searchService.setClearAll(false);
        }, 0)

        this.filterObjs = {};
        this.suggestedThemes = [];
        this.suggestedKeywords = [];
        this.suggestedAuthors = [];
        this.selectedAuthor = [];
        this.selectedKeywords = [];
        this.selectedThemes = [];
        this.selectedComponents = [];
        this.selectedComponentsNode = [];
        this.selectedAuthorDropdown = false;
        this.selectedResourceType = [];
        this.selectedResourceTypeNode = [];
        // this.resourceTypes = this.collectResourceTypes(this.searchResults);
        // this.collectResourceTypesWithCount();
        // this.authors = this.collectAuthors(this.searchResults);
        // this.suggestedKeywords = this.collectKeywords(this.searchResults);
        // this.components = this.collectComponents(this.searchResults);
        // this.collectComponentsWithCount();
        // this.collectThemes(this.searchResults);

        // this.collectThemesWithCount(Collections.DEFAULT);
        // this.collectThemesWithCount(this.collection);

        // this.componentsTree = [{
        //     label: 'Record has -',
        //     "expanded": false,
        //     children: this.componentsWithCount
        // }];

        // this.resourceTypeTree = [{
        //     label: 'Resource Type -',
        //     "expanded": false,
        //     children: this.resourceTypesWithCount
        // }];

        this.nodeExpanded = false;
        this.collectionNodeExpanded = true;
        
        this.clearAllCheckbox = true;
        setTimeout(() => {
            this.clearAllCheckbox = false;
        }, 0)
    }

    /**
     * Get resource type from search result
     * @param searchResults search result
     */
    collectResourceTypes(searchResults: any[]) {
        let resourceTypes: SelectItem[] = [];
        let resourceTypesArray: string[] = [];
        let resType: string;
        let tempType: any;
        this.resourceTypesAllArray = [];
        for (let resultItem of searchResults) {
            this.uniqueRes = [];
            let resTypeArray = resultItem['@type'];
            for (var i = 0; i < resTypeArray.length; i++) {
                resType = resTypeArray[i];
                this.uniqueRes.push(_.startCase(_.split(resType, ':')[1]));
                tempType = {
                    label: _.startCase(_.split(resType, ':')[1]),
                    value: _.startCase(_.split(resType, ':')[1])
                };

                if(resourceTypes.map(e => e.label).indexOf(tempType.label) < 0){
                    resourceTypes.push(tempType);
                }

                if (resourceTypesArray.indexOf(resType) < 0) {
                    resourceTypesArray.push(resType);
                }
            }

            this.uniqueRes = this.uniqueRes.filter(this.onlyUnique);
            for (let res of this.uniqueRes) {
                this.resourceTypesAllArray.push(res);
            }
        }

        return resourceTypes;
    }

    /**
     * Collect resource type + count
     */
    collectResourceTypesWithCount() {
        this.resourceTypesWithCount = [];
        for (let res of this.resourceTypes) {
            let count: any;
            count = _.countBy(this.resourceTypesAllArray, _.partial(_.isEqual, res.value))['true'];

            this.resourceTypesWithCount.push(new FilterTreeNode(res.label + "---" + count, true, res.label, res.label, count));
        }
    }

    /**
     * For unique filter
     * @param value 
     * @param index 
     * @param self 
     */
    onlyUnique(value, index, self) {
        return self.indexOf(value) === index;
    }

    /**
     * Get authors from search result
     * @param searchResults search result
     */
    collectAuthors(searchResults: any[]) {
        let authors: string[] = [];
        for (let resultItem of searchResults) {
        if (resultItem.contactPoint && resultItem.contactPoint !== null && resultItem.contactPoint.fn !== null) {
            if (authors.indexOf(resultItem.contactPoint.fn) < 0) {
                authors.push(resultItem.contactPoint.fn);
            }
        }
        }
        return authors;
    }

    /**
     * Get keywords from search result
     * @param searchResults search result
     */
    collectKeywords(searchResults: any[]) {
        let kwords: string[] = [];
        let tempkeywords: string[] = [];

        for (let resultItem of searchResults) {
            if (resultItem.keyword && resultItem.keyword !== null && resultItem.keyword.length > 0) {
                for (let keyword of resultItem.keyword) {
                    //If keyword value contains semicolons, split them
                    tempkeywords = keyword.split(";");
                    for(let kw of tempkeywords) {
                        if (kwords.indexOf(kw) < 0) {
                            kwords.push(kw);
                        }
                    }
                }
            }
        }
        return kwords;
    }

    /**
     * Collect components from search results
     * @param searchResults - search results
     */
    collectComponents(searchResults: any[]) {
        let components: SelectItem[] = [];
        let componentsArray: string[] = [];
        let compType: string;
        let uniqueComp: string[] = [];

        this.componentsAllArray = [];

        for (let resultItem of searchResults) {
            if(resultItem['components'] != null && resultItem['components'] != undefined && resultItem['components'].length > 0){
                uniqueComp = [];
                let allcomponents = resultItem['components'];
                for(let component of allcomponents){
                    let resTypeArray = component['@type'];
                    for (var i = 0; i < resTypeArray.length; i++) {
                        compType = _.startCase(_.split(resTypeArray[i], ':')[1])
                        if(uniqueComp.indexOf(compType) < 0)
                            uniqueComp.push(compType);
                
                        if(compType != null && compType != undefined && _.includes(resTypeArray[i], 'nrdp')){
                            if (componentsArray.indexOf(resTypeArray[i]) < 0) {
                                components.push({
                                label: compType,
                                value: compType
                                });
                                componentsArray.push(resTypeArray[i]);
                            }
                        }   
                    }
                }

                for (let comp of uniqueComp) {
                this.componentsAllArray.push(comp);
                }
            }
        }
        return components;
    }

    /**
     * Collect components + count
     */
    collectComponentsWithCount() {
        this.componentsWithCount = [];
        for (let comp of this.components) {
            let count: any;
            if (this.showComponents.includes(comp.label)) {
                count = _.countBy(this.componentsAllArray, _.partial(_.isEqual, comp.value))['true'];

                this.componentsWithCount.push(new FilterTreeNode(comp.label + "---" + count, true, comp.label, comp.label, count));
            }
        }
    }

    /**
     * Collect themes from Search results
     * @param searchResults - search results
     */
    collectThemes(searchResults: any[]) {
        let allThemes: any = {};
        allThemes[Collections.DEFAULT] = [];
        allThemes[Collections.FORENSICS] = [];
        allThemes[Collections.SEMICONDUCTORS] = [];

        let allThemesArray: any = {};
        allThemesArray[Collections.DEFAULT] = [];
        allThemesArray[Collections.FORENSICS] = [];
        allThemesArray[Collections.SEMICONDUCTORS] = [];

        let topicLabel: string;
        let data: string;

        let allUniqueThemes: any = {};
        allUniqueThemes[Collections.DEFAULT] = [];
        allUniqueThemes[Collections.FORENSICS] = [];
        allUniqueThemes[Collections.SEMICONDUCTORS] = [];

        let allThemesAllArray: any = {};
        allThemesAllArray[Collections.DEFAULT] = [];
        allThemesAllArray[Collections.FORENSICS] = [];
        allThemesAllArray[Collections.SEMICONDUCTORS] = [];

        this.unspecifiedCount = 0;
        
        //Collecting all themes
        for (let resultItem of searchResults) {
            if (typeof resultItem.topic !== 'undefined' && resultItem.topic.length > 0) {
                for (let topic of resultItem.topic) {
                    let topics = topic.tag.split(":");
                    topicLabel = topics[0];
                    data = topic.tag;

                    if(topics.length > 1){
                        // topicLabel = topics[0] + ":" + topics[1];
                        topicLabel = topic.tag;
                    }
                    
                    if(topic['scheme'].indexOf(this.taxonomyURI[Collections.SEMICONDUCTORS]) >= 0) {
                        topicLabel = topics[0];
                        data = topic.tag;

                        if(topics.length > 1){
                            // topicLabel = topics[0] + ":" + topics[1];
                            topicLabel = topic.tag;
                        }

                        if(allThemesArray[Collections.SEMICONDUCTORS].indexOf(topicLabel) < 0) {
                            allThemes[Collections.SEMICONDUCTORS].push({ label: topicLabel, value: data });
                            allThemesArray[Collections.SEMICONDUCTORS].push(topicLabel);
                        }
                    }else if(topic['scheme'].indexOf(this.taxonomyURI[Collections.FORENSICS]) >= 0) {
                        data = topic.tag;

                        if(topics.length > 1){
                            topicLabel = topic.tag;
                        }

                        if(allThemesArray[Collections.FORENSICS].indexOf(topicLabel) < 0) {
                            allThemes[Collections.FORENSICS].push({ label: topicLabel, value: data });
                            allThemesArray[Collections.FORENSICS].push(topicLabel);
                        }
                    }else if(topic['scheme'].indexOf(this.taxonomyURI[Collections.DEFAULT]) >= 0){
                        topicLabel = topics[0];

                        if (allThemesArray[Collections.DEFAULT].indexOf(topicLabel) < 0) {
                            allThemes[Collections.DEFAULT].push({ label: topicLabel, value: topic.tag });
                            allThemesArray[Collections.DEFAULT].push(topicLabel);
                        }
                    }
                }
            } else {
                this.unspecifiedCount += 1;
            }
        }

        //Find unique themes
        for (let resultItem of searchResults) {
            for(let col of this.collectionOrder){
                allUniqueThemes[col] = [];
            }

            if (typeof resultItem.topic !== 'undefined' && resultItem.topic.length > 0) {
                for (let topic of resultItem.topic) {
                    let topicTag = topic.tag;

                    for(let col of this.collectionOrder) {
                        for(let theme of allThemes[col]){
                            if(topicTag.toLowerCase().indexOf(theme.label.toLowerCase()) > -1){
                                allUniqueThemes[col].push(theme.label);
                            }
                        }
                    }
                }

                for(let col of this.collectionOrder) {
                    allThemesAllArray[col] = allThemesAllArray[col].concat(allUniqueThemes[col].filter(this.onlyUnique));
                }
            }
        }

        for(let col of this.collectionOrder) {
            if(!this.allCollections[col]){
                this.allCollections[col] = {} as Collection;
            }

            if(!this.allCollections[col].theme){
                this.allCollections[col].theme = {} as CollectionThemes;
            }

            this.allCollections[col].theme.collectionThemes = allThemes[col];
            this.allCollections[col].theme.collectionThemesAllArray = allThemesAllArray[col];
        }
    }

    /**
     * Find the location of nth character in a string
     * @param string - string to search from
     * @param nth - occuence
     * @param char - character to search for
     * @returns position of the character
     */
    findNthOccurence(string, nth, char) {
        let index = 0
        for (let i = 0; i < nth; i += 1) {
          if (index !== -1) index = string.indexOf(char, index + 1)
        }
        return index
    }

    /**
     * Collect NIST themes + count
     */
    collectThemesWithCount(collection: string, searchResults: any = null) {
        if(!searchResults) return;

        let sortable: any[] = [];
        let expand = (collection != Collections.DEFAULT);
        sortable = [];
        this.collectionThemesWithCount[collection] = new FilterTreeNode(this.collection + ' Research Topics', expand);

        if(!this.allCollections[collection]){
            this.allCollections[collection] = {} as Collection;
        }

        if(!this.allCollections[collection].theme)
            this.allCollections[collection].theme = {} as CollectionThemes;

        if(!this.allCollections[collection].theme.collectionThemesWithCount)
            this.allCollections[collection].theme.collectionThemesWithCount = [];

        for (let theme in (_.countBy(this.allCollections[collection].theme.collectionThemesAllArray))) {
            sortable.push([theme, _.countBy(this.allCollections[collection].theme.collectionThemesAllArray)[theme]]);
        }
        
        sortable.sort(function (a, b) {
            return b[1] - a[1];
        });

        if (this.unspecifiedCount > 0 && collection == Collections.DEFAULT) {
            sortable.push(['Unspecified', this.unspecifiedCount]);
        }

        for (var key in sortable) {
            this.collectionThemesWithCount[collection].upsertNodeFor(sortable[key], 1, searchResults, collection, this.taxonomyURI);
        }

        if (sortable.length > 5) {
            this.showMoreLink = true;
        } else {
            this.showMoreLink = false;
        }
    }

    /**
     * Set the width of the filter column. If the filter is active, set the width to 25%. 
     * If the filter is collapsed, set the width to 40px.
     */
     setFilterWidth() {
        if (!this.isActive) {
            this.filterMode.emit("collapsed");
        } else {
            this.filterMode.emit('normal');
        }
    }    

    /**
     * Return tooltip text for given filter tree node.
     * @param filternode tree node of a filter
     * @returns tooltip text
     */
    filterTooltip(filternode: any) {
        if(filternode && filternode.label)
            return filternode.label.split('---')[0] + "-" + filternode.label.split('---')[1];
        else
            return "";
    }
}
