/* 
 * Error infrastructure, including an ErrorHandler
 */
import { ErrorHandler, Injector, Injectable, Inject, PLATFORM_ID, Optional } from "@angular/core";
import { isPlatformServer } from '@angular/common';
import { Router }                             from "@angular/router";
import { RESPONSE } from '@nguniversal/express-engine/tokens';
import { Response } from 'express';

/**
 * an application-wide ErrorHandler.
 * 
 * The intent of this handler is to capture internal errors and reroute the response to 
 * the /int-error page.  
 */
@Injectable()
export class AppErrorHandler implements ErrorHandler {

    constructor(@Inject(PLATFORM_ID) private platid : object, private injector : Injector)
    { }

    public handleError(error : any) {
        console.error("LPS Application Error: "+error);
        if (isPlatformServer(this.platid))
            console.trace();
        let router : Router|null = null
        try {
            router = this.injector.get(Router) as Router;
        } catch (e) {
            console.log("No router available to reroute on error. ("+e.message+")");
        }

        if (isPlatformServer(this.platid)) {
            // this is needed if rerouting is not possible or status was already set (?)
            console.log("Setting response status to 500");
            let resp : Response = this.injector.get(RESPONSE) as Response;
            resp.status(500);
        }

        if (router) {
            // rerouting may not work if we've already started to build the page.  
            console.log("attempting reroute to /int-error");
            router.navigateByUrl("/int-error", { skipLocationChange: true });
        }
    }
}
