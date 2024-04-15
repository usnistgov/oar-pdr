import { Component, EventEmitter, Input, OnInit, Output, HostListener, Inject, PLATFORM_ID } from '@angular/core';
import { CollectionService } from '../../shared/collection-service/collection.service';
import { Themes, ThemesPrefs, Collections, Collection, ColorScheme, CollectionThemes } from '../../shared/globals/globals';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { CartConstants } from '../../datacart/cartconstants';
import { AppConfig } from '../../config/config';
import * as _ from 'lodash-es';
import { isPlatformBrowser } from '@angular/common';
import { MetricsData } from "../metrics-data";

export class menuItem {
    title: string;
    backgroundColor: string;
    isHeader: boolean;
    sectionName: string;
    icon: string;
    url: string;

    constructor(
        title: string, 
        sectionName: string = "",
        url: string,
        backgroundColor: string = "white", 
        isHeader: boolean = false,
        icon: string = ""){
            this.title = title;
            this.sectionName = sectionName;
            this.url = url;
            this.backgroundColor = backgroundColor;
            this.isHeader = isHeader;
            this.icon = icon;
    }
} 

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.css']
})
export class MenuComponent implements OnInit {
    defaultColor: string;
    lighterColor: string;
    hoverColor: string;
    allCollections: any = {};
    resourceType: string;
    gotoMenu: menuItem[] = [] as menuItem[];
    useMenu: menuItem[] = [] as menuItem[];
    findMenu: menuItem[] = [] as menuItem[];
    public CART_CONSTANTS: any = CartConstants.cartConst;
    globalCartUrl: string = "/datacart/" + this.CART_CONSTANTS.GLOBAL_CART_NAME;
    recordType: string = "";
    scienceTheme = Themes.SCIENCE_THEME;
    inBrowser: boolean = false;

    // the resource record metadata that the tool menu data is drawn from
    @Input() record : NerdmRes|null = null;    
    @Input() collection: string = Collections.DEFAULT;
    @Input() theme: string = "nist";

    // Record level metrics data
    @Input() metricsData : MetricsData;

    // flag if metrics is ready to display
    @Input() showMetrics : boolean = false;

    @Output() scroll = new EventEmitter<string>();
    
    // signal for triggering display of the citation information
    @Output() toggle_citation = new EventEmitter<boolean>();

    constructor(
        public collectionService: CollectionService,
        @Inject(PLATFORM_ID) private platformId: Object,
        private cfg : AppConfig) { 
            this.inBrowser = isPlatformBrowser(platformId);
        }

    ngOnInit(): void {
        this.allCollections = this.collectionService.loadCollections(this.collection.toLowerCase());

        this.setColor();

        this.resourceType = ThemesPrefs.getResourceLabel(this.theme);

        this.buildMenu();
    }

