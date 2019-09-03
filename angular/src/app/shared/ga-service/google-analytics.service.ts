// Google Analytics (GA) script was handled differently from traditional web pages. Angular 2+ is a SPA
// which was considered only one page.
// But if a page is launched in a new tab, it was consider a new page and the GA script will be triggered.
// In PDR, we have only landing page and datacart page. Landing page open datacart page in a new tab. 
// So we don't need to fire gas() function here.

import { Injectable } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
declare var gas: Function;
declare var _initAutoTracker: Function;

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

  // Tracking pageview
  gaTrackPageview(url: string, title: string) {
    setTimeout(() => {
      gas('send', 'pageview', url, title);
    }, 1000);
  }

  // Tracking events
  gaTrackEvent(category: string, event?:any, label?: string, action?: string) {
    if(action == undefined){
      // menu item
      if(event.item != undefined){
        action = event.item.url;
        label = event.item.label;
      }else if(event.path != undefined){
        for(var i = 0; i < event.path.length; i++){
          if(event.path[i].href != undefined){
            action = event.path[i].href;
            label = event.path[i].innerText;
            if(label == '' || label == undefined)
              label = event.path[i].hostname;
            break;
          }
        }
      }else
        action = 'URL not catched';
    }
    action = (action == undefined)?"":action;
    label = (label == undefined)?"":label;

    setTimeout(() => {
      gas('send', 'event', category, action, label, 1);
    }, 1000);
  }

  public appendGaTrackingCode() {
    console.log("Appending tracking code...");
    try {
      let scriptId = '_fed_an_ua_tag';

      if (document.getElementById(scriptId)) {
          console.log("Found GA id.");
          document.getElementById(scriptId).remove();
      }

      var s = document.createElement('script') as any;
      s.type = "text/javascript";
      s.id = scriptId;
      s.src = "https://dap.digitalgov.gov/Universal-Federated-Analytics-Min.js?agency=DOC&subagency=NIST&pua=UA-66610693-14&yt=true&exts=ppsx,pps,f90,sch,rtf,wrl,txz,m1v,xlsm,msi,xsd,f,tif,eps,mpg,xml,pl,xlt,c";

      var h = document.getElementsByTagName("head");
      console.log("head", h);
      document.getElementsByTagName("head")[0].appendChild(s);


      // const script = document.createElement('script');
      // console.log("script", script);
      // script.async = true;
      // script.src = "https://dap.digitalgov.gov/Universal-Federated-Analytics-Min.js?agency=DOC&subagency=NIST&pua=UA-66610693-14&yt=true&exts=ppsx,pps,f90,sch,rtf,wrl,txz,m1v,xlsm,msi,xsd,f,tif,eps,mpg,xml,pl,xlt,c";
      // document.head.appendChild(script);
    } catch (ex) {
      console.error('Error appending google analytics');
      console.error(ex);
    }

  }
}
