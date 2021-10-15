import { Component, OnInit, OnChanges, Input, SimpleChanges } from '@angular/core';
import { NerdmRes } from '../../nerdm/nerdm';
import { RecordLevelMetrics } from '../../metrics/metrics';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { MenuItem } from 'primeng/api';
import { MetricsService } from '../../shared/metrics-service/metrics.service';
import { HttpEventType } from '@angular/common/http';
import { Observable, of } from "rxjs";
import { DataCartStatus } from '../../datacart/cartstatus';
import { AppConfig } from '../../config/config';
import { CartActions } from '../../datacart/cartconstants';
import * as _ from 'lodash';

@Component({
  selector: 'app-metricsinfo',
  templateUrl: './metricsinfo.component.html',
  styleUrls: ['./metricsinfo.component.css']
})
export class MetricsinfoComponent {
    // the resource record metadata that the tool menu data is drawn from
    @Input() record : NerdmRes|null = null;

    // Record level metrics data
    // @Input() recordLevelMetrics : RecordLevelMetrics|null = new RecordLevelMetrics();

    @Input() inBrowser: boolean = false;

    // Record level metrics data
    @Input() metricsUrl : string|null = "";

    @Input() editEnabled: boolean = false;

    // flag if metrics is ready to display
    showMetrics : boolean = false;

    // flag if there is file level metrics data
    hasCurrentMetrics: boolean = false;

    hasMetrics: boolean = false;

    // Array to hold metrics info
    metricsInfo: string[] = [];
    metricsInfoOb: Observable<string[]>;

    fileLevelMetrics: any;
    recordLevelMetrics : RecordLevelMetrics;

    dataCartStatus: DataCartStatus;
    cartChangeHandler: any;

    //Default: wait 5 minutes (300sec) after user download a file then refresh metrics data
    delayTimeForMetricsRefresh: number = 300; 

    public CART_ACTIONS: CartActions;

    constructor(
        public commonFunctionService: CommonFunctionService,
        public metricsService: MetricsService,
        private cfg: AppConfig
    ) { 
        this.delayTimeForMetricsRefresh = +this.cfg.get("delayTimeForMetricsRefresh", "300");
    }

    ngOnInit(): void {
        this.CART_ACTIONS = CartActions.cartActions;
        this.dataCartStatus = DataCartStatus.openCartStatus();
        if(this.record){
            this.refreshMetrics(false);
        }
    }

    ngOnDestroy() {
        // window.removeEventListener("storage", this.cartChangeHandler);
    }

    /**
     * Refresh metrics data in N minutes. N is defined in environment.ts
     * @param delay if this is false, refresh immediately
     */
    refreshMetrics(delay:boolean = true){
        let delayTime;
        if(delay){
            console.log("Metrics will be refreshed in " + this.delayTimeForMetricsRefresh + " seconds.");
            delayTime = this.delayTimeForMetricsRefresh*1000;
        }else{
            delayTime = 0;
        }

        setTimeout(() => {
            this.getMetrics();
        }, delayTime);
    }

    /**
     * Get metrics data
     */
    getMetrics() {
        console.log("Retriving metrics data...");
        let ediid = this.record.ediid;

        // Get metrics when edit is not enabled. Otherwise display "Metrics not available"
        if(this.editEnabled) {
            this.hasCurrentMetrics = false;
            this.showMetrics = true;
            return;
        }

        this.metricsService.getFileLevelMetrics(ediid).subscribe(async (event) => {
            // Some large dataset might take a while to download. Only handle the response
            // when download is completed
            if(event.type == HttpEventType.Response){
                let response = await event.body.text();

                this.fileLevelMetrics = JSON.parse(response);

                if(this.fileLevelMetrics.FilesMetrics != undefined && this.fileLevelMetrics.FilesMetrics.length > 0){
                    // check if there is any current metrics data
                    for(let i = 1; i < this.record.components.length; i++){
                        let filepath = this.record.components[i].filepath;
                        if(filepath) filepath = filepath.trim();

                        this.hasCurrentMetrics = this.fileLevelMetrics.FilesMetrics.find(x => x.filepath.substr(x.filepath.indexOf(ediid)+ediid.length+1).trim() == filepath) != undefined;
                        if(this.hasCurrentMetrics) break;
                    }
                }else{
                    this.hasCurrentMetrics = false;
                }

                this.metricsService.getRecordLevelMetrics(ediid).subscribe(async (event) => {
                    if(event.type == HttpEventType.Response){
                        this.recordLevelMetrics = JSON.parse(await event.body.text());
                        this.updateMetrics();
                    }
                },
                (err) => {
                    console.error("Failed to retrieve dataset metrics: ", err);
                    this.showMetrics = true;
                });  
            }
        },
        (err) => {
            console.error("Failed to retrieve file metrics: ", err);
            this.showMetrics = true;
        });                    
    }
    
    /**
     * Update metrics data
     */
    updateMetrics() {
        var subitems : MenuItem[] = [];
        var hasMetrics: boolean = false;

        this.metricsInfo = [];
        // Dataset Metrics
        // First check if there is any file in the dataset. If not, do not display metrics.
        if(this.hasCurrentMetrics){
            let hasFile = false;
            if(this.record.components && this.record.components.length > 0){
                this.record.components.forEach(element => {
                    if(element.filepath){
                        hasFile = true;
                    }
                });
            }
            if(hasFile){
                //Now check if there is any metrics data
                let totalDatasetDownload = this.recordLevelMetrics.DataSetMetrics[0] != undefined? this.recordLevelMetrics.DataSetMetrics[0].record_download : 0;
    
                // totalFileDownload = totalFileDownload == undefined? 0 : totalFileDownload;
        
                let totalUsers = this.recordLevelMetrics.DataSetMetrics[0] != undefined? this.recordLevelMetrics.DataSetMetrics[0].number_users : 0;
        
                totalUsers = totalUsers == undefined? 0 : totalUsers;
        
                let totalDownloadSize = this.recordLevelMetrics.DataSetMetrics[0] != undefined?
                    this.commonFunctionService.formatBytes(this.recordLevelMetrics.DataSetMetrics[0].total_size, 2) : 0;
        
                if(this.recordLevelMetrics.DataSetMetrics.length > 0 && totalDatasetDownload > 0){

                    this.metricsInfo.push(totalDatasetDownload.toString() + ' dataset downloads');

                    this.metricsInfo.push(totalUsers > 1?totalUsers.toString() + ' unique users':totalUsers.toString() + ' unique user');
                    this.metricsInfo.push(totalDownloadSize.toString() + ' downloaded');
    
                    hasMetrics = true;
                }
            }

        }else{
            hasMetrics = false;
        }
        
        if(!hasMetrics){
            this.metricsInfo.push('Metrics not available');
        }
        this.showMetrics = false;
        setTimeout(() => { 
            this.showMetrics = true; 
        }, 0);

        this.metricsInfoOb = new Observable((observer) => {
            setTimeout(() => { observer.next(this.metricsInfo) }, 100);
        })
    }

}
