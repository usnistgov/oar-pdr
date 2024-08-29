import { Component, Input, OnInit } from '@angular/core';
import { ColorScheme } from '../../shared/globals/globals';
import { trigger, state, style, animate, transition } from '@angular/animations';

@Component({
  selector: 'app-resultitem',
  templateUrl: './resultitem.component.html',
  styleUrls: ['./resultitem.component.css'],
  animations: [
    trigger('detailExpand', [
    state('void', style({height: '*', minHeight: '0'})),
    state('collapsed', style({height: '*', minHeight: '0'})),
    state('expanded', style({height: '*'})),
    transition('expanded <=> collapsed', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    transition('expanded <=> void', animate('625ms cubic-bezier(0.4, 0.0, 0.2, 1)')),
    ]),
    trigger(
        'enterAnimation', [
            transition(':enter', [
                style({height: '0px', opacity: 0}),
                animate('700ms', style({height: '100%', opacity: 1}))
            ]),
            transition(':leave', [
                style({height: '100%', opacity: 1}),
                animate('700ms', style({height: 0, opacity: 0}))
            ])
        ]
    )
  ] 
})
export class ResultitemComponent implements OnInit {
    titleIconClass: string;
    homeBtnURL: string;
    contentShort: string = "";
    expanded: boolean = false;

    @Input() resultItem: any;
    @Input() PDRAPIURL: string = "https://data.nist.gov/lps/";
    @Input() colorScheme: ColorScheme;

    constructor() { }

    ngOnInit(): void {


      if(this.resultItem.landingPage) {
        this.homeBtnURL = this.resultItem.landingPage;

        if(this.resultItem.landingPage.indexOf(this.resultItem.ediid.split("/").at(-1)) >= 0) {
          this.titleIconClass = "faa faa-link vertical-center";
        } else {
          this.titleIconClass = "faa faa-external-link vertical-center";
        }
      }else{
        this.homeBtnURL = this.PDRAPIURL + this.resultItem.ediid;
        this.titleIconClass = "faa faa-external-link vertical-center";
      }

      if(this.resultItem.description)
        this.contentShort = this.resultItem.description[0].substring(0, 200) + "...";
    }

    /**
     * Determine if a given dataset has contact point email
     * @param dataset 
     * @returns 
     */
    hasEmail(dataset: any) {
      if(dataset['contactPoint'])
          return 'hasEmail' in dataset['contactPoint'];
      else
          return false;
  }    

  /**
   * Get the doi url from the given dataset. If not available, return blank.
   * @param dataset 
   * @returns doi url. Return blank if not available.
   */
  doiUrl(dataset: any) {
    if (dataset['doi'] !== undefined && dataset['doi'] !== "")
        return "https://doi.org/" + dataset['doi'].substring(4);
    else    
        return "";
  }

  lastModified(dataset: any) {
    let lastDate: Date;
    if(dataset.modified) {
        lastDate = new Date(dataset.modified.slice(0,10));
        return lastDate.toLocaleDateString();
    }else{
        return "None";
    }
  }

  toggleDetails() {
    this.expanded = !this.expanded;
  }
}
