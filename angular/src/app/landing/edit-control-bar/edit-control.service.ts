import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

export interface errMessage {
    err: string;
    errDetail: any;
}

@Injectable({
    providedIn: 'root'
})
export class EditControlService {
    ediid: string = null;
    editModeSub = new BehaviorSubject<boolean>(false);
    ediidSub = new BehaviorSubject<string>("");
    dataChangedSub = new BehaviorSubject<boolean>(false);
    errSub = new BehaviorSubject<errMessage>({ err: '', errDetail: null });
    isProcessingSub = new BehaviorSubject<boolean>(false);
    messageSub = new BehaviorSubject<string>("");
    editButtonClickSub = new BehaviorSubject<boolean>(false);

    constructor() { }

    /**
     * Set message for display
     **/
    setMessage(value: string) {
        this.messageSub.next(value);
    }

    /**
     * Watching message
     **/
    watchMessage(): Observable<string> {
        return this.messageSub.asObservable();
    }

    /**
     * Set landing page ready flag
     **/
    setIsProcessing(value: boolean) {
        this.isProcessingSub.next(value);
    }

    /**
     * Watching landing page ready flag
     **/
    watchIsProcessing(): Observable<boolean> {
        return this.isProcessingSub.asObservable();
    }

    /**
     * Set edit mode flag
     **/
    setEditMode(value: boolean) {
        this.editModeSub.next(value);
    }

    /**
     * Watching edit mode flag
     **/
    watchEditMode(): Observable<boolean> {
        return this.editModeSub.asObservable();
    }

        /**
     * Set edit mode flag
     **/
    setEditButtonClick(value: boolean) {
        this.editButtonClickSub.next(value);
    }

    /**
     * Watching edit mode flag
     **/
    watchEditButtonClick(): Observable<boolean> {
        return this.editButtonClickSub.asObservable();
    }

    /**
     * Set data changed flag
     **/
    setErrMessage(value: errMessage) {
        this.errSub.next(value);
    }

    /**
     * Watching data changed flag
     **/
    watchErrMessage(): Observable<any> {
        return this.errSub.asObservable();
    }


    /**
     * Set data changed flag
     **/
    setDataChanged(value: boolean) {
        this.dataChangedSub.next(value);
    }

    /**
     * Watching data changed flag
     **/
    watchDataChanged(): Observable<any> {
        return this.dataChangedSub.asObservable();
    }


    /**
     * Set ediid
     **/
    setEdiid(value: string) {
        this.ediid = value;
        this.ediidSub.next(value);
    }

    /**
    * Watching ediid
    **/
    watchEdiid(): Observable<any> {
        return this.ediidSub.asObservable();
    }

    /**
     * Reload PDR page
     */
    reloadPdrPage() {
        window.open('/od/id/' + this.ediid, '_self');
    }
}
