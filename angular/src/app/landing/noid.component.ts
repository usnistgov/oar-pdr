import { Component, Input } from '@angular/core';

@Component({
  styleUrls: ['landing.component.css'],
  selector: 'noid-template',
  template: `
  <div class="ui-g">
      <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
        <h3 id="noid" name="noid"><b>Empty Record</b></h3><br>   
        <div>Landing page is empty as no record id provided.</div>
      </div>
   </div>
  `
})

export class NoidComponent {
  ngAfterViewInit(){

    //window.history.replaceState( {} , '#/id/', '/od/id');
  }
}

