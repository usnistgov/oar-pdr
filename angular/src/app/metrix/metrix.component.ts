import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-metrix',
  templateUrl: './metrix.component.html',
  styleUrls: ['./metrix.component.css']
})
export class MetrixComponent implements OnInit {

    imageURL = '/assets/images/sample-files.png';
    imgChart = 'assets/images/line-chart-yearly.png';
    chartTitle02 = "Total Downloads in the Past Year"

    constructor() { }

    ngOnInit() {
    }

    loadTotalUser(){
        this.chartTitle02 = "Total Users in the Past Year"
        this.imgChart = 'assets/images/total-user-year.png';
    }

    loadTotalDownload(){
        this.chartTitle02 = "Total Downloads in the Past Year"
        this.imgChart = 'assets/images/line-chart-yearly.png';
    }

    loadTotalDownloadYear(){
        this.chartTitle02 = "Total Downloads in the Past Year"
        this.imgChart = 'assets/images/line-chart-yearly.png';
    }

    loadTotalDownloadMonth(){
        this.chartTitle02 = "Total Downloads in Month..."
        this.imgChart = 'assets/images/line-chart-month.png';
    }
}
