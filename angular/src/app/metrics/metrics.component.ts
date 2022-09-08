import { Component, OnInit, ViewChild, Inject, PLATFORM_ID, HostListener, ElementRef } from '@angular/core';
import { userInfo } from 'os';
import { CommonFunctionService } from '../shared/common-function/common-function.service';
import { ActivatedRoute } from '@angular/router';
import { MetricsService } from '../shared/metrics-service/metrics.service';
import { AppConfig } from '../config/config';
import { TreeNode } from 'primeng/api';
import { saveAs } from 'file-saver-es';
import { RecordLevelMetrics } from './metrics';
import { DatePipe } from '@angular/common';
import { HorizontalBarchartComponent } from './horizontal-barchart/horizontal-barchart.component';
import { SearchService } from '../shared/search-service/search-service.service';
import { isPlatformBrowser } from '@angular/common';
import { NerdmRes } from '../nerdm/nerdm';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';
import { HttpEventType } from '@angular/common/http';

const MOBIL_LABEL_LIMIT = 20;
const DESKTOP_LABEL_LIMIT = 50;

@Component({
    selector: 'app-metrics',
    templateUrl: './metrics.component.html',
    styleUrls: ['./metrics.component.css', '../landing/landing.component.css']
})
export class MetricsComponent implements OnInit {

    imageURL: string = 'assets/images/sdp-background.jpg';
    inBrowser: boolean = false;
    lps: string;
    pdrHomeUrl: string = "";

    // Data
    ediid: string;
    files: TreeNode[] = [];
    fileLevelData: any;
    firstTimeLogged: string = '';
    datasetTitle: string = '';
    datasetSubtitle: string = '';
    lastDownloadDate: string = "";
    filescount: number = 0;
    record: NerdmRes = null;
    metricsData: any[] = [];
    totalFileLevelSuccessfulGet: number = 0;
    totalFileSize: number = 0;
    totalFilesinChart: number = 0;
    noDatasetSummary: boolean = false;

    // Chart
    chartData: Array<any>;
    xAxisLabel: string = "";
    yAxisLabel: string = "";
    recordLevelTotalDownloads: number = 0;
    visible: boolean = true;
    cols: any[] = [];
    fontSize: string = '16px';  // Default font size
    noChartData: boolean = false;

    //Display
    screenSizeBreakPoint: number;
    screenWidth: number = 1080;
    mobileWidth: number = 500;
    maxLabelLength = 50;
    readyDisplay: boolean = false;

    // File tree
    isExpanded: boolean = false;

    // Error handling
    hasError: boolean = false;
    errorMsg: string = "";
    emailSubject: string = "";
    emailBody: string = "";

    recordLevelData : RecordLevelMetrics;
        
    // injected as ViewChilds so that this class can send messages to it with a synchronous method call.
    @ViewChild(HorizontalBarchartComponent)
    private barchart: HorizontalBarchartComponent;

    @ViewChild('panel0', { read: ElementRef }) public panel0: ElementRef<any>;

    constructor(
        private route: ActivatedRoute,
        private cfg: AppConfig,
        @Inject(PLATFORM_ID) private platformId: Object,
        public commonFunctionService: CommonFunctionService,
        private datePipe: DatePipe,
        private searchService: SearchService,
        public gaService: GoogleAnalyticsService,
        public metricsService: MetricsService) { 

            this.inBrowser = isPlatformBrowser(platformId);
            this.screenSizeBreakPoint = +this.cfg.get("screenSizeBreakPoint", "1060");
        }

