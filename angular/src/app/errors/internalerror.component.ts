import { Component, OnInit, Injector, Inject, Optional, PLATFORM_ID } from '@angular/core';
import { isPlatformServer } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { RESPONSE } from '@nguniversal/express-engine/tokens';
import { Response } from 'express';

/**
 * A Component that displays an error message indicating that a requested 
 * URL path could not be found (i.e. as in, a 404 status).  
 */
@Component({
    moduleId: module.id,
    selector: 'internal-error',
    styleUrls: [ '../landing/landing.component.css' ],
    template: `
<div class="card landingcard">
  <div class="ui-g">
    <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
      <div class="title"><h2 id="internal-error" name="internal-error">Oops!</h2></div>
    </div>
  </div>
  <div class="ui-g">
    <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
      <p>
We're sorry!  An internal error occurred while preparing your content.  
      </p>
      <p>
Please try loading this page again.  If the error persists, feel free to send the URL along 
to us at <a href="mailto:datasupport@nist.gov">datasupport@nist.gov</a>. 
      <span *ngIf="requestedID">
Please include the text, "PDR: {{ requestedID }}", in your email.  
      </span>
      </p>
    </div>
  </div>
</div>
`
})
export class InternalErrorComponent implements OnInit {
    requestedID : string|null = null;
    
    constructor(private route: ActivatedRoute, @Inject(PLATFORM_ID) private platid : object,
                private injector : Injector)
    { }
    
    ngOnInit() {
        this.requestedID = this.route.snapshot.paramMap.get('id');

        if (isPlatformServer(this.platid)) {
            let resp : Response = this.injector.get(RESPONSE) as Response;
            resp.status(500);
        }
    }
}
