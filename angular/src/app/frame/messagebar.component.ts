import { Component, Optional } from '@angular/core';
import { UserMessageService } from './usermessage.service';

/**
 * A Component that can receive and display messages.
 * 
 * This component accepts messages through a variety of methods representing different 
 * kinds of messages, including warn(), error(), and celebrate().  Each function can 
 * format the message in its own way, and it applies its own style properties (as 
 * provided in messagebar.component.css).  
 */
@Component({
    selector: 'pdr-message',
    templateUrl: 'messagebar.component.html',
    styleUrls: [ 'messagebar.component.css'   ]
})
export class MessageBarComponent {

    messageClass : string = "instruction";
    message : string = "";
    // bgcolor : string = "#FCF9CD";

    public constructor(@Optional() private svc : UserMessageService) {
        if (svc) {
            svc._subscribe({
                next: (msg) => {
                    this.messageClass = msg.type;
                    this.message = msg.text
                }
            });
        }
    }

    /**
     * Provide some brief instruction.  This is intended for prompts to the user 
     * advising some action or choice of actions.
     */
    public instruct(message : string) : void {
        this.messageClass = "instruction";
        this.message = message;
    }

    /**
     * Provide a confirmation or report of a successful action.  This is intended 
     * to assure the user that a user action was successful.
     */
    public celebrate(message : string) : void {
        this.messageClass = "celebration";
        this.message = message;
    }

    /**
     * Display a warning.  This is to alert the user about issues that they may 
     * want to remedy.
     */
    public warn(message : string) : void {
        this.messageClass = "warning";
        this.message = message;
    }

    /*
     * Provide some helpful information without concern or worry.  
     */
    public inform(message : string) : void {
        this.messageClass = "information";
        this.message = message;
    }

    /*
     * Provide a suggestion.  
     */
    public tip(message : string) : void {
        this.messageClass = "tip";
        this.message = message;
    }

    /*
     * Report a (user) error.  Use this to inform the user of error conditions due to 
     * incorrect user action
     */
    public error(message : string) : void {
        this.messageClass = "error";
        this.message = message;
    }

    /*
     * Report a system error.  Use this to inform the user of error conditions due to 
     * unexpected conditions that are not the fault of the user.  
     */
    public syserror(message : string) : void {
        this.messageClass = "syserror";
        this.message = message;
    }
}
