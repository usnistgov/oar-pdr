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
    selector: 'not-found',
    styleUrls: [ '../landing/landing.component.css' ],
    template: `
<div class="card landingcard">
  <div class="ui-g">
    <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
      <div class="title"><h2 id="not-found" name="not-found">Hmm...</h2></div>
    </div>
  </div>
  <div class="ui-g">
    <div class = "ui-g-12 ui-md-12 ui-lg-12 ui-sm-12">
      <div *ngIf="requestedID; else generic">
        <p>Requested ID not found: {{requestedID}}.</p>
      </div>
      <ng-template #generic><p>Requested URL not found</p></ng-template>
    </div>
  </div>
</div>
`
})
export class NotFoundComponent implements OnInit {
    requestedID : string|null = null;
    
    constructor(private route: ActivatedRoute, @Inject(PLATFORM_ID) private platid : object,
                private injector : Injector)
    {
        // an error here will get caught by the error handler; however,
        // the response status update does not take, nor does re-routing.
        // 
        // throw new Error("Testing error handling from component constructor");
    }
    
    ngOnInit() {
        this.requestedID = this.route.snapshot.paramMap.get('id');

        if (isPlatformServer(this.platid)) {
            let resp : Response = this.injector.get(RESPONSE) as Response;
            resp.status(404);
        }

        // an error here will get caught by the error handler; updating the
        // HTTP status code and rerouting in the handler works.
        // 
        // throw new Error("Testing error handling from ngOnInit");
    }

    /**
     * apply housekeeping after view has been initialized
     */
    ngAfterViewInit() {
        if (this.inBrowser && this.requestedID) {
            window.history.replaceState({}, '', '/od/id/' + this.requestedID);
        }
    }
}
