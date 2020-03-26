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
        if (isPlatformServer(this.platid) && error.stack)
            console.error(error.stack);
        let router : Router|null = null
        try {
            router = this.injector.get(Router) as Router;
        } catch (e) {
            console.log("No router available to reroute on error. ("+e.message+")");
        }

        if (isPlatformServer(this.platid)) {
            let respstat = 500;
            if (error instanceof IDNotFound)
                respstat = 404;
            
            // this is needed if rerouting is not possible or status was already set (?)
            console.log("Setting response status to "+respstat);
            let resp : Response = this.injector.get(RESPONSE) as Response;
            resp.status(respstat);
        }

        if (router) {
            // rerouting may not work if we've already started to build the page.  

            if (error instanceof IDNotFound) {
                console.log("attempting reroute to /not-found");
                router.navigateByUrl("/not-found/"+error.id, { skipLocationChange: true });
            }
            else {
                console.log("attempting reroute to /int-error");
                router.navigateByUrl("/int-error", { skipLocationChange: true });
            }
        }
    }
}

/**
 * a custom exception indicating a request for the landing page for a non-existent identifier
 */
export class IDNotFound {

    public message : string;

    /**
     * create the error
     * @param id   the ID that was requested but does not exist
     */
    constructor(public id : string) {
        this.message = "Resource identifier not found: "+id;
    }

    public toString() : string { return this.message; }
}
