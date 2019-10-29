import { Component, OnInit } from '@angular/core';
import { SharedService } from '../shared/shared'

@Component({
  selector: 'landing-about',
  templateUrl: './landingAbout.component.html',
  styleUrls: ['./landingAbout.component.css']
})
export class LandingAboutComponent implements OnInit {
 
 headerText: string;

  constructor(private commonVarService: SharedService) {
    
  }

  ngOnInit() {
    this.commonVarService.setContentReady(true);
  }
}
