import { Component, OnInit, OnChanges, Input, Output, SimpleChanges, EventEmitter } from '@angular/core';
import { NerdmRes } from '../../nerdm/nerdm';
import { RecordLevelMetrics } from '../../metrics/metrics';
import { CommonFunctionService } from '../../shared/common-function/common-function.service';
import { MenuItem } from 'primeng/api';
import { MetricsService } from '../../shared/metrics-service/metrics.service';
import { Observable, of, Observer } from "rxjs";
import { AppConfig } from '../../config/config';
import { CartActions } from '../../datacart/cartconstants';
import { MetricsData } from "../metrics-data";
import * as _ from 'lodash-es';
import { formatBytes } from '../../utils';

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
    @Input() metricsData : MetricsData;

    // flag if metrics is ready to display
    @Input() showMetrics : boolean = false;

    // flag if there is file level metrics data
    hasFileLevelMetrics: boolean = false;

    // Array to hold metrics info
    metricsInfo: string[] = [];
    metricsInfoOb: Observable<string[]>;

    fileLevelMetrics: any;
    recordLevelMetrics : RecordLevelMetrics;

    //Default: wait 5 minutes (300sec) after user download a file then refresh metrics data
    delayTimeForMetricsRefresh: number = 300; 
    time: any;

    constructor(
        public commonFunctionService: CommonFunctionService,
        public metricsService: MetricsService,
        private cfg: AppConfig
    ) { 
        this.delayTimeForMetricsRefresh = +this.cfg.get("delayTimeForMetricsRefresh", "300");
    }

    get totalUsers() {
        return this.metricsData.totalUsers > 1? this.metricsData.totalUsers.toString() + ' unique users': this.metricsData.totalUsers.toString() + ' unique user';
    }

    displayMetrics() {
        if(!this.metricsData.hasCurrentMetrics){
            this.metricsInfo = ['Metrics not available'];
        }

        this.showMetrics = true;
    }

    /**
     * Reture record level total download size
     */
    get totalDownloadSize() {
        if(this.metricsData != undefined)
            return formatBytes(this.metricsData.totalDownloadSize, 2);
        else
            return "";
    }
}
