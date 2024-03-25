import { Component, Input, Output, OnChanges, ViewChild, EventEmitter } from '@angular/core';

import { MenuItem } from 'primeng/api';
import { Menu } from 'primeng/menu';

import { AppConfig } from '../../config/config';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { EditStatusService } from '../editcontrol/editstatus.service';
import * as _ from 'lodash-es';
import { RecordLevelMetrics } from '../../metrics/metrics';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { CartConstants } from '../../datacart/cartconstants';
import { Collections, Themes, ThemesPrefs } from '../../shared/globals/globals';


/**
 * A component for displaying access to landing page tools in a menu.
 * 
 * Items include:
 * * links to the different sections of the landing page
 * * links to view or export metadata
 * * information about usage (like Citation information in a pop-up)
 * * links for searching for similar resources
 */
@Component({
    selector: 'tools-menu',
    template: `
<p-menu #tmenu [ngClass]="menuStyle()" 
               [popup]="isPopup" [model]="items" [appendTo]="appendTo"></p-menu>
`,
    styleUrls: ['./toolmenu.component.css']
})
export class ToolMenuComponent implements OnChanges {
    recordType: string = "";

    // the resource record metadata that the tool menu data is drawn from
    @Input() record : NerdmRes|null = null;

    // true if this menu should appear as a popup
    @Input() isPopup : boolean = false;
    @Input() appendTo : boolean = false;
    @Input() theme: string = "nist"
    @Input() collection: string = Collections.DEFAULT;

    // signal for triggering display of the citation information
    @Output() toggle_citation = new EventEmitter<boolean>();

    // signal for scrolling to a section within the page
    @Output() scroll = new EventEmitter<string>();

    // reference to the child menu (needed to toggle display when isPopup = true)
    @ViewChild('tmenu', { static: true })
    private menu : Menu;

    // the menu item configuration
    items: MenuItem[] = [];
    public CART_CONSTANTS: any = CartConstants.cartConst;
    globalCartUrl: string = "/datacart/" + this.CART_CONSTANTS.GLOBAL_CART_NAME;
    editEnabled: any;

    /**
     * create the component.
     * @param cfg   the app configuration data
     */
    constructor(
        private cfg : AppConfig,
        public commonFunctionService: CommonFunctionService,
        public edstatsvc: EditStatusService) {  
            this.editEnabled = cfg.get("editEnabled", "");
    }

    ngOnInit(): void {
        //Called after the constructor, initializing input properties, and the first call to ngOnChanges.
        //Add 'implements OnInit' to the class.
        // console.log("menu this.theme", this.theme);
    }

    /**
     * toggle the appearance of a popup menu
     */
    togglePopup(click) {
        if (this.isPopup)
            this.menu.toggle(click);
    }

    /**
     * update the component state when the record metadata is updated
     */
    ngOnChanges() {
        if (this.record) {
            this.recordType = (new NERDResource(this.record)).resourceLabel();
            this.theme = (new NERDResource(this.record)).theme();
            this.updateMenu();
        }
    }

    menuStyle() {
        if(this.theme == Themes.SCIENCE_THEME) {
            if(this.isPopup) 
                return 'rightMenuStylePopST';
            else{
                if(this.collection == Collections.FORENSICS)
                    return 'rightMenuStyleST rightMenuStyleForensicsHeader rightMenuStyleForensicsItem';
                else
                    return 'rightMenuStyleST rightMenuStyleSemiconductorsHeader rightMenuStyleSemiconductorsItem';
            }
        }else{
            if(this.isPopup) 
                return 'rightMenuStylePop';
            else
                return 'rightMenuStyle';
        }
    }

    /**
     * configure the menu using data from the record metadata
     */
    updateMenu() {
        var mitems : MenuItem[] = [];
        var subitems : MenuItem[] = [];
        let hasMetrics: boolean = false;

        let mdService: string;
        mdService = this.cfg.get("locations.mdService", "/unconfigured");

        if (mdService.slice(-1) != '/') mdService += '/';
        if (mdService.search("/rmm/") < 0)
            mdService += this.record['ediid'];
        else
            mdService += "records?@id=" + this.record['@id'];

        // Go To...
        // top of the page
        subitems.push(
            this.createMenuItem("Top", "faa faa-arrow-circle-right",
                                (event) => { this.goToSection(null); }, null)
        );

        // Go To Description
        subitems.push(
            this.createMenuItem("Description", "faa faa-arrow-circle-right",
                                (event) => { this.goToSection('description'); }, null)
        );

        // is it possible to not have a data access section?
        subitems.push(
            this.createMenuItem("Data Access", "faa faa-arrow-circle-right",
                                (event) => { this.goToSection('dataAccess'); }, null)
        );
        
        if (this.record['references'])
            subitems.push(
                this.createMenuItem("References", "faa faa-arrow-circle-right ",
                                    (event) => { this.goToSection('references'); }, null)
            );

            
        let resourceType: string = ThemesPrefs.getResourceLabel(this.theme);

        subitems.push(
            this.createMenuItem("About This " + resourceType, "faa faa-arrow-circle-right ",
                                (event) => { this.goToSection('about'); }, null)
        );
        mitems.push({ label: 'Go To...', items: subitems });

        // Use
        let disableMenu = false;
        if(this.editEnabled) disableMenu = true;

        subitems = [];

        if(this.theme != Themes.SCIENCE_THEME) {
            subitems = [
                this.createMenuItem('Citation', "faa faa-angle-double-right", (event) => { this.toggleCitation(); }, null)
            ]
        }

        subitems = [...subitems, 
            this.createMenuItem("Repository Metadata", "faa faa-angle-double-right",
                                (event) => { this.goToSection('Metadata'); }, null),            
            this.createMenuItem("Fair Use Statement", "faa faa-external-link", null,
                                this.record['license']),
            this.createMenuItem("Data Cart", "faa faa-cart-plus", null,
                                this.globalCartUrl, "_blank", disableMenu)
        ];


        mitems.push({ label: "Use", items: subitems });

        // Find
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

        subitems = [
            this.createMenuItem(resourceLabel, "faa faa-external-link", null,
                                searchbase + "#/search?q=keyword%3D" + keywordString),
            this.createMenuItem('Resources by Authors', "faa faa-external-link", "",
            this.cfg.get("locations.pdrSearch", "/sdp/") + authorSearchString)
        ];
        mitems.push({ label: "Find", items: subitems });

        this.items = mitems;
    }

    /**
     * create an entry for a menu
     * @param label     the label that should appear on the menu entry
     * @param icon      the class labels that define the icon to display next to the menu label
     * @param command   a function that should be executed when the menu item is selected.
     *                    The function should take a single argument representing the selection
     *                    event object
     * @param url       a URL that should be navigated to when the menu item is selected.
     */
    createMenuItem(label: string, icon: string, command: any, url: string, target: string = "_blank", disabled: boolean = false) {
        let item : MenuItem = {
            label: label,
            icon: icon
        };
        if (command)
            item.command = command;
        if (url) {
            item.url = url;
            item.target = target;
        }

        item.disabled = disabled;

        return item;
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
     * scroll to the specified section of the landing page
     */
    goToSection(sectname : string) {
        if (sectname) 
            console.info("scrolling to #"+sectname+"...");
        else
            console.info("scrolling to top of document");
        this.scroll.emit(sectname);
    }
}
