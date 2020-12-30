import { Component, OnInit, OnChanges, ElementRef, Input, Inject, APP_ID, HostListener, ViewChild } from '@angular/core';
import { Title, Meta } from '@angular/platform-browser';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { TreeNode } from 'primeng/primeng';
import { MenuItem } from 'primeng/api';
import { Observable, of } from 'rxjs';
import * as _ from 'lodash';
import 'rxjs/add/operator/map';
import { AppConfig } from '../config/config';
import { NerdmRes } from '../nerdm/nerdm';
import { tap } from 'rxjs/operators';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { EditControlComponent } from './editcontrol/editcontrol.component';
import { ModalService } from '../shared/modal-service';
import { AuthorPopupComponent } from './author/author-popup/author-popup.component';
import { NgbModalOptions, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ContactPopupComponent } from './contact/contact-popup/contact-popup.component';
import { SearchTopicsComponent } from './topic/topic-popup/search-topics.component';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import { HttpClient } from '@angular/common/http';
import { DescriptionPopupComponent } from './description/description-popup/description-popup.component';
import { DataFilesComponent } from './data-files/data-files.component';
import { ConfirmationDialogService } from '../shared/confirmation-dialog/confirmation-dialog.service';
import { NotificationService } from '../shared/notification-service/notification.service';
import { DatePipe } from '@angular/common';

import { MetadataUpdateService } from './editcontrol/metadataupdate.service';
import { LandingConstants } from '../landing/constants';
import { EditStatusService } from '../landing/editcontrol/editstatus.service';

declare var _initAutoTracker: Function;

interface reference {
    refType?: string,
    "@id"?: string,
    label?: string,
    location?: string
}

function compare_versions(a: string, b: string): number {
    let aflds: any[] = a.split(".");
    let bflds: any[] = b.split(".");
    let toint = function (el, i, a) {
        let e = null;
        try {
            return parseInt(el);
        } catch (e) {
            return el;
        }
    }
    aflds = aflds.map(toint);
    bflds = bflds.map(toint);
    let i: number = 0;
    let out: number = 0;
    for (i = 0; i < aflds.length && i < bflds.length; i++) {
        if (typeof aflds[i] === "number") {
            if (typeof bflds[i] === "number") {
                out = <number>aflds[i] - <number>bflds[i];
                if (out != 0) return out;
            }
            else
                return +1;
        }
        else if (typeof bflds[i] === "number")
            return -1;
        else
            return a.localeCompare(b);
    }
    return out;
}
function compare_dates(a: string, b: string): number {
    if (a.includes("Z"))
        a = a.substring(0, a.indexOf("Z"));
    if (a.includes("Z"))
        b = b.substring(0, a.indexOf("Z"));
    let asc = -1, bsc = -1;
    try {
        asc = Date.parse(a);
        bsc = Date.parse(b);
    } catch (e) { return 0; }
    return asc - bsc;
}
function compare_histories(a, b) {
    let out = 0;
    if (a.issued && b.issued)
        out = compare_dates(a.issued, b.issued);
    if (out == 0)
        out = compare_versions(a.version, b.version);
    return out;
}

@Component({
    selector: 'app-landing',
    templateUrl: './landing.component.html',
    styleUrls: ['./landing.component.css']
})

export class LandingComponent implements OnInit, OnChanges {
    layoutCompact: boolean = true;
    layoutMode: string = 'horizontal';
    profileMode: string = 'inline';
    status: string;
    keyword: string;
    findId: string;
    leftmenu: MenuItem[];
    rightmenu: MenuItem[];
    similarResources: boolean = false;
    similarResourcesResults: any[] = [];
    selectedFile: TreeNode;
    citeString: string = '';
    type: string = '';
    process: any[];
    isCopied: boolean = false;
    distdownload: string = '';
    mdApi: string = '';
    mdServer: string = '';
    private files: TreeNode[] = [];
    pdrApi: string = '';
    isResultAvailable: boolean = true;
    isId: boolean = true;
    displayContact: boolean = false;
    private meta: Meta;
    private newer: reference = {};
    navigationSubscription: any;
    displayDatacart: boolean = false;
    currentMode: string = 'initial';
    organizationList: string[] = ["National Institute of Standards and Technology"]
    HomePageLink: boolean = false;
    isVisible: boolean;
    editEnabled: boolean;
    doiUrl: string = null;
    recordType: string = "";
    editMode: string;
    EDIT_MODES: any;

