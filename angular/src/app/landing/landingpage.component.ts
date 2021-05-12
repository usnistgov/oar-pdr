import {
    Component, OnInit, AfterViewInit,
    ElementRef, PLATFORM_ID, Inject, ViewEncapsulation
} from '@angular/core';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import { Title } from '@angular/platform-browser';

import { AppConfig } from '../config/config';
import { MetadataService } from '../nerdm/nerdm.service';
import { EditStatusService } from './editcontrol/editstatus.service';
import { NerdmRes, NERDResource } from '../nerdm/nerdm';
import { IDNotFound } from '../errors/error';
import { MetadataUpdateService } from './editcontrol/metadataupdate.service';
import { LandingConstants } from './constants';
import { CartService } from '../datacart/cart.service';
import { DataCartStatus } from '../datacart/cartstatus';
import { RecordLevelMetrics } from '../metrics/metrics';
import { MetricsService } from '../shared/metrics-service/metrics.service';
import { CommonFunctionService } from '../shared/common-function/common-function.service';

/**
 * A component providing the complete display of landing page content associated with 
 * a resource identifier.  This content is handle in various sub-components.
 * 
 * Features include:
 * * an "identity" section, providing title, names, identifiers, and who is repsonsible
 * * description section, providing thd prose description/abstract, keywords, terms, ...
 * * a data access section, including a file listing (if files are availabe) and other links
 * * a references section
 * * tools and navigation section.
 *
 * This component sets the view encapsulation to None: this means that the style settings 
 * defined in landingpage.component.css apply globally, including to all the child components.
 */
@Component({
    selector: 'pdr-landing-page',
    templateUrl: './landingpage.component.html',
    styleUrls: ['./landingpage.component.css'],
    providers: [
        Title
    ],
    encapsulation: ViewEncapsulation.None
})
export class LandingPageComponent implements OnInit, AfterViewInit {
    layoutCompact: boolean = true;
    layoutMode: string = 'horizontal';
    profileMode: string = 'inline';
    md: NerdmRes = null;       // the NERDm resource metadata
    reqId: string;             // the ID that was used to request this page
    inBrowser: boolean = false;
    citetext: string = null;
    citationVisible: boolean = false;
    editEnabled: boolean = false;
    _showData: boolean = false;
    _showContent: boolean;
    headerObj: any;
    public EDIT_MODES: any;
    editMode: string;
    message: string;
    displaySpecialMessage: boolean = false;
    citationDialogWith: number = 550; // Default width
    recordLevelMetrics : RecordLevelMetrics;
    metricsUrl: string;

    // this will be removed in next restructure
    showMetadata = false;
    routerParamEditEnabled: boolean = false;

    loadingMessage = '<i class="faa faa-spinner faa-spin"></i> Loading...';

    dataCartStatus: DataCartStatus;

    /**
     * create the component.
     * @param route   the requested URL path to be fulfilled with this view
     * @param router  the router to use to reroute output, if necessary
     * @param titleSv the Title service (used to set the browser's title bar)
     * @param cfg     the app configuration data
     * @param mdserv  the MetadataService for gaining access to the NERDm metadata.
     * @param res     a CurrentResource object for sharing the metadata and requested 
     *                 ID with child components.
     */
    constructor(private route: ActivatedRoute,
        private router: Router,
        @Inject(PLATFORM_ID) private platformId: Object,
        public titleSv: Title,
        private cfg: AppConfig,
        private mdserv: MetadataService,
        public edstatsvc: EditStatusService,
        private cartService: CartService,
        private mdupdsvc: MetadataUpdateService,
        public commonFunctionService: CommonFunctionService,
        public metricsService: MetricsService) 
    {
        this.reqId = this.route.snapshot.paramMap.get('id');
        this.inBrowser = isPlatformBrowser(platformId);
        this.editEnabled = cfg.get('editEnabled', false) as boolean;
        this.EDIT_MODES = LandingConstants.editModes;

        this.edstatsvc.watchEditMode((editMode) => {
            this.editMode = editMode;
            if(this.editMode == this.EDIT_MODES.DONE_MODE || this.editMode == this.EDIT_MODES.OUTSIDE_MIDAS_MODE){
                this.displaySpecialMessage = true;
                this._showContent = true;
                this.setMessage();
            }
        });

        this.mdupdsvc.subscribe(
            (md) => {
                if (md && md != this.md) {
                    this.md = md as NerdmRes;
                }

                this.showData();
            }
        );

        this.edstatsvc.watchShowLPContent((showContent) => {
            this._showContent = showContent;
        });
    }

