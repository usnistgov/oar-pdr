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

  constructor(
    private gaService: GoogleAnalyticsService,
    private cfg: AppConfig,
  ) { }

  ngOnInit() {
  }
}

