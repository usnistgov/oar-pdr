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
        btnOkText: string = 'YES',
        btnCancelText: string = 'NO',
        dialogSize: 'sm' | 'lg' = 'sm'): Promise<boolean> {
        let ngbModalOptions: NgbModalOptions = {
            backdrop: 'static',
            keyboard: false,
            windowClass: "myAlertPopupClass"
        };
        const modalRef = this.modalService.open(ConfirmationDialogComponent, ngbModalOptions);
        // const modalRef = this.modalService.open(ConfirmationDialogComponent, { size: dialogSize });
        modalRef.componentInstance.title = title;
        modalRef.componentInstance.message = message;
        modalRef.componentInstance.btnOkText = btnOkText;
        modalRef.componentInstance.btnCancelText = btnCancelText;
        modalRef.componentInstance.showWarningIcon = showWarningIcon;

        return modalRef.result;
    }

}