    ngOnInit() {
        this.lps = this.cfg.get("locations.landingPageService", "/od/id/");

        this.detectScreenSize();
        this.recordLevelData = new RecordLevelMetrics();

        this.cols = [
            { field: 'name', header: 'Name', width: '60%' },
            { field: 'success_get', header: 'Downloads', width: '20%' },
            { field: 'download_size', header: 'File Size', width: '20%' }];

        // Expend the data tree to level one
        this.yAxisLabel = "";

        if(this.inBrowser){
            this.route.params.subscribe(queryParams => {
                this.ediid = queryParams.id;
                this.pdrHomeUrl = this.lps + this.ediid;
                // Get dataset title
                this.searchService.searchById(this.ediid, true).subscribe(md => {
                    if(md) {
                        this.record = md as NerdmRes;
                        this.datasetTitle = md['title'];

                        this.createNewDataHierarchy();
                        if (this.files.length != 0){
                            this.files = <TreeNode[]>this.files[0].data;

                            // Get file level metrics data
                            this.metricsService.getFileLevelMetrics(this.ediid).subscribe(async (event) => {
                                // Some large dataset might take a while to download. Only handle the response
                                // when it finishes downloading
                                if(event.type == HttpEventType.Response){
                                    let response = await event.body.text();
                                    this.fileLevelData = JSON.parse(response);

                                    if(this.fileLevelData.FilesMetrics != undefined && this.fileLevelData.FilesMetrics.length > 0){
                                        this.totalFileLevelSuccessfulGet = 0;
                                        this.totalFilesinChart = 0;
                                        this.cleanupFileLevelData(this.files);
                                        this.fileLevelData.FilesMetrics = this.metricsData;
                                        this.handleSum(this.files);

                                        if(this.fileLevelData.FilesMetrics.length > 0){
                                            this.noChartData = false;
                                            this.createChartData();
                                            this.lastDownloadDate = this.getLastDownloadDate()
                                        }else{
                                            this.noChartData = true;
                                        }
                                    }else{
                                        this.noChartData = true;
                                    }
                                }
                            },
                            (err) => {
                                let dateTime = new Date();
                                console.log("err", err);
                                this.errorMsg = JSON.stringify(err);
                                this.hasError = true;
                                console.log('this.hasError', this.hasError);
                                this.emailSubject = 'PDR: Error getting file level metrics data';
                                this.emailBody =
                                    'The information below describes an error that occurred while downloading metrics data.' + '%0D%0A%0D%0A'
                                    + '[From the PDR Team:  feel free to add additional information about the failure or your questions here.  Thanks for sending this message!]' + '%0D%0A%0D%0A'
                                    + 'ediid:' + this.ediid + '%0D%0A'
                                    + 'Time: ' + dateTime.toString() + '%0D%0A%0D%0A'
                                    + 'Error message:%0D%0A' + JSON.stringify(err);
            
                                this.readyDisplay = true;
                            });                            
                        }else{
                            this.noChartData = true;
                        }

                        this.readyDisplay = true;
                        this.expandToLevel(this.files, true, 0, 1);
                    }
                })

                // Get record level metrics data
                this.metricsService.getRecordLevelMetrics(this.ediid).subscribe(async (event) => {
                    switch (event.type) {
                        case HttpEventType.Response:
                            // this.recordLevelData = JSON.parse(JSON.stringify(event.body));
                            this.recordLevelData = JSON.parse(await event.body.text());

                            if(this.recordLevelData.DataSetMetrics != undefined && this.recordLevelData.DataSetMetrics.length > 0){
                                this.firstTimeLogged = this.datePipe.transform(this.recordLevelData.DataSetMetrics[0].first_time_logged, "MMM d, y");

                                this.recordLevelTotalDownloads = this.recordLevelData.DataSetMetrics[0].success_get;

                                // this.xAxisLabel = "Total Downloads Since " + this.firstTimeLogged;
                                this.datasetSubtitle = "Metrics Since " + this.firstTimeLogged;
                                this.noDatasetSummary = false;
                            }else{
                                this.noDatasetSummary = true;
                            }

                            break;
                        default:
                            break;
                    }

                },
                (err) => {
                    let dateTime = new Date();
                    console.log("err", err);
                    this.errorMsg = JSON.stringify(err);
                    this.hasError = true;
                    console.log('this.hasError', this.hasError);

                    this.emailSubject = 'PDR: Error getting file level metrics data';
                    this.emailBody =
                        'The information below describes an error that occurred while downloading metrics data.' + '%0D%0A%0D%0A'
                        + '[From the PDR Team:  feel free to add additional information about the failure or your questions here.  Thanks for sending this message!]' + '%0D%0A%0D%0A'
                        + 'ediid:' + this.ediid + '%0D%0A'
                        + 'Time: ' + dateTime.toString() + '%0D%0A%0D%0A'
                        + 'Error message:%0D%0A' + JSON.stringify(err);

                    this.readyDisplay = true;
                });
            });
        }
    }

    /**
     *  Following functions detect screen size
     */
    @HostListener("window:resize", [])
        public onResize() {
            this.detectScreenSize();
    }
    
