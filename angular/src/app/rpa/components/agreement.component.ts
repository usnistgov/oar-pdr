import { Component, Input, OnInit } from "@angular/core";

@Component({
    selector:    'rpd-request-form-agreement',
    templateUrl: './agreement.component.html',
    styleUrls: ['./request-form.component.css'],
    providers:  [  ]
  })
  export class AgreementComponent implements OnInit {
    @Input() text: string;
    constructor() { }

    ngOnInit() {
      
    }
  }