    // passed in by the parent component:
    @Input() record: NerdmRes = null;
    @Input() requestId: string = null;     // the ID used in the URL to access this page
    @Input() inBrowser: boolean = false;

    // this will be removed in the next restructure iteration
    @Input() showMetadata: boolean = false;

    ediid: string = null;

    /**
     * Creates an instance of the LandingComponent
     *
     */
    constructor(
        private route: ActivatedRoute,
        private el: ElementRef,
        private titleService: Title,
        private cfg: AppConfig,
        private router: Router,
        @Inject(APP_ID) private appId: string,
        public mdupdsvc: MetadataUpdateService,
        private edstatsvc: EditStatusService,
        private gaService: GoogleAnalyticsService) 
    {
        this.editEnabled = cfg.get("editEnabled", false) as boolean;

        this.EDIT_MODES = LandingConstants.editModes;

        this.edstatsvc.watchEditMode((editMode) => {
          this.editMode = editMode;
        });
    }

    ngOnInit() { 
      // console.log('this.record', this.record);
    }

    ngOnChanges() {
        if (!this.ediid && this.recordLoaded())
            this.useMetadata();  // initialize internal component data based on metadata
    }

    /**
     * Return mdService
     */
    getMdService()
    {
        let mdService: string;

        mdService = this.cfg.get("locations.mdService", "/unconfigured");
            
        if (mdService.slice(-1) != '/') mdService += '/';
        if (mdService.search("/rmm/") < 0)
            mdService += this.record['ediid'];
        else
            mdService += "records?@id=" + this.record['@id'];


        return mdService;
    }

    /**
     * initial this component's internal data used to drive the display based on the 
     * input resource metadata
     */
    useMetadata(): void {
        this.ediid = this.record['ediid'];
        this.HomePageLink = this.displayHomePageLink();
        this.recordType = this.determineResourceLabel(this.record);

        this.createNewDataHierarchy();
        if (this.files.length > 0) {
            this.setLeafs(this.files[0].data);
        }

        if (this.record['doi'] !== undefined && this.record['doi'] !== "")
            this.doiUrl = "https://doi.org/" + this.record['doi'].split(':')[1];

        this.assessNewer();

        if (this.files.length != 0)
            this.files = <TreeNode[]>this.files[0].data;

    }

    /**
     * analyze the NERDm resource metadata and return a label indicating the type of 
     * the resource described.  This is used as a label at the top of the page, just above 
     * the title.
     */
    determineResourceLabel(resmd: NerdmRes): string {
        if (this.record['@type'] instanceof Array && this.record['@type'].length > 0) {
            switch (this.record['@type'][0]) {
                case 'nrd:SRD':
                    return "Standard Reference Data";
                case 'nrdp:DataPublication':
                    return "Data Publication";
                case 'nrdp:PublicDataResource':
                    return "Public Data Resource";
            }
        }

        return "Data Resource";
    }

    viewmetadata() {
        this.showMetadata = true;
        this.similarResources = false;
    }

    recordLoaded() {
        return this.record && !this.isEmptyObject(this.record);
    }

    //This is to check if empty
    isEmptyObject(obj) {
        return (Object.keys(obj).length === 0);
    }