    /**
     * initialize the component.  This is called early in the lifecycle of the component by 
     * the Angular rendering infrastructure.
     */
    ngOnInit() {
        this.recordLevelMetrics = new RecordLevelMetrics();
        var showError: boolean = true;
        let metadataError = "";
        this.displaySpecialMessage = false;

        // Clean up cart status storage 
        if(this.inBrowser){
            this.dataCartStatus = DataCartStatus.openCartStatus();
            this.dataCartStatus.cleanUpStatusStorage();
        }
        // this.cartService.cleanUpStatusStorage();

        this.route.queryParamMap.subscribe(queryParams => {
            var param = queryParams.get("editEnabled");
            if(param)
                this.routerParamEditEnabled = (param.toLowerCase() == 'true');
            else
                this.routerParamEditEnabled = false;
        })

        // if editEnabled = true, we don't want to display the data that came from mdserver
        // Will set the display to true after the authentication process. If authentication failed, 
        // we set it to true and the data loaded from mdserver will be displayed. If authentication 
        // passed and draft data loaded from customization service, we will set this flag to true 
        // to display the data from MIDAS.
        if(this.routerParamEditEnabled) 
            this.edstatsvc.setShowLPContent(false);
        else 
            this.edstatsvc.setShowLPContent(true);

        // Retrive Nerdm record and keep it in case we need to display it in preview mode
        // use case: user manually open PDR landing page but the record was not edited by MIDAS
        // This part will only be executed if "editEnabled=true" is not in URL parameter.
        this.mdserv.getMetadata(this.reqId).subscribe(
        (data) => {
            // successful metadata request
            this.md = data;
            if (!this.md) {
                // id not found; reroute
                console.error("No data found for ID=" + this.reqId);
                metadataError = "not-found";
                //   this.router.navigateByUrl("/not-found/" + this.reqId, { skipLocationChange: true });
            }
            else{
                // Get metrics 
                this.getMetrics();

                // proceed with rendering of the component
                this.useMetadata();

                // if editing is enabled, and "editEnabled=true" is in URL parameter, try to start the page
                // in editing mode.  This is done in concert with the authentication process that can involve 
                // redirection to an authentication server; on successful authentication, the server can 
                // redirect the browser back to this landing page with editing turned on. 
                if(this.inBrowser){
                    // Display content after 15sec no matter what
                    setTimeout(() => {
                        this.edstatsvc.setShowLPContent(true);
                    }, 15000);
        
                  if (this.edstatsvc.editingEnabled()) 
                  {
                      if (this.routerParamEditEnabled) {
                          showError = false;
                        //   console.log("Returning from authentication redirection (editmode="+this.routerParamEditEnabled+")");
                          // Need to pass reqID (resID) because the resID in editControlComponent
                          // has not been set yet and the startEditing function relies on it.
                            this.edstatsvc.startEditing(this.reqId);
                      }else{
                          showError = true;
                      }
                  }else{
                      showError = true;
                  }
                }
            }

            if(showError){
                if(metadataError == "not-found"){
                    if(this.routerParamEditEnabled){
                        console.log("ID not found...");
                        this.edstatsvc._setEditMode(this.EDIT_MODES.OUTSIDE_MIDAS_MODE);
                        this.setMessage();
                        this.displaySpecialMessage = true;
                    }else{
                        this.router.navigateByUrl("not-found/" + this.reqId, { skipLocationChange: true });
                    }
                }

            }
        },
        (err) => {
            console.error("Failed to retrieve metadata: ", err);
            this.edstatsvc.setShowLPContent(true);
            if (err instanceof IDNotFound)
            {
                metadataError = "not-found";
                  this.router.navigateByUrl("not-found/" + this.reqId, { skipLocationChange: true });
            }else
            {
                metadataError = "int-error";
                // this.router.navigateByUrl("int-error/" + this.reqId, { skipLocationChange: true });

                this.router.navigateByUrl("int-error/" + this.reqId, { skipLocationChange: true });
            }
        }
        );
    }

