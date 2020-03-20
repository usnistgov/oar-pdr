import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

/**
 * A Component that allows user to edit description.  
 * 
 * Features include:
 * * A black title bar at the top of the page that displays the input title value
 * * A blue background tool bar with control buttons
 * * A text edit box that user can edit description.
 *   * Since this is a required field, once it's empty or all white spaces, the save
 *   * button will be disabled
 */

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

    tempReturn: any = {};
    defaultText: string = "Enter description here...";

    constructor(public activeModal: NgbActiveModal) { }

    ngOnInit() { }

    /*
     *   Function to emit decription and close this pop up window
     */
    saveDescription() {
        this.returnValue.emit(this.inputValue);
        window.scroll(0, 0);
        this.activeModal.close('Close click');
    }

    /*
     *   Function to close this pop up window without emit any change
     */
    cancelChange() {
        window.scroll(0, 0);
        this.activeModal.close('Close click');
    }

    /*
     *   Once user types in the description edit box, trim leading and ending 
     *   white spaces
     */
    onDescriptionChange(field: any, event: any) {
        this.inputValue[field] = event; 
    }
}
