import { Component, Input } from '@angular/core';
import { ActivatedRoute }     from '@angular/router';
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
    searchid:string;

    constructor(private route: ActivatedRoute){

    }
    ngOnInit(){
        this.searchid = this.route.snapshot.paramMap.get('id');
    }
  ngAfterViewInit(){

   window.history.replaceState( {} , '#/error/', '/error/');
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
            The landing page for the given ID cannot be displayed due to some error.  <br>
            Please make sure you have requested  correct id <b>{{ searchid }}</b> in your query and try again.  
          </div>
        </div>
     </div>
    `
  })
  
  export class UserErrorComponent {
      searchid:string;
      constructor(private route: ActivatedRoute){
  
      }
      ngOnInit(){
          this.searchid = this.route.snapshot.paramMap.get('id');
      }
    ngAfterViewInit(){
  
     window.history.replaceState( {} , '#/error/', '/error/');
    }
  }