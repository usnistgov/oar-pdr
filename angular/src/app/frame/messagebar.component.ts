import { Component, Optional, Input } from '@angular/core';
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

    @Input() defSysErrorPrefix : string = "There was an internal hiccup.";
    // bgcolor : string = "#FCF9CD";

    public constructor(@Optional() private svc : UserMessageService) {
        if (svc) {
            svc._subscribe({
                next: (msg) => {
                    this.messages.push(msg)  // msg: an object with type, message
                }
            });
        }
    }

    _addMessage(message : string, type ?: string, prefix : string = "") : void {
        if (! type) type = "information";
        this.messages.push({ type: type, text: message, prefix: prefix, id: this.nextid++ });
    }

    _msgid(item, i) { return item['id']; }

    /**
     * remove a message from the list currently displayed
     */
    public dismiss(msgid : any) {
        let msg : any;
        for (let i=0; i < this.messages.length; i++) {
            if (this.messages[i].id == msgid) {
                this.messages.splice(i, 1);
                break;
            }
        }
    }

    /**
     * remove all messages from view
     */
    public dismissAll() {
        this.messages.splice(0, this.messages.length);
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
     * 
     * @param mesage   A technical (perhaps non-user oriented) explanation of the error
     * @param prefix   An optional, extra explanation that is expected to be more user-oriented.
     */
    public syserror(message : string, prefix ?: string) : void {
        this._addMessage(message, "syserror");
    }
}
