import { Component, OnInit } from '@angular/core';
import { userInfo } from 'os';

@Component({
  selector: 'app-metrix',
  templateUrl: './metrix.component.html',
  styleUrls: ['./metrix.component.css']
})
export class MetrixComponent implements OnInit {

    imageURL = '/assets/images/sample-files.png';
    imgChart = 'assets/images/line-chart-yearly.png';
    chartTitle02 = "downloads";
    currentMonth: string = "";
    currentYear: string = "2021";
    category: string = "download";

    constructor() { }

    ngOnInit() {
    }

    loadTotalUser(e){
        this.currentMonth = "";
        this.chartTitle02 = "users";
        this.imgChart = 'assets/images/total-user-year.png';
    }

    loadTotalDownload(e){
        console.log("this.category", this.category);
        this.chartTitle02 = "downloads";
        this.imgChart = 'assets/images/line-chart-yearly.png';
    }

    changeYear(e) {
        this.currentYear = e.target.value;
        if(this.category == "user"){
            this.currentMonth = "";
            this.chartTitle02 = "users";
            this.imgChart = 'assets/images/total-user-year.png';
        }else{
            this.chartTitle02 = "downloads";
            this.currentMonth = "";
            this.imgChart = 'assets/images/line-chart-yearly.png';
        }
    }

    changeMonth(e) {
        this.currentMonth = e.target.value;
        if(this.category == "user"){
            this.currentMonth = "";
            this.chartTitle02 = "users";
            this.imgChart = 'assets/images/total-user-year.png';
        }else{
            this.chartTitle02 = "downloads";
            this.imgChart = 'assets/images/line-chart-month.png';
        }
    }
}
