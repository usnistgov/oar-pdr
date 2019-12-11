import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
    selector: 'app-description-popup',
    templateUrl: './description-popup.component.html',
    styleUrls: ['./description-popup.component.css']
})
export class DescriptionPopupComponent implements OnInit {
    @Input() inputValue: any;
    @Input() field: string;
    @Input() title: string;
    @Input() message?: string;
    @Output() returnValue: EventEmitter<any> = new EventEmitter();

    tempDescription: any;
    tempReturn: any = {};
    defaultText: string = "Enter description here...";

    constructor(public activeModal: NgbActiveModal) { }

    ngOnInit() {
        this.tempDescription = JSON.stringify(this.inputValue[this.field]);
    }

    saveDescription() {
        this.returnValue.emit(this.inputValue);
        window.scroll(0, 0);
        this.activeModal.close('Close click');
    }

    cancelChange() {
        window.scroll(0, 0);
        this.activeModal.close('Close click');
    }
}