    public ngAfterViewInit() {
        this.detectScreenSize();
    }

    private detectScreenSize() {
        setTimeout(() => {
            if(this.inBrowser){
                this.screenWidth = window.innerWidth;
                if(this.screenWidth < 550){
                    this.maxLabelLength = MOBIL_LABEL_LIMIT;
                }else{
                    this.maxLabelLength = DESKTOP_LABEL_LIMIT;
                }
            }
        }, 0);
    }

    /**
     * Remove outdated data and sha files from the metrics
     */
    cleanupFileLevelData(files: TreeNode[]){
        let metricsData: any[] = [];

        for(let node of files){
            let found = this.fileLevelData.FilesMetrics.find(x => x.filepath.substr(x.filepath.indexOf(this.ediid)+this.ediid.length).trim() == node.data.filePath.trim() && !x.filepath.endsWith('sha256'));
            if(found){
                metricsData.push(found);
                node.data.success_get = found.success_get;
                if(!node.data.download_size || node.data.download_size == 0){
                    node.data.download_size = found.download_size;
                }

                this.totalFileLevelSuccessfulGet += found.success_get;
                this.totalFilesinChart += 1;

                node.data.inChart = true;
                if(node.parent){
                    node.parent.data.inChart = true;
                }
            }

            if(node.children.length > 0){
                this.cleanupFileLevelData(node.children);
            }else{
                this.filescount = this.filescount + 1;
            }
        }

        // Append to existing metrics data - for some reason Object.assign did not work properly
        // Had to append metricsData elements one by one!
        // this.metricsData = Object.assign(JSON.parse(JSON.stringify(metricsData)), this.metricsData);
        for(let k=0; k < metricsData.length; k++)
            this.metricsData.push(metricsData[k]);
    }

    /**
     * Sum each folder in the file tree
     * @param files 
     */
    handleSum(files: TreeNode[]){
        this.totalFileSize = 0;
        files.forEach(child => {
            const {downloads, fileSize} = this.sumFolder(child);
            this.totalFileSize += fileSize;
        })
    }

    /**
     * Recursive call to sum each folder
     * @param node 
     * @returns 
     */
    sumFolder(node: TreeNode){
        if (node.children.length > 0) {
            node.children.forEach(child => {
                const {downloads, fileSize} = this.sumFolder(child);              
                node.data.success_get += downloads;
                node.data.download_size += fileSize;
            });
        }
    
        var downloads = node.data.success_get;
        var fileSize = node.data.download_size;
        return {downloads, fileSize};
    }

    /**
     * Save metrics data in csv format
     */
    saveMetrics() {
        if(!this.fileLevelData || this.fileLevelData.FilesMetrics == undefined){
            // Need to display message in the future
            return;
        }
        // Make a deep copy of the metrics data
        let fileMetrics = JSON.parse(JSON.stringify(this.fileLevelData.FilesMetrics));
        // Remove the ediid column
        for(let i in fileMetrics) {
            delete fileMetrics[i].ediid;
         }

        // convert JSON to CSV
        const replacer = (key, value) => value === null ? '' : value // specify how you want to handle null values here
        const header = Object.keys(fileMetrics[0])
        let csv = fileMetrics.map(row => header.map(fieldName => 
        JSON.stringify(row[fieldName], replacer)).join(','))
        csv.unshift(header.join(','))
        csv = csv.join('\r\n')

        if(this.recordLevelTotalDownloads == null || this.recordLevelTotalDownloads == undefined)
            this.recordLevelTotalDownloads = 0;

        // Add summary
        csv = "# Record id," + this.ediid + "\r\n"
            + "# Total file downloads," + this.recordLevelTotalDownloads + "\r\n"
            + "# Total dataset downloads," + this.TotalDatasetDownloads + "\r\n"
            + "# Total bytes downloaded," + this.totalDownloadSizeInByte + "\r\n"
            + "# Total unique users," + this.TotalUniqueUsers + "\r\n"
            + "\r\n" + csv;

        // Create link and download
        var link = document.createElement('a');
        link.setAttribute('href', 'data:text/csv;charset=utf-8,%EF%BB%BF' + encodeURIComponent(csv));
        link.setAttribute('download', this.ediid + '.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    /**
     * Return total dataset downloads
     */
    get TotalDatasetDownloads() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.recordLevelData.DataSetMetrics[0].record_download;
        }else{
            return ""
        }
    }

