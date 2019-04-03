
import { ActivatedRoute } from '@angular/router';
import { Component, Input, Inject, OnInit, Optional, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { RESPONSE } from '@nguniversal/express-engine/tokens';
import { Response } from 'express';

@Component({
  moduleId: module.id,
  styleUrls: ['landing.component.css'],
  selector: 'error-template',
  template: `
  <div class="ui-g">
      <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
        <h3 id="error" name="error"><b>Error</b></h3><br>   
        <div>
        The landing page for the given ID cannot be displayed due to an internal error.  <br>
        Please contact us at 
        <a href="mailto:datasupport@nist.gov?subject=PDR: {{ searchid }}&body= ">datasupport@nist.gov</a> to report the problem. If possible, include the 
        string "PDR: {{ searchid }}" in your email report.  
        </div>
      </div>
   </div>
  `
})

export class ErrorComponent {
  searchid: string;
  errorcode: string;

  constructor(private route: ActivatedRoute, @Optional() @Inject(RESPONSE) private response: Response) {
  }
  ngOnInit() {
    this.searchid = this.route.snapshot.paramMap.get('id');
    this.response.statusCode = 500;
    this.response.statusMessage = "There is internal server error!"
  }
  ngAfterViewInit() {
  }
}

@Component({
  moduleId: module.id,
  // styleUrls: ['landing.component.css'],
  selector: 'user-error',
  template: `
    <div class="ui-g">
        <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
          <h3 id="uerror" name="uerror"><b>Error</b></h3><br>   
          <div>
            The landing page for the given ID cannot be displayed due to some error.  <br>
            Please make sure you have requested  correct id <b>{{ searchid }}</b> in your query and try again.  
          </div>
        </div>
     </div>
    `
})

export class UserErrorComponent implements OnInit {
  searchid: string;
  public errorcode: number;
  constructor(private route: ActivatedRoute, @Optional() @Inject(RESPONSE) private response: Response) {

  }
  ngOnInit() {
    if (this.response != null) {
      this.response.statusCode = 404;
      this.errorcode = this.response.statusCode;
      this.response.statusMessage = "There is an user error!";
      console.log(this.errorcode);
    }
  }
  ngAfterViewInit() {

    //window.history.replaceState( {} , '#/error/', '/error/');
  }
}