import { Component, AfterViewInit, OnInit } from '@angular/core';
import { CommonVarService } from './shared/common-var';
import { Router, NavigationStart, NavigationEnd, NavigationCancel, NavigationError } from '@angular/router';
import './content/modal.less';
import { AuthService } from './shared/auth-service/auth.service';
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
    private authService: AuthService,
    private gaService: GoogleAnalyticsService,
    private cfg: AppConfig,
  ) { }

  ngOnInit() {
    // for testing purpose, logout user everytime the app starts
//     if (this.authService.loggedIn())
//       this.authService.logoutUser(true);
  }
}

