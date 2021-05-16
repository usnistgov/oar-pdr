import { Component, OnInit, ViewChild, Inject, PLATFORM_ID } from '@angular/core';
import { userInfo } from 'os';
import { CommonFunctionService } from '../shared/common-function/common-function.service';
import { ActivatedRoute } from '@angular/router';
import { MetricsService } from '../shared/metrics-service/metrics.service';
import { AppConfig } from '../config/config';
import { TreeNode } from 'primeng/api';
import { saveAs } from 'file-saver';
import { RecordLevelMetrics } from './metrics';
import { DatePipe } from '@angular/common';
import { HorizontalBarchartComponent } from './horizontal-barchart/horizontal-barchart.component';
import { SearchService } from '../shared/search-service/search-service.service';
import { isPlatformBrowser } from '@angular/common';

@Component({
    selector: 'app-metrics',
    templateUrl: './metrics.component.html',
    styleUrls: ['./metrics.component.css', '../landing/landing.component.css']
})
export class MetricsComponent implements OnInit {

    imageURL: string = 'assets/images/sdp-background.jpg';
    inBrowser: boolean = false;

    // Data
    ediid: string;
    files: any[] = [];
    fileLevelData: any;
    firstTimeLogged: string = '';
    datasetTitle: string = '';
    lastDownloadDate: string = "";

    // Chart
    chartData: Array<any>;
    chart_title: string;
    xAxisLabel: string = "";
    yAxisLabel: string = "";
    recordLevelTotalDownloads: number = 0;
    visible: boolean = true;
    cols: any[] = [];
    fontSize: string = '16px';  // Default font size
    noChartData: boolean = true;

    // File tree
    isExpanded: boolean = false;

    recordLevelData : RecordLevelMetrics;
        
    // injected as ViewChilds so that this class can send messages to it with a synchronous method call.
    @ViewChild(HorizontalBarchartComponent)
    private barchart: HorizontalBarchartComponent;

    constructor(
        private route: ActivatedRoute,
        @Inject(PLATFORM_ID) private platformId: Object,
        public commonFunctionService: CommonFunctionService,
        private datePipe: DatePipe,
        private searchService: SearchService,
        public metricsService: MetricsService) { 

            this.inBrowser = isPlatformBrowser(platformId);
        }

    ngOnInit() {
        this.recordLevelData = new RecordLevelMetrics();

        this.cols = [
            { field: 'name', header: 'Name', width: '60%' },
            { field: 'success_get', header: 'Downloads', width: '20%' },
            { field: 'download_size', header: 'Total Bytes Downloaded', width: '20%' }];

        // Expend the data tree to level one
        this.chart_title = "File Level Details";
        this.yAxisLabel = "";

        if(this.inBrowser){
            this.route.params.subscribe(queryParams => {
                this.ediid = queryParams.id;
                // Get dataset title
                this.searchService.searchById(this.ediid).subscribe(md => {
                    if(md) {
                        this.datasetTitle = md['title'];
                    }
                })

                this.metricsService.getRecordLevelMetrics(this.ediid).subscribe(metricsData => {
                    console.log('metricsData', metricsData);
                    this.recordLevelData = JSON.parse(JSON.stringify(metricsData));
                    if(this.recordLevelData.DataSetMetrics != undefined && this.recordLevelData.DataSetMetrics.length > 0){
                        this.firstTimeLogged = this.datePipe.transform(this.recordLevelData.DataSetMetrics[0].first_time_logged, "MMM d, y")

                        this.xAxisLabel = "Total Downloads Since " + this.firstTimeLogged;
                    }
                });

                this.metricsService.getDatasetMetrics(this.ediid).subscribe(metricsData => {
                    console.log('fileLevelData', metricsData);
                    this.fileLevelData = metricsData;
                    if(this.fileLevelData.FilesMetrics != undefined && this.fileLevelData.FilesMetrics.length > 0){
                        this.noChartData = false;
                        this.createChartData();
                        this.lastDownloadDate = this.getLastDownloadDate()
                        this.files = JSON.parse(JSON.stringify(this.createTreeFromPaths(this.fileLevelData.FilesMetrics)));
                        this.expandToLevel(this.files, true, 0, 1);
                    }else{
                        this.noChartData = true;
                    }

                });
            });
        }
    }

