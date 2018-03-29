import { Component } from '@angular/core';



@Component({
  selector: 'nerdm-detail',
  
  template: `
    <div class="ui-grid ui-grid-responsive ui-grid-pad center">
    <div class="card" style="padding: 2.5rem 2.5rem 2.5rem 2.5rem">
      <label style="font-size: xx-large;float: left;display: block;">NERDm details</label>
      <div class="EmptyBox20"></div>
      <p>
      NIST Extended Resource Data model (NERDm) is the nist POD metadata extention. 
      It is implemented in the JSON-LD format. The conversion from POD to NERDm is a
      lossless conversion keeping all the key fields as is, NERDm adds some extensions.
      <br>
      More details of NERDm  coming soon ....
    </div>
  </div> 
  `
})

export class NerdmComponent {
  ngAfterViewInit() {
    window.history.replaceState( {} , '#/nerdm/', '/pdr/nerdm/' );
  }
}
   