    filescount: number = 0;
    createNewDataHierarchy() {
        var testdata = {}
        if (this.record['components'] != null) {
            testdata["data"] = this.arrangeIntoTree(this.record['components']);
            this.files.push(testdata);
        }
    }
    //This is to create a tree structure
    private arrangeIntoTree(paths) {
        const tree = [];
        // This example uses the underscore.js library.
        var i = 1;
        var tempfiletest = "";

        paths.forEach((path) => {
            if (path.filepath && !path['@type'].includes('nrd:Hidden')) {
                if (!path.filepath.startsWith("/"))
                    path.filepath = "/" + path.filepath;

                const pathParts = path.filepath.split('/');
                pathParts.shift(); // Remove first blank element from the parts array.
                let currentLevel = tree; // initialize currentLevel to root

                pathParts.forEach((part) => {
                    // check to see if the path already exists.
                    const existingPath = currentLevel.filter(level => level.data.name === part);
                    if (existingPath.length > 0) {

                        // The path to this item was already in the tree, so don't add it again.
                        // Set the current level to this path's children  
                        currentLevel = existingPath[0].children;
                    } else {
                        let tempId = path['@id'];
                        if (tempId == null || tempId == undefined)
                            tempId = path.filepath;

                        let newPart = null;
                        newPart = {
                            data: {
                                cartId: tempId,
                                ediid: this.ediid,
                                name: part,
                                mediatype: path.mediaType,
                                size: path.size,
                                downloadUrl: path.downloadURL,
                                description: path.description,
                                filetype: path['@type'][0],
                                resId: tempId,
                                // resId: path["filepath"].replace(/^.*[\\\/]/, ''),
                                filePath: path.filepath,
                                downloadProgress: 0,
                                downloadInstance: null,
                                isIncart: false,
                                zipFile: null,
                                message: ''
                            }, children: []
                        };
                        currentLevel.push(newPart);
                        currentLevel = newPart.children;
                        // }
                    }
                    this.filescount = this.filescount + 1;
                });
            }
            i = i + 1;
        });
        return tree;
    }

    /**
    * Set isLeaf to true for all leafs
    */
    setLeafs(files: any) {
        for (let comp of files) {
            if (comp.children.length > 0) {
                comp.data.isLeaf = false;
                this.setLeafs(comp.children);
            } else {
                if (comp.data.filetype == 'nrdp:DataFile' || comp.data.filetype == 'nrdp:ChecksumFile') {
                    comp.data.isLeaf = true;
                } else {
                    comp.data.isLeaf = false;
                }
            }
        }
    }

    visibleHistory = false;
    expandHistory() {
        this.visibleHistory = !this.visibleHistory;
        return this.visibleHistory;
    }
    /**
    * create an HTML rendering of a version string for a NERDm VersionRelease.  
    * If there is information available for linking to version's home page, a 
    * link is returned.  Otherwise, just the version is returned (prepended 
    * with a "v").
    */
    renderRelVer(relinfo, thisversion) {
        if (thisversion == relinfo.version)
            return "v" + relinfo.version;
        return this.renderRelAsLink(relinfo, "v" + relinfo.version);
    }
    renderRelAsLink(relinfo, linktext) {
        let out: string = linktext;
        if (relinfo.location)
            out = '<a href="' + relinfo.location + '">' + linktext + '</a>';
        else if (relinfo.refid) {
            if (relinfo.refid.startsWith("doi:"))
                out = '<a href="https://doi.org/' + relinfo.refid.substring(4) + '">' + linktext + '</a>';
            else if (relinfo.refid.startsWith("ark:/88434/"))
                out = '<a href="https://data.nist.gov/od/id/' + relinfo.refid + '">' + linktext + '</a>';
        }
        return out;
    }
    /**
    * return a rendering of a release's ID.  If possible, the ID will be 
    * rendered as a link.  If there is no ID, a link with the text "View..." 
    * is returned. 
    *
    * NOTE: the behavior of this function is being temporarily changed until 
    *       there is better version support from the metadata service
    */
    renderRelId(relinfo, thisversion) {
        if (thisversion == relinfo.version)
            return "this version";
        // let id: string = "View...";
        let id: string = "";
        if (relinfo.refid) {
            id = relinfo.refid;
            if (this.editMode != this.EDIT_MODES.EDIT_MODE)
                return this.renderRelAsLink(relinfo, id);
        }
        return id;
    }

    display: boolean = false;

    showDialog() {
        this.display = true;
    }
    closeDialog() {
        this.display = false;
    }

    public setTitle(newTitle: string) {
        this.titleService.setTitle(newTitle);
    }

    /**
     * Check if current record contains reference for display.
     * Valid reference types are IsDocumentedBy and IsSupplementTo.
     */
    checkReferences() {
        if (Array.isArray(this.record['references'])) {
            for (let ref of this.record['references']) {
                if (ref.refType == "IsDocumentedBy" || ref.refType == "IsSupplementTo") return true;
            }
        }
    }

