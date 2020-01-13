import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

export interface errMessage {
    message: string;
    messageDetail: string;
    action: string;
    display: boolean;
}

@Injectable({
    providedIn: 'root'
})
export class ErrorHandlingService {
    errorMessageSub = new BehaviorSubject<errMessage>({ message: '', messageDetail: '', action: '', display: false });

    constructor() { }

    /**
     * Set data changed flag
     **/
    setErrMessage(value: errMessage) {
        this.errorMessageSub.next(value);
    }

    /**
     * Watching data changed flag
     **/
    watchErrMessage(): Observable<any> {
        return this.errorMessageSub.asObservable();
    }
}
