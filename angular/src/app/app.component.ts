import { Component, AfterViewInit, OnInit } from '@angular/core';
import { Router, NavigationStart, NavigationEnd, NavigationCancel, NavigationError } from '@angular/router';
import './content/modal.less';
import { GoogleAnalyticsService } from './shared/ga-service/google-analytics.service'
import { AppConfig } from './config/config';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'PDR Resource Landing Page';
  gaCode: string;

  constructor(
    private gaService: GoogleAnalyticsService,
    private cfg: AppConfig,
  ) { 

  }

  ngOnInit() {
  }

  ngAfterViewInit(): void {
    //Called after ngAfterContentInit when the component's view has been initialized. Applies to components only.
    //Add 'implements AfterViewInit' to the class.
    // Add Google Analytics service
    this.gaCode = this.cfg.get("gaCode", "") as string;
    this.gaService.appendGaTrackingCode(this.gaCode);

    console.log('this.gaCode', this.gaCode);
  }
}