    buildMenu() {
        this.gotoMenu.push(new menuItem("Go To...", "", "", this.defaultColor, true));
        this.gotoMenu.push(new menuItem("Top", "top", "", this.lighterColor, false, "faa faa-arrow-circle-right menuicon"));
        this.gotoMenu.push(new menuItem("Description", "description", "", this.lighterColor, false, "faa faa-arrow-circle-right menuicon"));
        this.gotoMenu.push(new menuItem("Data Access", "dataAccess", "", this.lighterColor, false, "faa faa-arrow-circle-right menuicon"));
        this.gotoMenu.push(new menuItem("About This "+this.resourceType, "about","", this.lighterColor, false, "faa faa-arrow-circle-right menuicon"));

        this.useMenu.push(new menuItem("Use", "", "", this.defaultColor, true));
        this.useMenu.push(new menuItem("Citation", "citation", "", this.lighterColor, false, "faa faa-angle-double-right"));
        this.useMenu.push(new menuItem("Repository Metadata", "Metadata", "", this.lighterColor, false, "faa faa-angle-double-right"));
        this.useMenu.push(new menuItem("Fair Use Statement","", this.record['license'], this.lighterColor, false, "faa faa-external-link"));
        this.useMenu.push(new menuItem("Data Cart", "", this.globalCartUrl, this.lighterColor, false, "faa faa-cart-plus"));

        let searchbase = this.cfg.get("locations.pdrSearch","/sdp/")
        if (searchbase.slice(-1) != '/') searchbase += "/"
        let authlist = "";
        if (this.record['authors']) {
            for (let i = 0; i < this.record['authors'].length; i++) {
                if(i > 0) authlist += ',';
                let fn = this.record['authors'][i]['fn'];

                if (fn != null && fn != undefined && fn.trim().indexOf(" ") > 0)
                    authlist += '"'+ fn.trim() + '"';
                else    
                authlist += fn.trim();
            }
        }

        let contactPoint = "";
        if (this.record['contactPoint'] && this.record['contactPoint'].fn) {
            contactPoint = this.record['contactPoint'].fn.trim();
            if(contactPoint.indexOf(" ") > 0){
                contactPoint = '"' + contactPoint + '"';
            }
        }

        // If authlist is empty, use contact point instead
        let authorSearchString: string = "";
        if(_.isEmpty(authlist)){
            authorSearchString = "/#/search?q=contactPoint.fn%3D" + contactPoint;
        }else{
            authorSearchString = "/#/search?q=authors.fn%3D" + authlist + "%20OR%20contactPoint.fn%3D" + contactPoint;
        }

        if (!authlist) {
            if (this.record['contactPoint'] && this.record['contactPoint'].fn) {
                let splittedName = this.record['contactPoint'].fn.split(' ');
                authlist = splittedName[splittedName.length - 1];
            }
        }

        let keywords: string[] = this.record['keyword'];
        let keywordString: string = "";
        for(let i = 0; i < keywords.length; i++){
            if(i > 0) keywordString += ',';

            if(keywords[i].trim().indexOf(" ") > 0)
                keywordString += '"' + keywords[i].trim() + '"';
            else
            keywordString += keywords[i].trim();
        }

        let resourceLabel: string = "Similar Resources";
        if(this.recordType == Themes.SCIENCE_THEME){
            resourceLabel = "Resources in this Collection";
        }

        this.findMenu.push(new menuItem("Find", "", "", this.defaultColor, true));

        this.findMenu.push(new menuItem(resourceLabel, "", searchbase + "#/search?q=keyword%3D" + keywordString, this.lighterColor, false, "faa faa-external-link" ))
        this.findMenu.push(new menuItem('Resources by Authors', "", this.cfg.get("locations.pdrSearch", "/sdp/") + authorSearchString, this.lighterColor, false,  "faa faa-external-link" ))


    }

    /**
     * switch the display of the Citation information:  if it is currently showing,
     * it should be hidden; if it is not visible, it should be shown.  This method
     * is trigger by clicking on the "Citation" link in the menu; clicking 
     * alternatively both shows and hides the display.
     *
     * The LandingPageComponent handles the actual display of the information
     * (currently implemented as a pop-up).  
     */
    toggleCitation() {
        this.toggle_citation.emit(true);
    }

    /**
     * Set color variables
     */
    setColor() {
        this.defaultColor = this.allCollections[this.collection.toLowerCase()].color.default;
        this.lighterColor = this.allCollections[this.collection.toLowerCase()].color.lighter;
        this.hoverColor = this.allCollections[this.collection.toLowerCase()].color.hover;
    }   
    
    /**
     * scroll to the specified section of the landing page
     */
    goToSection(sectname : string, url: string = "") {
        if (sectname) {
            console.info("scrolling to #"+sectname+"...");
        }else{
            console.info("scrolling to top of document");
        }

        switch(sectname) { 
            case "citation": { 
                this.toggleCitation();
                break; 
            } 
            case "": { 
                if(url)
                    window.open(url,'_blank');
                break; 
            } 
            default: { 
                this.scroll.emit(sectname);
                break; 
            } 
         } 
        
    }    
}