    /**
     * Return total download size from file level summary
     */
    get TotalFileSize() {
        return this.commonFunctionService.formatBytes(this.totalFileSize, 2);
    }

    /**
     * Get total unique users
     */
    get TotalUniqueUsers() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.recordLevelData.DataSetMetrics[0].number_users;
        }else{
            return ""
        }
    }

    /**
     * Save the bar chart as a png file
     */
    saveMetricsAsImage() {
        this.barchart.saveMetricsAsImage(this.datasetTitle + ".jpg");
    }
    
    /**
     * Convert input data into chart data format and calculate recordLevelTotalDownloads
     */
    createChartData() {
        if(!this.fileLevelData) return;

        this.chartData = [];

        let filename;
        let filenameDisp;
        let filenameWithPath;
        let filenameWithPathDisp;
        let nameList: string[] = [];
        let dupFileNames: string[] = [];

        // Find all duplicate file names if any
        for(let j = 0; j < this.fileLevelData.FilesMetrics.length; j++){
            // Get file name from path
            if(this.fileLevelData.FilesMetrics[j].filepath){
                filename = this.fileLevelData.FilesMetrics[j].filepath.replace(/^.*[\\\/]/, '');
                filename = decodeURI(filename).replace(/^.*[\\\/]/, '');
                if(nameList.find(x => x == filename)){
                    if(!dupFileNames.find(x => x == filename))
                        dupFileNames.push(filename);
                }else{
                    nameList.push(filename);
                }
            }
        }

        // Populate chartData. For dup file names, use full path without ediid.
        // Handle long file name: to make it simple, if file name is longer than max label length
        // (laptop and mobile are different), we will truncate the begining characters 
        // and add a sequence number at the end and put it in the first column (for display
        // purpose). The real file name with path saved in the 3rd column. 
        // The real file name saved in the 4th column. 

        let filenameSq: number = 1;
        let filenameWithPathSq: number = 1;

        for(let i = 0; i < this.fileLevelData.FilesMetrics.length; i++){
            // Get file name from path
            if(this.fileLevelData.FilesMetrics[i].filepath){


                filename = this.fileLevelData.FilesMetrics[i].filepath.replace(/^.*[\\\/]/, '');
                filename = decodeURI(filename).replace(/^.*[\\\/]/, '');
                filename = filename.replace(new RegExp('%20', 'g'), " ").trim();
                filenameDisp = filename;

                if(filename.length > this.maxLabelLength) {
                    filenameDisp = "..." + filename.substr(filename.length - this.maxLabelLength);
                }

                filenameWithPath = this.fileLevelData.FilesMetrics[i].filepath.substr(this.fileLevelData.FilesMetrics[i].filepath.indexOf(this.ediid)+this.ediid.length+1);
                filenameWithPath = decodeURI(filenameWithPath);
                filenameWithPath = '/' + filenameWithPath.replace(new RegExp('%20', 'g'), " ").trim();
                filenameWithPathDisp = filenameWithPath;

                if(filenameWithPath.length > this.maxLabelLength) {
                    filenameWithPathDisp = "..." + filenameWithPath.substr(filenameWithPath.length - this.maxLabelLength);
                }

                // Discard blank file name and handle duplicates
                let data = [];
                if(filename != "" && filenameWithPath != ""){
                    // First, check if any dup real name
                    var value = Math.floor(this.fileLevelData.FilesMetrics[i].success_get);
                    if(dupFileNames.find(x => x == filename)){
                        if(!this.chartData.find(e => e[2] == filenameWithPath)){
                            data = [filenameWithPathDisp, value, filenameWithPath, filename];
                        }
                    }else{
                        data = [filenameDisp, value, filenameWithPath, filename];
                    }

                    // Second, check if any dup display name
                    if(this.chartData.find(e => e[0] == filenameDisp)){
                        data = [filenameDisp + "_" + filenameSq.toString(), value, filenameWithPath, filename];

                        filenameSq++;
                    }

                    if(this.chartData.find(e => e[0] == filenameWithPathDisp)){
                        data = [filenameWithPathDisp + "_" + filenameWithPathSq.toString(), value, filenameWithPath, filename];

                        filenameWithPathSq++;
                    }

                    this.chartData.push(data);
                }
            }
        }

        // var sum = this.chartData.reduce((sum, current) => sum + current[1], 0);
        // this.recordLevelTotalDownloads = sum;
    }

    /**
     * Get the last download date (file level)
     * @returns last download date
     */
    getLastDownloadDate(){
        if (this.fileLevelData.FilesMetrics.length) {
            var lastDownloadTime = this.fileLevelData.FilesMetrics.reduce((m,v,i) => (v.timestamp > m.timestamp) && i ? v : m).timestamp;

            return this.datePipe.transform(this.fileLevelData.FilesMetrics.reduce((m,v,i) => (v.timestamp > m.timestamp) && i ? v : m).timestamp, "MMM d, y");
        }
    }

    /**
     * Get total recordset level download size
     */
    get totalDownloadSize() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.commonFunctionService.formatBytes(this.recordLevelData.DataSetMetrics[0].total_size, 2);
        }else{
            return ""
        }
    }

    /**
     * Get total recordset level download size in bytes
     */
    get totalDownloadSizeInByte() {
        if(this.recordLevelData.DataSetMetrics[0] != undefined){
            return this.recordLevelData.DataSetMetrics[0].total_size;
        }else{
            return ""
        }
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
        return { 'width': this.cols[1].width, 'font-size': this.fontSize, "text-align": "right" };
    }

    /**
     * Reture style for Totle Downloads column of the file tree
     * @returns 
     */
    totalDownloadsStyle() {
        return { 'width': this.cols[2].width, 'font-size': this.fontSize, "text-align": "right", "padding-right":"3em" };
    }

    /**
     * Function to expand tree display to certain level
     * @param dataFiles - file tree
     * @param expanded - expand flag 
     * @param currentLevel - current level
     * @param targetLevel - the level to expand to. Null - expand all level
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
                if (dataFiles[i].children && dataFiles[i].children.length > 0 && nextLevel < targetLevel) {
                    this.expandAll(dataFiles[i].children, expanded, nextLevel, targetLevel);
                }
            } else {
                if (dataFiles[i].children && dataFiles[i].children.length > 0) {
                    this.expandAll(dataFiles[i].children, expanded, nextLevel, targetLevel);
                }
            }
        }
    }

    /**
     * Create file tree from Nerdm record
     */
    createNewDataHierarchy() {
        var testdata: TreeNode = {}
        if (this.record['components'] != null) {
            testdata["data"] = this.arrangeIntoTree(this.record['components']);
            this.files.push(testdata);
        }
    }

    /**
     * Create a tree structure from a Nerdm component
     * @param paths 
     * @returns 
     */
    private arrangeIntoTree(paths) {
        const tree: TreeNode[] = [];
        // This example uses the underscore.js library.
        var i = 1;
        var tempfiletest = "";

        paths.forEach((path) => {
            //Remove hidden type files and sha files 
            if (path.filepath && !path['@type'].includes('nrd:Hidden') && !path.filepath.endsWith('sha256')) {
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

                        let newPart: TreeNode = null;
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
                                success_get: 0,
                                download_size: path.size? path.size: 0,
                                isLeaf: false,
                                inChart: false,
                                bkcolor: "white"
                            }, children: []
                        };
                        currentLevel.push(newPart);
                        currentLevel = newPart.children;
                    }
                });
            }
            i = i + 1;
        });
        return tree;
    }

    /**
     * Set raw back color based on node attributes
     * @param rowNode 
     * @returns 
     */
    rowColor(rowNode){
        if(rowNode.node.data.bkcolor != "white"){
            return rowNode.node.data.bkcolor;
        }else if(rowNode.node.children.length > 0){
            return "#c2eeff";
        }else if(rowNode.node.data.inChart){
            return "#e6ffe6";
        }else{
            return "white";
        }
    }

    /**
     * Return table column header text align style
     * The name column needs be left justified. Other columns need be right justified.
     * @param index Column index
     * @returns text align style
     */
    getTableHearderTextAlign(index){
        if(index == 0) return "left";
        else return "right";
    }

    /**
     * Return table column heaser padding style
     * The right most column need 3em padding
     * @param index Column index
     * @returns padding style
     */
    getTableHearderPadding(index){
        if(index == 2) return "3em";
        else return "0em";
    }
}