    /**
     * Return the link text of the given reference.
     * 1. the value of the label property (if set and is not empty)
     * 2. the value of the citation property (if set and is not empty)
     * 3. to "URL: " appended by the value of the location property.
     * @param refs reference object
     */
    getReferenceText(refs){
        if(refs['label']) 
            return refs['label'];
        if(refs['citation'])
            return refs['citation'];
        return refs['location'];
    }

    isArray(obj: any) {
        return Array.isArray(obj);
    }

    isObject(obj: any) {
        if (typeof obj === "object") {
            return true;
        }
    }
    showContactDialog() {
        this.displayContact = true;
    }

    /**
     * analyze the given resource metadata to determine if a newer version is 
     * available.  Currently, this looks in three places (in order) within the 
     * NERDm record:
     * <ol>
     *   <li> the 'isReplacedBy' property </li>
     *   <li> as a 'isPreviousVersionOf' reference in the references list.
     *   <li> in the 'versionHistory' property </li>
     * </ol>
     * The checks for last two places may be removed in a future release. 
     */
    assessNewer() {
        if (!this.record) return;
        // look for the 'isReplacedBy'; this is expected to be inserted into the
        // record on the fly by the server based on the values of 'replaces' in
        // all other resources.
        if (this.record['isReplacedBy']) {
            this.newer = this.record['isReplacedBy'];
            if (!this.newer['refid']) this.newer['refid'] = this.newer['@id'];
            return;
        }
        // look for a reference with refType="isPreviousVersionOf"; the
        // referenced resource is a newer version. 
        if (this.record['references']) {
            for (let ref of this.record['references']) {
                if (ref.refType == "IsPreviousVersionOf" && (ref.label || ref.refid)) {
                    this.newer = ref;
                    if (!this.newer['refid']) this.newer['refid'] = this.newer['@id'];
                    if (!this.newer.label) this.newer.label = ref.newer.refid;
                    return;
                }
            }
        }
        // look at the version history to see if there is a newer version listed
        //
        // TODO: this block is being temporarily disable because there is a flaw in the code comparing
        //       history entries.  This will prevent the "there's a newer version available" message
        //       from appearing erroneously
        // 
        if (false && this.record['version'] && this.record['versionHistory']) {
            let history = this.record['versionHistory'];
            history.sort(compare_histories);

            var thisversion = this.record['version'];
            var p = thisversion.indexOf('+');    // presence indicates this is an update
            if (p >= 0) thisversion = thisversion.substring(0, p)   // strip off +...

            if (compare_histories(history[history.length - 1],
                {
                    version: thisversion,
                    issued: this.record['modified']
                }) > 0) {
                // this version is older than the latest one in the history
                this.newer = history[history.length - 1];
                if (!this.newer['refid']) this.newer['refid'] = this.newer['@id'];
                this.newer['label'] = this.newer['version'];
                if (!this.newer['location'] && this.newer['refid']) {
                    if (this.newer['refid'].startsWith("doi:"))
                        this.newer.location = 'https://doi.org/' + this.newer['refid'].substring(4);
                    else if (this.newer['refid'].startsWith("ark:/88434/"))
                        this.newer.location = 'https://data.nist.gov/od/id/' + this.newer['refid'].substring(4);
                }
            }
        }
    }

    /*
     *   This function is used to track ngFor loop
     */
    trackByFn(index: any, author: any) {
        return index;
    }

    /* 
    *   Check if this record has a home page link that does not point to the landing page itself
    */
    displayHomePageLink() {
        if (this.record.landingPage == null || this.record.landingPage == undefined) {
            return false;
        }
        return (this.record.landingPage.search(/^https?:\/\/[\w\.\-]+\/od\/id\//) < 0)
    }

    visitHomePage(url: string, event, title) {
        this.gaService.gaTrackEvent('homepage', event, title, url);
        window.open(url, '_blank');
    }

    // This can be uncommented for debugging purposes
    //
    // @ViewChild(EditControlComponent)
    // ecc : EditControlComponent;
}

