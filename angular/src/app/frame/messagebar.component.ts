import { Component, Optional, ChangeDetectorRef } from '@angular/core';
import { UserMessageService, Message } from './usermessage.service';

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

    private nextid = 0;
    messages : Message[] = [];
    // bgcolor : string = "#FCF9CD";

    public constructor(private chgDetRef : ChangeDetectorRef,
                       @Optional() private svc : UserMessageService) {
        if (svc) {
            svc._subscribe({
                next: (msg) => {
                    this.messages.push(msg)  // msg: an object with type, message
                }
            });
        }
    }

    _addMessage(message : string, type ?: string) {
        if (! type) type = "information";
        this.messages.push({ type: type, text: message, id: ++this.nextid });
    }

    _msgid(item, i) { return item['id']; }

    /**
     * remove a message from the list currently displayed
     */
    public dismiss(msgid : any) {
        let msg : any;
        console.log("trying to dismiss message id="+msgid);
        for (let i=0; i < this.messages.length; i++) {
            console.log("message "+i.toString()+" id="+this.messages[i].id);
            if (this.messages[i].id == msgid) {
                this.messages.splice(i, 1);
                this.chgDetRef.detectChanges();
                break;
            }
        }
    }

    /**
     * remove all messages from view
     */
    public dismissAll() {
        this.messages.splice(0, this.messages.length);
        this.chgDetRef.detectChanges();
    }

    /**
     * Provide some brief instruction.  This is intended for prompts to the user 
     * advising some action or choice of actions.
     */
    public instruct(message : string) : void {
        this._addMessage(message, "instruction");
    }

    /**
     * Provide a confirmation or report of a successful action.  This is intended 
     * to assure the user that a user action was successful.
     */
    public celebrate(message : string) : void {
        this._addMessage(message, "celebration");
    }

    /**
     * Display a warning.  This is to alert the user about issues that they may 
     * want to remedy.
     */
    public warn(message : string) : void {
        this._addMessage(message, "warning");
    }

    /*
     * Provide some helpful information without concern or worry.  
     */
    public inform(message : string) : void {
        this._addMessage(message, "information");
    }

    /*
     * Provide a suggestion.  
     */
    public tip(message : string) : void {
        this._addMessage(message, "tip");
    }

    /*
     * Report a (user) error.  Use this to inform the user of error conditions due to 
     * incorrect user action
     */
    public error(message : string) : void {
        this._addMessage(message, "error");
    }

    /*
     * Report a system error.  Use this to inform the user of error conditions due to 
     * unexpected conditions that are not the fault of the user.  
     */
    public syserror(message : string) : void {
        this._addMessage(message, "syserror");
    }
}
