import { Component, OnInit, Input } from '@angular/core';
import { trigger, state, style, animate, transition } from '@angular/animations';

@Component({
    selector: 'app-facilitators',
    templateUrl: './facilitators.component.html',
    styleUrls: ['./facilitators.component.css'],
    animations: [
        trigger('detailExpand', [
        state('collapsed', style({height: '0px', minHeight: '0'})),
        state('expanded', style({height: '*'})),
        transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
        //   transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
        ])
    ]
})
export class FacilitatorsComponent implements OnInit {
    facilitators: any[] = [];
    clickFacilitators: boolean = false;
    isCollapsedContent: boolean = true;
    expandButtonAlterText: string = "Open dataset details";
    expandIconClass: string = "faa-caret-right";
    expanded = false;

    @Input() record: any[];
    @Input() inBrowser: boolean;   // false if running server-side

    constructor() { }

    ngOnInit(): void {
        if(this.record["facilitators"]){
            this.facilitators = this.record["facilitators"];
        }

    }

    getFieldStyle() {
        return "";
    }

    /**
     * Toggle the visibility of the facilitator details;
     * Set icon class for the expand button;
     * Set expand button alter text.
     */
    toggleExpand() {
        this.expanded = !this.expanded;
        this.expandIconClass = this.expanded? "faa-caret-down" : "faa-caret-right";
        this.expandButtonAlterText = this.expanded? "Close facilitator details" : "Open facilitator details";
    }
}
