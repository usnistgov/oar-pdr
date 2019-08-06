import { Component } from '@angular/core';
import { GoogleAnalyticsService } from '../shared/ga-service/google-analytics.service';

/**
 * A Component that serves as the footer of the landing page.  
 * 
 * Features include:
 * * Set as black bar at the bottom of the page
 */
@Component({
  moduleId: module.id,
  selector: 'pdr-footbar',
  templateUrl: 'footbar.component.html',
  styleUrls: ['footbar.component.css']
})
export class FootbarComponent { 
  constructor(public gaService: GoogleAnalyticsService){}

}
