import { Component, OnInit, PLATFORM_ID, Inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import 'rxjs/add/operator/map';
import { TreeNode } from 'primeng/primeng';
import { CartConstants } from './cartconstants';
import { ZipData } from '../shared/download-service/zipData';
import { isPlatformBrowser } from '@angular/common';

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
    ediid: string;
    selectedData: TreeNode[] = [];
    dataFiles: TreeNode[] = [];
    CART_CONSTANTS: any;
    zipData: ZipData[] = [];

    /**
     * Creates an instance of the SearchPanel
     *
     */
    constructor( 
        private route: ActivatedRoute,
        @Inject(PLATFORM_ID) private platformId: Object ) 
    {
        this.CART_CONSTANTS = CartConstants.cartConst;
        this.inBrowser = isPlatformBrowser(platformId);
    }

    /**
     * Get the params OnInit
     */
    ngOnInit() {
        this.routerparams = this.route.params.subscribe(params => {
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
        this.zipData = zipData;
    }
}

