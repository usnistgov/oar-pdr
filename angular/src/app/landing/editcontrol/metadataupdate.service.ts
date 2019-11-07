import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

import { UserMessageService } from '../../frame/usermessage.service';
import { CustomizationService } from './customization.service';

/**
 * a service that receives updates to the resource metadata from update widgets.
 * 
 * This service mediates the updates between user-facing editing widgets, the 
 * CustomizationService (which saves updates in "draft" record stored on the server), 
 * and a controller object--namely, the EditControlPanel--that handles updating the 
 * resource metadata used to drive the landing page display.  In particular, editing
 * widgets send their metadata updates to this class (via update()); this class will 
 * then forward the changes to the CustomizationService and forward the full, updated 
 * record to the controller object.
 *
 * This class also works with a UserMessageService to alert the user with messages when 
 * things go wrong.  
 */
@Injectable()
export class MetadataUpdateService {

    private mdres : Subject<{}> = new Subject<{}>();
    private custsvc : CustomizationService = null;

    /**
     * construct the service
     * 
     * @param custsvc   the CustomizationService to use to send updates to the 
     *                  server.  
     */ 
    constructor(private msgsvc  : UserMessageService)
    { }

    /*
     * subscribe to updates to the metadata.  This is intended for connecting the 
     * service to the EditControlPanel.
     */
    _subscribe(controller) : void {
        this.mdres.subscribe(controller);
    }

    _setCustomizationService(svc : CustomizationService) : void {
        this.custsvc = svc;
    }

    /**
     * update the resource metadata.
     * 
     * The given object will be merged into the resource metadata.  The update will be 
     * sent to the server, and the full and updated version of the metadata will be 
     * sent to the metadata controller.
     *
     * @param md   an object containing the portion of the resource metadata that 
     *             should be updated.  
     */
    public update(md : {}) : void {
        if (! this.custsvc) {
            console.error("Attempted to update without authorization!  Ignoring update.");
            return;
        }
        
        this.custsvc.updateMetadata(md).subscribe(
            (res) => {
                // console.log("Draft data returned from server:\n  ", res)
                this.mdres.next(res);
            },
            (err) => {
                // err will be a subtype of CustomizationError
                if (err.type == 'user') {
                    console.error("Failed to save metadata changes: user error:" + err);
                    this.msgsvc.error(err.message)
                }
                else {
                    console.error("Failed to save metadata changes: server/system error:" + err);
                    this.msgsvc.syserror(err.message)
                }
            }
        );
    }

    /**
     * load the latest draft of the resource metadata.
     * 
     * retrieve the latest draft of the resource metadata from the server and forward it
     * to the controller for display to the user.  
     */
    public loadDraft() : void {
        if (! this.custsvc) {
            console.error("Attempted to update without authorization!  Ignoring update.");
            return;
        }
        
        console.log("Loading draft metadata");
        this.custsvc.getDraftMetadata().subscribe(
            (res) => {
                // console.log("Draft data returned from server:\n  ", res)
                this.mdres.next(res);
            },
            (err) => {
                // err will be a subtype of CustomizationError
                if (err.type = 'user') {
                    console.error("Failed to retrieve draft metadata changes: user error:" + err);
                    this.msgsvc.error(err.message)
                }
                else {
                    console.error("Failed to retrieve draft metadata changes: server error:" + err);
                    this.msgsvc.syserror(err.message)
                }
            }
        );
    }

}
