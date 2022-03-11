import { Component, OnInit, Input } from '@angular/core';
import { NerdmRes, NERDResource } from '../../nerdm/nerdm';
import { trigger, state, style, animate, transition } from '@angular/animations';


@Component({
  selector: 'app-searchresult',
  templateUrl: './searchresult.component.html',
  styleUrls: ['./searchresult.component.css'],
  animations: [
    trigger('filterStatus', [
    state('collapsed', style({width: '30px'})),
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
    searchTaxonomyKey: string;
    page: number = 1;
    filterToggler: string = 'expanded';
    filterString: string = "";

    @Input() record: NerdmRes = null;
    @Input() inBrowser: boolean = false;
    @Input() theme: string = 'nist';

    constructor() {
     }

    ngOnInit(): void {
    }

    onResize(event) {
        this.mobWidth = window.innerWidth;
        this.mobileMode = this.mobWidth < 641;

        this.updateWidth();
    }

    updateWidth(filterMode?: string){
        this.filterMode = filterMode? filterMode : this.filterMode;

        if(this.filterMode == 'normal'){
            this.filterToggler = 'expanded';
        }else{
            this.filterToggler = 'collapsed';
        }

        if(this.mobWidth > 641){
            if(this.filterMode == 'normal'){
                this.filterWidth = this.mobWidth / 4;
                this.filterToggler = 'expanded';
            }else{
                this.filterWidth = 40;
                this.filterToggler = 'collapsed';
            }
        }else{
            this.filterWidth = this.mobWidth;
        }
    }

    /**
     * 
     * @param filterString 
     */
    updateFilterString(filterString: string) {
        this.filterString = filterString;
    }

    getDisplayStyle(){
        if(this.mobWidth == this.filterWidth){
            return "normal";
        }else{
            return "flex";
        }
    }

    resultWidth(){
        if(this.mobWidth == this.filterWidth){
            return this.filterWidth;
        }else{
            return this.mobWidth - this.filterWidth - 20;
        }
    }
}
