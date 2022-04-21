import { Component, OnInit, Input, HostListener } from '@angular/core';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { trigger, state, style, animate, transition } from '@angular/animations';


@Component({
    selector: 'app-searchresult',
    templateUrl: './searchresult.component.html',
    styleUrls: ['./searchresult.component.css'],
    animations: [
        trigger('filterStatus', [
        state('collapsed', style({width: '39px'})),
        state('expanded', style({width: '*'})),
        transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
        ])
    ]
})
export class SearchresultComponent implements OnInit {
    searchValue: string = 'isPartOf.@id=ark:/88434/mds9911';
    mobHeight: number;
    mobWidth: number;
    mobileMode: boolean = false; // set mobile mode to true if window width < 641
    filterWidth: number;
    filterMode: string = "normal";
    resultWidth: any;
    searchTaxonomyKey: string;
    page: number = 1;
    filterToggler: string = 'expanded';
    filterString: string = "";
    mouse: any = {x:0, y:0};
    mouseDragging: boolean = false;
    prevMouseX: number = 0;
    prevFilterWidth: number = 0;

    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;

    constructor() {
    }

    ngOnInit(): void {
        if(this.inBrowser){
            this.mobWidth = window.innerWidth;
            this.mobileMode = this.mobWidth < 641;
        }

        this.updateWidth();
    }

    // The following mouse functions handle drag action
    @HostListener('window:mousemove', ['$event'])
    onMouseMove(event: MouseEvent){
        this.mouse = {
            x: event.clientX,
            y: event.clientY
        }

        if(this.mouseDragging) {
            let diff = this.mouse.x - this.prevMouseX;
            this.filterWidth = this.prevFilterWidth + diff;
            this.filterWidth = this.filterWidth < 40? 39 : this.filterWidth > 500? 500 : this.filterWidth;
        }

        this.setResultWidth();
    }

    onMousedown(event) {
        this.prevMouseX = this.mouse.x;
        this.prevFilterWidth = this.filterWidth;
        this.mouseDragging = true;
    }

    @HostListener('window:mouseup', ['$event'])
    onMouseUp(event) {
        this.mouseDragging = false;
    }

    onResize(event) {
        this.mobWidth = window.innerWidth;
        this.mobileMode = this.mobWidth < 641;

        this.updateWidth();
    }

    /**
     * Update the width of the left side filters
     * @param filterMode expanded or collapsed
     */
    updateWidth(filterMode?: string){
        this.filterMode = filterMode? filterMode : this.filterMode;

        if(this.filterMode == 'normal'){
            this.filterToggler = 'expanded';
        }else{
            this.filterToggler = 'collapsed';
        }

        if(!this.mobileMode){
            if(this.filterMode == 'normal'){
                this.filterWidth = this.mobWidth / 4;
                this.filterToggler = 'expanded';
            }else{
                this.filterWidth = 39;
                this.filterToggler = 'collapsed';
            }
        }else{
            this.filterWidth = this.mobWidth - 40;
        }

        this.setResultWidth();
    }

    /**
     * Update the filter string
     * @param filterString 
     */
    updateFilterString(filterString: string) {
        this.filterString = filterString;
    }

    /**
     * Set the width of the right side result list panel
     * @returns 
     */
    setResultWidth(){
        if(this.mobWidth <= this.filterWidth){
            this.resultWidth = "100%";
        }else{
            this.resultWidth = this.mobWidth - this.filterWidth - 20;
        }
    }
}
