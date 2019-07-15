import { Injectable } from '@angular/core';
import {Router, NavigationEnd} from '@angular/router';
import { environment } from '../../../environments/environment';
declare var gas:Function; 

@Injectable()
export class GoogleAnalyticsService {
  constructor() {
  }

  /*
  *   Append Google Analytics script to a page
  */
  public appendGaTrackingCode() {
    try {
      console.log("phone home...");
      const script = document.createElement('script');
      script.async = true;
      script.src = "https://dap.digitalgov.gov/Universal-Federated-Analytics-Min.js?agency=DOC&subagency=NIST&pua=UA-66610693-14&yt=true&exts=ppsx,pps,f90,sch,rtf,wrl,txz,m1v,xlsm,msi,xsd,f,tif,eps,mpg,xml,pl,xlt,c";
      document.head.appendChild(script);
    } catch (ex) {
      console.error('Error appending google analytics');
      console.error(ex);
    }

  }
}
