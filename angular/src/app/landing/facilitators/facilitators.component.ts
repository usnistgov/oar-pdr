import { Component, OnInit, Input } from '@angular/core';
import { trigger, state, style, animate, transition } from '@angular/animations';

@Component({
    selector: 'app-facilitators',
    templateUrl: './facilitators.component.html',
    styleUrls: ['./facilitators.component.css'],
    animations: [
        trigger('detailExpand', [
        state('collapsed', style({height: '0px', minHeight: '0', display: 'none'})),
        state('expanded', style({height: '*'})),
        transition('expanded <=> collapsed', animate(625)),
        //   transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
        ])
    ]
})
export class FacilitatorsComponent implements OnInit {
    facilitators: any[] = [];
    clickFacilitators: boolean = false;
    isCollapsedContent: boolean = true;

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

    clicked = false;
    expandClick() {
        this.clicked = !this.clicked;
        return this.clicked;
    }
}
