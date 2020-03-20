import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';

import { NgbModal, NgbModalOptions } from '@ng-bootstrap/ng-bootstrap';

import { ConfirmationDialogComponent } from './confirmation-dialog.component';

@Injectable({
    providedIn: 'root'
})
export class ConfirmationDialogService {

    constructor(private modalService: NgbModal) { }

    public confirm(
        title: string,
        message: string,
        showWarningIcon: boolean,
        showCancelButton: boolean = true,
        btnOkText: string = 'YES',
        btnCancelText: string = 'NO',
        dialogSize: 'sm' | 'lg' = 'sm'): Promise<boolean> {
        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "comfirmModalClass",
            size: dialogSize
        };
        const modalRef = this.modalService.open(ConfirmationDialogComponent, ngbModalOptions);
        modalRef.componentInstance.title = title;
        modalRef.componentInstance.message = message;
        modalRef.componentInstance.btnOkText = btnOkText;
        modalRef.componentInstance.btnCancelText = btnCancelText;
        modalRef.componentInstance.showWarningIcon = showWarningIcon;
        modalRef.componentInstance.showCancelButton = showCancelButton;

        return modalRef.result;
    }

    public displayMessage(
        title: string,
        message: string,
        showWarningIcon: boolean = false,
        showCancelButton: boolean = false,
        btnOkText: string = 'Close',
        btnCancelText: string = 'NO',
        dialogSize: 'sm' | 'lg' = 'sm'): Promise<boolean> {
        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myCustomModalClass",
            size: dialogSize
        };
        const modalRef = this.modalService.open(ConfirmationDialogComponent, ngbModalOptions);
        modalRef.componentInstance.title = title;
        modalRef.componentInstance.message = message;
        modalRef.componentInstance.btnOkText = btnOkText;
        modalRef.componentInstance.btnCancelText = btnCancelText;
        modalRef.componentInstance.showWarningIcon = showWarningIcon;
        modalRef.componentInstance.showCancelButton = showCancelButton;

        return modalRef.result;
    }
}
