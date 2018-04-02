import { Component, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
// import { FormBuilder, FormGroup } from '@angular/forms';



@Component({
  selector: 'landing-to-do',
  templateUrl: './landingAbout.component.html',
  styleUrls: ['./landingAbout.component.css']
})
export class LandingAboutComponent implements OnInit {
 
 headerText: string;

  constructor() {
    
  }

  ngOnInit() {
    //this.getTodos();
  }

  getTodos() {
    //this.todos = this._todoService.getTodosFromData();
  }

  
}
