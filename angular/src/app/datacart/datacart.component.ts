import { Component, OnInit, AfterViewInit, PLATFORM_ID, Inject, ViewChild, HostListener } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
// import 'rxjs/add/operator/map';
import { map } from 'rxjs/operators';
import { TreeNode } from 'primeng/api';
import { DownloadStatus } from './cartconstants';
import { ZipData } from '../shared/download-service/zipData';
import { isPlatformBrowser } from '@angular/common';
import { CartService } from './cart.service';
import { DataCart } from './cart';
import { BundleplanComponent } from './bundleplan/bundleplan.component';
import { switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import { throwError } from 'rxjs';


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
export class DatacartComponent implements OnInit, AfterViewInit {
    inBrowser: boolean = false;

    //Data
    dataCart : DataCart = null;
    zipData: ZipData[] = [];

    overallStatus: string = "";
    datacartName: string = "";
    forceReload: boolean = false;

    @ViewChild('bundler', { static: true })
    bundler : BundleplanComponent;

    // property to track if the cart loading was successful
    isCartLoadedSuccessfully: boolean = false;
    // property to hold the error message
    errorMessage: string = ''; 
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

        // this.isCartLoadedSuccessfully = false; Already initialized during declaration

        this.route.params.pipe(
            switchMap(params => {
                let cartName = params['cartname'];
                this.datacartName = cartName;
                // Attempt to get the cart; assuming getCart returns a cart object or null if unsuccessful
                const cart = this.cartService.getCart(cartName);
                if (cart) {
                    this.dataCart = cart;
                    this.isCartLoadedSuccessfully = true; // Set flag to true for successfully retrieved carts
                    // Check if it's an RPA cart and we're in the browser
                    if(cartName === 'rpa' && this.inBrowser) {
                        return this.route.queryParams.pipe(
                            switchMap(queryParams => {
                                let id = queryParams['id'];
                                return this.cartService.getRpaCart(id, cartName);
                            })
                        );
                    } else {
                        // For non-RPA carts or when not in browser, no further action needed
                        // Use of(null) to complete the Observable chain
                        return of(null);
                    }
                } else {
                    // Handle the case where the cart could not be retrieved
                    this.isCartLoadedSuccessfully = false;
                    return throwError(() => new Error("Cart could not be retrieved"));
                }
            })
        ).subscribe({
            next: (result: any) => {
              if (result) {
                // Only update the contents for RPA carts as the cart is already loaded successfully above
                if(this.datacartName === 'rpa') {
                    this.dataCart.contents = result.contents;
                    this.forceReload = true;
                    
                    setTimeout(() => {
                      this.dataCart.save();
                    }, 0);
                }
              }
            },
            error: (error: string) => {
              console.error("Error loading cart:", error);
              this.errorMessage = error; // Set the error message for display
              this.isCartLoadedSuccessfully = false;
            }
        });
    }

    /**
     * Get the params OnInit
     */
    ngOnInit(): void {
    }

    /**
     * initiate download if requested via URL query parameter.  (The download can't start
     * until after all the children are initiated.)
     */
    ngAfterViewInit() {
        // initiate the download if requested via a URL query parameter
        if (this.inBrowser) {
            this.route.queryParamMap.subscribe(queryParams => {
                var param = queryParams.get("downloadSelected");
                if(param && param.toLowerCase() == 'true')
                    this.downloadSelectedFiles(null);
            });
        }
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

    @HostListener('window:beforeunload', ['$event'])
    unloadNotification($event: any) {
        if (! this.canDeactivate()) 
            $event.preventDefault();
    }


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

