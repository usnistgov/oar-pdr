import { Subject } from 'rxjs';

export interface Message {
    type : string;
    text : string;
    id  ?: any;
}

/**
 * a service for sending user messages to the MessageComponent
 * 
 * Like the MessageBarComponent, this service accepts messages through a variety of 
 * methods representing different kinds of messages, including warn(), error(), and 
 * celebrate().  The MessageBarComponent will display the message with a custom 
 * formatting and style appropriate for the message type.  
 * 
 * This class can be extended to modify or decorate messages of particular types 
 * with, say, extra information. 
 */
export class UserMessageService {

    private msg : Subject<Message> = new Subject<Message>();

    /*
     * connect a receiver to this service that will display the messages
     */
    _subscribe(receiver) : void {
        this.msg.subscribe(receiver);
    }
    
    /**
     * Provide some brief instruction.  This is intended for prompts to the user 
     * advising some action or choice of actions.
     */
    public instruct(message : string) : void {
        this.msg.next({ type: "instruction", text: message });
    }

    /**
     * Provide a confirmation or report of a successful action.  This is intended 
     * to assure the user that a user action was successful.
     */
    public celebrate(message : string) : void {
        this.msg.next({ type: "celebration", text: message });
    }

    /**
     * Display a warning.  This is to alert the user about issues that they may 
     * want to remedy.
     */
    public warn(message : string) : void {
        this.msg.next({ type: "warning", text: message });
    }

    /*
     * Provide some helpful information without concern or worry.  
     */
    public inform(message : string) : void {
        this.msg.next({ type: "information", text: message });
    }

    /*
     * Provide a suggestion.  
     */
    public tip(message : string) : void {
        this.msg.next({ type: "tip", text: message });
    }

    /*
     * Report a (user) error.  Use this to inform the user of error conditions due to 
     * incorrect user action
     */
    public error(message : string) : void {
        this.msg.next({ type: "error", text: message });
    }

    /*
     * Report a system error.  Use this to inform the user of error conditions due to 
     * unexpected conditions that are not the fault of the user.  
     */
    public syserror(message : string) : void {
        this.msg.next({ type: "syserror", text: message });
    }
}
