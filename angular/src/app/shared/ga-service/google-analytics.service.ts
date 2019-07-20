// Google Analytics (GA) script was handled differently from traditional web pages. Angular 2+ is a SPA
// which was considered only one page.
// But if a page is launched in a new tab, it was consider a new page and the GA script will be triggered.
// In PDR, we have only landing page and datacart page. Landing page open datacart page in a new tab. 
// So we don't need to fire gas() function here.

import { Injectable } from '@angular/core';
import {Router, NavigationEnd} from '@angular/router';
declare var gas:Function; 

@Injectable()
export class GoogleAnalyticsService {
  // constructor(router: Router) {
  //   router.events.subscribe(event => {
  //     if ((event instanceof NavigationEnd) && event.url != '/') {
  //       console.log("event", event);
  //       setTimeout(() => {
  //         gas('send', 'pageview', event.url, 'pageview');
  //       }, 1000);
  //     }
  //   })
  // }

}
