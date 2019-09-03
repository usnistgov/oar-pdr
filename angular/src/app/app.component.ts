import { Component, AfterViewInit, OnInit } from '@angular/core';
import { CommonVarService } from './shared/common-var';
import { Router, NavigationStart, NavigationEnd, NavigationCancel, NavigationError } from '@angular/router';
import './content/modal.less';
import { AuthService } from './shared/auth-service/auth.service';
import { GoogleAnalyticsService } from './shared/ga-service/google-analytics.service'

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'PDR Resource Landing Page';

  constructor(
    private authService : AuthService,
    private gaService: GoogleAnalyticsService
    ){}

  ngOnInit() {
    // for testing purpose, logout user everytime the app starts
    if(this.authService.loggedIn())
      this.authService.logoutUser(true);

      this.gaService.appendGaTrackingCode();
  }
}

/* 
 * if SSR is working, this version, which enables a "loading" spinner,
 * should not be necessary
 *
export class AppComponent implements AfterViewInit, OnInit {
  element: HTMLElement;

  constructor(private commonVarService: CommonVarService,
    private router: Router) {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationStart) {
        this.element.hidden = false;
      } else if (event instanceof NavigationEnd || event instanceof NavigationCancel || event instanceof NavigationError) {
        // this.element.hidden = true;
        // console.log("Spinner is not visible.");
      }
    }, () => {
      this.element.hidden = true;
    });
  }

  /**
   * Get the params OnInit
   *
  ngOnInit() {
    this.element = document.getElementById('loadspinner') as HTMLElement;
    this.element.hidden = false;
    setTimeout(() => {
      this.element.hidden = true;
    }, 15000);
  }

  ngAfterViewInit() {
    setTimeout(() => {
      this.commonVarService.watchContentReady().subscribe(
        value => {
          // let element: HTMLElement = document.getElementById('loadspinner') as HTMLElement;
          this.element.hidden = value;
          setTimeout(() => {
            this.element.hidden = true;
          }, 10000);
        }
      );
    });
  }
}
*/
