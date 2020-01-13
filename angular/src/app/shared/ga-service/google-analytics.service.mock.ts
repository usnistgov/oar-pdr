import { Injectable } from '@angular/core';
import {Router, NavigationEnd} from '@angular/router';

declare var gas:Function; 

@Injectable()
export class GoogleAnalyticsServiceMock {
  constructor(router: Router) {
  }
}
