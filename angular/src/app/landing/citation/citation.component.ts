/*
 * This file defines two components:
 *
 * Two components are provided for displaying this information:
 *  * CitationDescriptionComponent -- a component that display the information in a panel
 *  * CitationPopupComponent -- a component that wraps the description in a pop-up widget
 */
import { Component, Input, Output, OnChanges, EventEmitter } from '@angular/core';

/**
 * A component for displaying information about how to cite a data resource described 
 * by a NERDm metadata record
 */
@Component({
    selector: 'citation-display',
    template: `
<span><b>Copy the recommended text to cite this resource </b></span> <br><br>
<p contenteditable="false" class="citation">{{ citetext }}</p>
<br>
<a target="citationsRecommendation"
   href="https://www.nist.gov/director/copyright-fair-use-and-licensing-statements-srd-data-and-software#citations">See also the NIST Citation Recommendations.</a>
`,
    styles: [
        ".citation { font-size: 14px; }"
    ]
})
export class CitationDescriptionComponent {
    /** the recommended citation string */
    @Input() citetext : string;
}
    
/**
 * a component for displaying citation information in a pop-up window
 */
@Component({
    selector: 'citation-popup',
    template: `
    <p-dialog #citepopup header="Citation" modal="true" [(visible)]="visible" (click)="hide()" [style]="{width: '70vw'}" [baseZIndex]="10000">
      <p-header> Citation
      </p-header>
      <citation-display [citetext]="citetext"></citation-display>
    </p-dialog>
    `,
    styles: [
        `
        :host ::ng-deep .p-dialog.customDialog{
            /* background-color:rgb(0, 255, 76); */
            color: red;
        }
        
        :host ::ng-deep .ui-dialog .ui-dialog-titlebar{
            background-color: #05ff43 !important;
            color: #212121;
            font-family: sans-serif;
            font-size: 16px;
        }
        `
    ]
})
export class CitationPopupComponent {
    @Input() citetext : string;
    @Input() visible : boolean;
    @Input() width: number;
    @Output() visibleChange = new EventEmitter<boolean>();

    _setVisible(yesno : boolean) : void {
        this.visible = yesno;
        this.visibleChange.emit(this.visible);
    }        

    /** display the pop-up */
    show() : void { this._setVisible(true); }

    /** dismiss the pop-up */
    hide() : void { this._setVisible(false); }

    /** dismiss the pop-up */
    toggle() : void { this._setVisible(!this.visible); }
}
