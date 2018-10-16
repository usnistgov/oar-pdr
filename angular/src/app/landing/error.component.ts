
import { ActivatedRoute }     from '@angular/router';
import {Component,Input, Inject, OnInit, Optional, PLATFORM_ID} from '@angular/core';
import {isPlatformBrowser} from '@angular/common';
import {RESPONSE} from '@nguniversal/express-engine/tokens';
import {Response} from 'express';

@Component({
  moduleId: module.id,
  styleUrls: ['landing.component.css'],
  selector: 'error-template',
  template: `
  <div class="ui-g">
      <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
        <h3 id="error" name="error"><b>Error</b></h3><br>   
        <div>
        <b>ErrorStatus: {{ errorcode }}</b> <br>
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
    searchid:string;
    @Optional() @Inject(RESPONSE) private response: Response;

    constructor(private route: ActivatedRoute){
    }
    ngOnInit(){
        this.searchid = this.route.snapshot.paramMap.get('id');

    }
  ngAfterViewInit(){
  }
}

@Component({
    moduleId: module.id,
    styleUrls: ['landing.component.css'],
    selector: 'user-error',
    template: `
    <div class="ui-g">
        <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
          <h3 id="uerror" name="uerror"><b>Error</b></h3><br>   
          <div>
            ErrorStatus: {{ errorcode }} !! <br>
            The landing page for the given ID cannot be displayed due to some error.  <br>
            Please make sure you have requested  correct id <b>{{ searchid }}</b> in your query and try again.  
          </div>
        </div>
     </div>
    `
  })
  
  export class UserErrorComponent {
    @Optional() @Inject(RESPONSE) private response: Response;
      searchid:string;
      errorcode: string;
      constructor(private route: ActivatedRoute
     ){
  
      }
      ngOnInit(){
          this.searchid = this.route.snapshot.paramMap.get('id');
          this.errorcode = this.route.snapshot.paramMap.get('errorcode');
          console.log(this.errorcode);
          if (this.errorcode == "404") {
            this.response.status(404);
          }
      }
    ngAfterViewInit(){
  
     //window.history.replaceState( {} , '#/error/', '/error/');
    }
  }