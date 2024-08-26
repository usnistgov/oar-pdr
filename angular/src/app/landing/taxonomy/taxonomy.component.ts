import { Component, EventEmitter, Input, OnInit, Output, SimpleChanges } from '@angular/core';
import {TreeNode} from 'primeng/api';
import { TaxonomyListService, SearchfieldsListService } from '../../shared/index';
import { trigger, state, style, animate, transition } from '@angular/animations';
import { Themes, ThemesPrefs, Collections, Collection, ColorScheme, CollectionThemes, FilterTreeNode } from '../../shared/globals/globals';

@Component({
  selector: 'app-taxonomy',
  templateUrl: './taxonomy.component.html',
  styleUrls: ['./taxonomy.component.css'],
  providers: [TaxonomyListService, SearchfieldsListService],
  animations: [
      trigger('expand', [
          state('closed', style({height: '0px'})),
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
    // collectionNodeExpanded: boolean = true;
    collectionShowMoreLink: boolean = false;
    collectionSelectedThemesNode: any[] = [];
    tempTotal: number = 0;
    totalNodes: number = 0;
    totalSelectedNodes: number = 0;
    allChecked: boolean = false;

    researchTopicStyle: any;

    @Input() collectionThemesTree: TreeNode[] = [];
    @Input() colorScheme: ColorScheme;
    @Input() collection: string = Collections.DEFAULT;
    @Input() isCollection: boolean = false;
    @Input() collectionNodeExpanded: boolean = false;
    @Input() clearAllCheckbox: boolean = false;
    @Output() filterString: EventEmitter<string> = new EventEmitter();
    
    constructor() { 

    }

    ngOnInit(): void {
        this.getTotlalNode(this.collectionThemesTree);
        this.totalNodes = this.tempTotal;

        if(this.colorScheme)
            this.researchTopicStyle = {'width':'100%','padding-top': '0.2em', 'padding-bottom': '.0em', 'background-color': this.colorScheme.lighter, 'overflow':'hidden','border-width':'0','margin-left': '-10px'};
    }

    ngAfterViewInit(): void {
        //Called after ngAfterContentInit when the component's view has been initialized. Applies to components only.
        //Add 'implements AfterViewInit' to the class.
        this.uncheckAll();
    }

    ngOnChanges(changes: SimpleChanges): void {
        if(this.clearAllCheckbox){
            this.uncheckAll();
        }
    }

    get isAllChecked() {
        let totalChecked = this.collectionSelectedThemesNode.length + 1;

        return ( totalChecked == this.totalNodes);
    }

    updateCheckbox() {
        if(this.allChecked) {
            this.checkAll();
        }else{
            this.uncheckAll();
        }
    }

    checkAll() {
        this.collectionSelectedThemesNode = [];
        if(this.collectionThemesTree && this.collectionThemesTree.length > 0)
            this.preselectNodes(this.collectionThemesTree[0].children);

        this.filterResults();
    }

    uncheckAll() {
        this.collectionSelectedThemesNode = [];
        this.filterResults();
    }

    preselectNodes(allNodes: TreeNode[]): void {
        for (let node of allNodes) {
            // let temp = JSON.parse(JSON.stringify(node));
            // temp.children = [];
            this.collectionSelectedThemesNode.push(node);
            if(node.children.length > 0) {
                this.preselectNodes(node.children);
            }
        }
    }

    totalNode(allNodes: TreeNode) {
        let that = this;
        if(!allNodes) return 0;

        if(allNodes.children.length > 0){
            that.tempTotal += 1;
            for(let child of allNodes.children){
                this.totalNode(child);
            }
        }else{
            that.tempTotal += 1;
        }
    }

    getTotlalNode(nodes: TreeNode[]) {
        this.tempTotal = 0;

        if(nodes && nodes.length > 0){
            for(let node of nodes) {
                this.totalNode(node);
            }
        }

        return this.tempTotal;
    }

    /**
     * Form the filter string and refresh the result page
     */
    filterResults() {
        this.allChecked = this.isAllChecked;
        let lFilterString: string = "";
        let themeSelected: boolean = false;
        // let themeType = '';

        // Collection Research topics
        
            if (this.collectionSelectedThemesNode.length > 0) {
                for (let theme of this.collectionSelectedThemesNode) {
                    if (theme != 'undefined' && typeof theme.data !== 'undefined' && theme.data[0] !== 'undefined') {
                        themeSelected = true;
                        for(let i = 0; i < theme.data.length; i++ ){
                            if(this.isCollection) {
                                // themeType += theme.data[i] + ',';
                                lFilterString += this.collection + "----" + theme.data[i].trim() + ",";
                            }else{
                                lFilterString += theme.data[i].trim().replace(/\s/g, "") + ",";
                            }
                        }
                    }
                }
            }

            lFilterString = this.removeEndingComma(lFilterString);
            if(!lFilterString) lFilterString = "";
            else {
                if(this.isCollection) {
                    lFilterString = "topic.tag=" + lFilterString;
                }else{
                    lFilterString = this.collection + "=" + lFilterString;
                }
            } 

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
    
    expandIcon() {
        if(!this.collectionNodeExpanded){
            return "pi pi-chevron-right";
        }else{
            return "pi pi-chevron-down"
        }
    }

    /**
     * Return tooltip text for given filter tree node.
     * @param filternode tree node of a filter
     * @returns tooltip text
     */
    filterTooltip(filternode: any) {
        if(filternode && filternode.label)
            return filternode.label.split('-')[0] + "-" + filternode.count;
        else
            return "";
    }    

    /**
     * Only expand the filter window if user close the first level 
     * @param level node level
     */
    onNodeExpand(event) {
        if(event.node.level == 1)
            this.collectionNodeExpanded = true;
    }

    /**
     * Only collapse the filter window if user close the first level 
     * @param level node level
     */
    onNodeCollapse(event) {
        if(event.node.level == 1)
            this.collectionNodeExpanded = false;
    }
}
