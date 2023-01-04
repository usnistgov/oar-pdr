import { Component, Input, OnInit } from "@angular/core";

@Component({
    selector:    'rpd-request-form-terms',
    templateUrl: './terms.component.html',
    styleUrls: ['./request-form.component.css'],
    providers:  [  ]
  })
  export class TermsComponent implements OnInit {
    @Input() terms: string[] = [];
    domparser = new DOMParser();  
    constructor() { }

    ngOnInit() {
      
    }
  }