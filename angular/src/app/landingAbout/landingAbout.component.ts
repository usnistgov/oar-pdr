import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { CommonVarService } from '../shared/common-var'
// import { FormBuilder, FormGroup } from '@angular/forms';

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
    //this.getTodos();
    this.commonVarService.setContentReady(true);
  }

  getTodos() {
    //this.todos = this._todoService.getTodosFromData();
  }

  
}
