import { Component, OnInit } from '@angular/core';
import { CommonVarService } from '../shared/common-var'

@Component({
  selector: 'landing-about',
  templateUrl: './landingAbout.component.html',
  styleUrls: ['./landingAbout.component.css']
})
export class LandingAboutComponent implements OnInit {
 
 headerText: string;

  constructor(private commonVarService: CommonVarService) {
    
  }

  ngOnInit() {
    this.commonVarService.setContentReady(true);
  }
}
