import { Component, OnInit, PLATFORM_ID, Inject, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import 'rxjs/add/operator/map';
import { TreeNode } from 'primeng/primeng';
import { DownloadStatus } from './cartconstants';
import { ZipData } from '../shared/download-service/zipData';
import { isPlatformBrowser } from '@angular/common';
import { CartService } from './cart.service';
import { DataCart } from './cart';
import { BundleplanComponent } from './bundleplan/bundleplan.component';

/**
 * a component that provides an interface for viewing the contents of a data cart and download items 
 * from it in bulk (as zip files).  It includes three main subcomponents:
 *   * `CartcontrolComponent` -- the control panel for initiating downloads and cleaning out the contents  
 *           of the cart.
 *   * `BundleplanComponent` -- a panel that displays the status of zipfiles being created and downloaded
 *   * `TreetableComponent` -- a panel showing the contents of the cart as a hierarchical tree.
 * 
 * A `DatacartComponent` provides a view of only one cart; the cart it displays and controls is determined
 * by the cart name it is given (via its HTML template).  
 */
@Component({
    moduleId: module.id,
    selector: 'data-cart',
    templateUrl: 'datacart.component.html',
    styleUrls: ['datacart.component.css'],
})
export class DatacartComponent implements OnInit {
    inBrowser: boolean = false;

    //Connection
    routerparams: any;

    //Data
    dataCart : DataCart = null;
    selectedData: TreeNode[] = [];
    dataFiles: TreeNode[] = [];
    zipData: ZipData[] = [];

    overallStatus: string = "";

    @ViewChild('bundler')
    bundler : BundleplanComponent;

    /**
     * Creates an instance of the SearchPanel
     *
     */
    constructor( 
        private route: ActivatedRoute,
        private router: Router,
        public cartService: CartService,
        @Inject(PLATFORM_ID) private platformId: Object ) 
    {
        this.inBrowser = isPlatformBrowser(platformId);
    }

    /**
     * Get the params OnInit
     */
    ngOnInit() {
        let currentUrl = this.router.url;

        this.routerparams = this.route.params.subscribe(params => {
            let cartName = params['cartname'];
            this.dataCart = this.cartService.getCart(cartName);
        });
    }

    /**
     * trigger download planning and display plan in the bundle-plan panel
     */
    downloadSelectedFiles(event) : void {
        if (this.bundler) 
            this.bundler.downloadSelectedFiles();
    }

    /**
     * remove the currently selected files from the data cart.  The child component displaying the 
     * cart contents will updated automatically because it is watching the cart for changes.
     */
    removeSelectedFiles(event) : void {
        this.dataCart.removeSelectedFiles();
    }

    /**
     * remove the currently selected files from the data cart.  The child component displaying the 
     * cart contents will updated automatically because it is watching the cart for changes.
     */
    remvoeDownloadedFiles(event) : void {
        this.dataCart.removeDownloadedFiles();
    }

    /**
     * receive the current overall download status of the cart
     */
    updateCartOperationalStatus(status : string) : void {
        this.overallStatus = status;
    }
    
    /* Control closing of this cart prematurely */

    /**
     * return true if the user should not close this tab/window because downloading is currently in progress.
     * This is used by LeaveWhileDownloadingGuard which is configured as part of the DataCartModule.
     */
    public canDeactivate() : boolean {
        return (this.overallStatus != DownloadStatus.DOWNLOADING);
    }

    /*
    @HostListener('window:beforeunload', ['$event'])
    unloadNotification($event: any) {
        if (! this.canDeactivate()) $event.returnValue = true;
    }
    */


    /******************************************/

    /**

    /**
     * Update zipData from the output of bundlePlan component
     * @param zipData zipDta from bundlePlan component
     */
    updateZipData(zipData: ZipData[]){
        this.zipData = zipData;
    }

    /**
     * Update overall download status from bundle download
     * @param overallStatus 
     */
    updateOverallStatus(overallStatus: string){
        this.overallStatus = overallStatus;
    }
}