    /**
     * Save metrics data in json format
     */
    saveMetrics() {
        if(this.inBrowser){
            // convert JSON to CSV
            const replacer = (key, value) => value === null ? '' : value // specify how you want to handle null values here
            const header = Object.keys(this.fileLevelData.FilesMetrics[0])
            let csv = this.fileLevelData.FilesMetrics.map(row => header.map(fieldName => 
            JSON.stringify(row[fieldName], replacer)).join(','))
            csv.unshift(header.join(','))
            csv = csv.join('\r\n')

            // Add summary
            csv = "# Record id," + this.ediid
                + "# Total file downloads," + this.recordLevelTotalDownloads + "\r\n"
                + "# Total dataset downloads," + this.TotalDatasetDownloads + "\r\n"
                + "# Total bytes downloaded," + this.totalDownloadSizeInByte + "\r\n"
                + "# Total unique users," + this.TotalUniqueUsers
                + "\r\n" + csv;

            console.log('csv', csv)

            // Create link and download
            var link = document.createElement('a');
            link.setAttribute('href', 'data:text/csv;charset=utf-8,%EF%BB%BF' + encodeURIComponent(csv));
            link.setAttribute('download', this.ediid + '.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    get TotalDatasetDownloads() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.recordLevelData.DataSetMetrics[0].success_get;
        }else{
            return ""
        }
    }

    get TotalUniqueUsers() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.recordLevelData.DataSetMetrics[0].number_users;
        }else{
            return ""
        }
    }

    saveMetricsAsImage() {
        this.barchart.saveMetricsAsImage();
    }
    
    /**
     * Convert input data into chart data format and calculate recordLevelTotalDownloads
     */
    createChartData() {
        this.chartData = [];

        let filename;
        let filenameWithPath;
        let nameList: string[] = [];
        let dupFileNames: string[] = [];

        // Find all duplicate file names if any
        for(let j = 0; j < this.fileLevelData.FilesMetrics.length; j++){
            // Get file name from path
            filename = this.fileLevelData.FilesMetrics[j].filepath.replace(/^.*[\\\/]/, '');
            filename = decodeURI(filename).replace(/^.*[\\\/]/, '');
            if(nameList.find(x => x == filename)){
                if(!dupFileNames.find(x => x == filename))
                    dupFileNames.push(filename);
            }else{
                nameList.push(filename);
            }
        }

        // Populate chartData. For dup file names, use full path without ediid.
        for(let i = 0; i < this.fileLevelData.FilesMetrics.length; i++){
            // Get file name from path
            filename = this.fileLevelData.FilesMetrics[i].filepath.replace(/^.*[\\\/]/, '');
            filename = decodeURI(filename).replace(/^.*[\\\/]/, '');

            filenameWithPath = this.fileLevelData.FilesMetrics[i].filepath.substr(this.fileLevelData.FilesMetrics[i].filepath.indexOf('/')+1);
            filenameWithPath = decodeURI(filenameWithPath);

            var value = Math.floor(this.fileLevelData.FilesMetrics[i].success_get);
            if(dupFileNames.find(x => x == filename)){
                this.chartData.push([filenameWithPath, value]);
            }else{
                this.chartData.push([filename, value]);
            }
        }

        var sum = this.chartData.reduce((sum, current) => sum + current[1], 0);
        this.recordLevelTotalDownloads = sum;
    }

    getLastDownloadDate(){
        if (this.fileLevelData.FilesMetrics.length) {
            var lastDownloadTime = this.fileLevelData.FilesMetrics.reduce((m,v,i) => (v.timestamp > m.timestamp) && i ? v : m).timestamp;
            console.log("lastDownloadTime", lastDownloadTime);

            return this.datePipe.transform(this.fileLevelData.FilesMetrics.reduce((m,v,i) => (v.timestamp > m.timestamp) && i ? v : m).timestamp, "MMM d, y");
        }
    }

    get totalDownloadSize() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.commonFunctionService.formatBytes(this.recordLevelData.DataSetMetrics[0].total_size, 2);
        }else{
            return ""
        }
    }

    get totalDownloadSizeInByte() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.recordLevelData.DataSetMetrics[0].total_size;
        }else{
            return ""
        }
    }

    /**
     * Create a tree structure from a given object array. The elements of the object array must contain 
     * "filepath" property.
     * @param paths Object array that contains "filepath" property
     * @returns tree object
     */
    createTreeFromPaths(paths: any[]) {
        const tree = [];
        let i = 1;
        let tempPaths = JSON.parse(JSON.stringify(paths));

        tempPaths.forEach((path) => {
            if (path.filepath) {
                if (!path.filepath.startsWith("/"))
                    path.filepath = "/" + path.filepath;

                // Remove ediis from filepath
                var cleanPath = path.filepath.replace(path.ediid + '/', '')

                var decodedPath = decodeURI(cleanPath).replace(/^.*[\\\/]/, '');

                const pathParts = cleanPath.split('/');
                pathParts.shift(); // Remove first blank element from the parts array.
                let currentLevel = tree; // initialize currentLevel to root
                let pathPartsLength = pathParts.length;
                let j: number = 0;  // Counter to decide if a node is leaf

                pathParts.forEach((part) => {
                    let isLeaf: boolean = false;
                    if(j == pathPartsLength-1){
                        isLeaf = true;
                    }

                    // check to see if the path already exists.
                    const existingPath = currentLevel.filter(level => level.data.name === part);
                    if (existingPath.length > 0) {

                        // The path to this item was already in the tree, so don't add it again.
                        // Set the current level to this path's children  
                        currentLevel = existingPath[0].children;
                    } else {
                        let newPart = null;
                        newPart = {
                            data: {
                                name: decodeURI(part).replace(/^.*[\\\/]/, ''),
                                filePath: decodedPath,
                                success_get: path.success_get,
                                download_size: path.download_size,
                                isLeaf: isLeaf
                            }, children: []
                        };
                        currentLevel.push(newPart);
                        currentLevel = newPart.children;
                    }

                    j++;
                });
            }
            i = i + 1;
        });
        return tree;
    }

    /**
     * Reture style for Title column of the file tree
     * @returns 
     */
    titleStyle() {
        return { 'width': this.cols[0].width, 'font-size': this.fontSize };
    }

    /**
     * Reture style for Success Get column of the file tree
     * @returns 
     */
    successGetStyle() {
        return { 'width': this.cols[1].width, 'font-size': this.fontSize };
    }

    /**
     * Reture style for Totle Downloads column of the file tree
     * @returns 
     */
    totalDownloadsStyle() {
        return { 'width': this.cols[2].width, 'font-size': this.fontSize };
    }

    /**
     * Function to expand tree display to certain level
     * @param dataFiles - file tree
     * @param expanded - expand flag 
     * @param currentLevel - current level
     * @param targetLevel - the level to expand to
     */
    expandToLevel(dataFiles: any, expanded: boolean, currentLevel:number = 0, targetLevel: any = null) {
        this.expandAll(dataFiles, expanded, currentLevel, targetLevel)

        this.isExpanded = expanded;
        this.visible = false;
        setTimeout(() => {
            this.visible = true;
        }, 0);
    }

    /**
     * Function to expand tree display to certain level - used by expandToLevel()
     * @param dataFiles - file tree
     * @param expanded 
     * @param currentLevel - current level
     * @param targetLevel - the level we want to expand
     */
    expandAll(dataFiles: TreeNode[], expanded: boolean, currentLevel: any = 0, targetLevel: any = 0) {
        let nextLevel = currentLevel + 1;
        for (let i = 0; i < dataFiles.length; i++) {
            dataFiles[i].expanded = expanded;
            if (targetLevel != null) {
                if (dataFiles[i].children.length > 0 && nextLevel < targetLevel) {
                    this.expandAll(dataFiles[i].children, expanded, nextLevel, targetLevel);
                }
            } else {
                if (dataFiles[i].children.length > 0) {
                    this.expandAll(dataFiles[i].children, expanded, nextLevel, targetLevel);
                }
            }
        }
    }
}
