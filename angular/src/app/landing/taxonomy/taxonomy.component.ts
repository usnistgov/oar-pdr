import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import {TreeNode} from 'primeng/api';
import { TaxonomyListService, SearchfieldsListService } from '../../shared/index';
import { trigger, state, style, animate, transition } from '@angular/animations';

@Component({
  selector: 'app-taxonomy',
  templateUrl: './taxonomy.component.html',
  styleUrls: ['./taxonomy.component.css'],
  providers: [TaxonomyListService, SearchfieldsListService],
  animations: [
      trigger('expand', [
          state('closed', style({height: '50px'})),
          state('collapsed', style({height: '183px'})),
          state('expanded', style({height: '*'})),
          transition('expanded <=> collapsed', animate('625ms')),
          transition('expanded <=> closed', animate('625ms')),
          transition('closed <=> collapsed', animate('625ms'))
      ]),
      trigger('expandOptions', [
          state('collapsed', style({height: '0px'})),
          state('expanded', style({height: '*'})),
          transition('expanded <=> collapsed', animate('625ms'))
      ]),
      trigger('filterExpand', [
          state('collapsed', style({width: '40px'})),
          state('expanded', style({height: '*'})),
          transition('expanded <=> collapsed', animate('625ms'))
      ])
  ]
})
export class TaxonomyComponent implements OnInit {
    collectionNodeExpanded: boolean = true;
    collectionShowMoreLink: boolean = false;
    collectionSelectedThemesNode: any[] = [];

    researchTopicStyle = {'width':'100%','padding-top': '.5em', 'padding-bottom': '.5em', 'background-color': 'var(--science-theme-background-light)', 'overflow':'hidden','border-width':'0'};

    @Input() collectionThemesTree: TreeNode[] = [];
    @Input() backgroundColor: string = "white";
    @Input() defaultColor: string = "black";
    @Output() filterString: EventEmitter<string> = new EventEmitter();
    
    constructor() { 
    }

    ngOnInit(): void {
        console.log("collectionThemesTree", this.collectionThemesTree);
    }

    /**
     * Form the filter string and refresh the result page
     */
    filterResults() {
        let lFilterString: string = "";
        let themeSelected: boolean = false;
        let themeType = '';

        // Collection Research topics
        if (this.collectionSelectedThemesNode.length > 0) {
            for (let theme of this.collectionSelectedThemesNode) {
                if (theme != 'undefined' && typeof theme.data !== 'undefined' && theme.data !== 'undefined') {
                    themeSelected = true;
                    this.collectionSelectedThemesNode.push(theme.data);
                    themeType += theme.data + ',';

                    lFilterString += theme.data.trim() + ",";
                }
            }
        }

        lFilterString = this.removeEndingComma(lFilterString);
        if(!lFilterString) lFilterString = "";
        else lFilterString = "topic.tag=" + lFilterString;

        this.filterString.emit(lFilterString);
    }

    /**
     * Remove the ending comma of the given string
     * @param inputrString 
     */
    removeEndingComma(inputrString: string): string{
        if(!inputrString) return "";

        if(inputrString[inputrString.length-1] == ",")
            return inputrString.substr(0, inputrString.length-1);
        else    
            return inputrString;
    }  
    
    /**
     * Return tooltip text for given filter tree node.
     * @param filternode tree node of a filter
     * @returns tooltip text
     */
    filterTooltip(filternode: any) {
        if(filternode && filternode.label)
            return filternode.label.split('-')[0] + "-" + filternode.label.split('-')[1];
        else
            return "";
    }    
}