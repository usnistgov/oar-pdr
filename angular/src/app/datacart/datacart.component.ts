import { Component, OnInit, PLATFORM_ID, Inject, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import 'rxjs/add/operator/map';
import { TreeNode } from 'primeng/primeng';
import { CartConstants } from './cartconstants';
import { ZipData } from '../shared/download-service/zipData';
import { isPlatformBrowser } from '@angular/common';
import { FormCanDeactivate } from '..//form-can-deactivate/form-can-deactivate';
import { CartService } from '../datacart/cart.service';

@Component({
    moduleId: module.id,
    selector: 'data-cart',
    templateUrl: 'datacart.component.html',
    styleUrls: ['datacart.component.css'],
})

export class DatacartComponent extends FormCanDeactivate implements OnInit {
    inBrowser: boolean = false;

    //Connection
    routerparams: any;

    //Data
    ediid: string;
    selectedData: TreeNode[] = [];
    dataFiles: TreeNode[] = [];
    CART_CONSTANTS: any;
    zipData: ZipData[] = [];

    // overallStatus is used in can-deactivate component. If overallStatus is not 'completed'
    // and user tried to close the tab, a warning dialog will pop up.
    @ViewChild('overallStatus')
    overallStatus: string = "";

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
        super(cartService);

        this.CART_CONSTANTS = CartConstants.cartConst;
        this.inBrowser = isPlatformBrowser(platformId);
    }

    /**
     * Get the params OnInit
     */
    ngOnInit() {
        let currentUrl = this.router.url;

        this.routerparams = this.route.params.subscribe(params => {
            if(currentUrl.indexOf("ark:/88434") >= 0)
                this.ediid = 'ark:/88434/' + params['ediid'];
            else
                this.ediid = params['ediid'];
        })
    }

    /**
     * Update selectedData from the output of treeTable component
     * @param selectedData Selected data array from treeTable component
     */
    updateSelectedData(selectedData){
        this.selectedData = selectedData;
    }

    /**
     * Update dataFiles from the output of treeTable component
     * @param dataFiles dataFiles from treeTable component
     */
    updateDafaFiles(dataFiles){
        this.dataFiles = dataFiles;
    }

    /**
     * Update zipData from the output of bundlePlan component
     * @param zipData zipDta from bundlePlan component
     */
    updateZipDafa(zipData: ZipData[]){
        console.log("Updating zipData...");
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