    /**
     * Get metrics data
     */
    getMetrics() {
        console.log("this.md", this.md);
        let ediid = this.md.ediid;

        this.metricsService.getRecordLevelMetrics(ediid).subscribe(metricsData => {
            this.recordLevelMetrics = metricsData;
        });
    }

    get totalDownloadSize() {
        if(this.recordLevelMetrics.DataSetMetrics[0] != undefined)
            return this.commonFunctionService.formatBytes(this.recordLevelMetrics.DataSetMetrics[0].total_size, 2);
        else
            return "";
    }

    /**
     * apply housekeeping after view has been initialized
     */
    ngAfterViewInit() {
        if (this.md && this.inBrowser) {
            this.useFragment();
            window.history.replaceState({}, '', '/od/id/' + this.reqId);
        }
    }

    showData() : void{
      if(this.md != null){
        this._showData = true;
      }else{
        this._showData = false;
      }
    }

    /**
     * make use of the metadata to initialize this component.  This is called asynchronously
     * from ngOnInit after the metadata has been successfully retrieved (and saved to this.md).
     * 
     * This method will:
     *  * set the page's title (as displayed in the browser title bar).
     */
    useMetadata(): void {
        this.metricsUrl = "/metrics/" + this.reqId;
        // set the document title
        this.setDocumentTitle();
        this.mdupdsvc.setOriginalMetadata(this.md);
    }

    /**
     * set the document's title.  
     */
    setDocumentTitle(): void {
        let title = "PDR: ";
        if (this.md['abbrev']) title += this.md['abbrev'] + " - ";
        if (this.md['title'])
            title += this.md['title']
        else
            title += this.md['@id']
        this.titleSv.setTitle(title);
    }

    /**
     * return the current document title
     */
    getDocumentTitle(): string { return this.titleSv.getTitle(); }

    /**
     * apply the URL fragment by scrolling to the proper place in the document
     */
    public useFragment() {
        this.router.events.subscribe(s => {
            if (s instanceof NavigationEnd) {
                const tree = this.router.parseUrl(this.router.url);
                let element = null;
                if (tree.fragment) {
                    element = document.querySelector("#" + tree.fragment);
                }
                else {
                    element = document.querySelector("body");
                    if (!element)
                        console.warn("useFragment: failed to find document body!");
                }
                if (element) {
                    //element.scrollIntoView(); 
                    setTimeout(() => {
                        element.scrollIntoView({ behavior: "smooth", block: "start", inline: "nearest" });
                    }, 1);
                }
            }
        });
    }

    goToSection(sectionId: string) {
        this.showMetadata = (sectionId == "metadata");
        if (sectionId) 
            this.router.navigate(['/od/id/', this.reqId], { fragment: sectionId });
        else
            this.router.navigate(['/od/id/', this.reqId], { fragment: "" });
    }

    /**
     * display or hide citation information in a popup window.
     * @param yesno   whether to show (true) or hide (false)
     */
    showCitation(yesno: boolean): void {
        this.citationVisible = yesno;
    }

    /**
     * toggle the visibility of the citation pop-up window
     * @param size 
     */
    toggleCitation(size: string) : void { 
        if(size == 'small')
            this.citationDialogWith = 400;
        else
            this.citationDialogWith = 550;

        this.citationVisible = !this.citationVisible; 
    }

    /**
     * return text representing the recommended citation for this resource
     */
    getCitation(): string 
    {
        this.citetext = (new NERDResource(this.md)).getCitation();
        return this.citetext;
    }

    /**
     * Set the message to display based on the edit mode.
     */
    setMessage(){
        if(this.editMode == this.EDIT_MODES.DONE_MODE)
        {
            this.message = 'You can now close this browser tab <p>and go back to MIDAS to either accept or discard the changes.'
        }

        if(this.editMode == this.EDIT_MODES.OUTSIDE_MIDAS_MODE)
        {
            this.message = 'This record is not currently available for editing. <p>Please return to MIDAS and click "Edit Landing Page" to edit.'
        }
    }
}
