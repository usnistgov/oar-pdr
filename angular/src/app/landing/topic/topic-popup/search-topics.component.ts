import { Component, OnInit, Input, EventEmitter, Output, ElementRef, ViewChild } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { TreeNode } from 'primeng/api';
import { TemplateBindingParseResult, preserveWhitespacesDefault } from '@angular/compiler';
import { AppConfig } from '../../../config/config';
import { TaxonomyListService } from '../../../shared/taxonomy-list';
import { UserMessageService } from '../../../frame/usermessage.service';

export const ROW_COLOR = '#1E6BA1';

@Component({
  selector: 'app-search-topics',
  templateUrl: './search-topics.component.html',
  styleUrls: ['./search-topics.component.css']
})
export class SearchTopicsComponent implements OnInit {
  @Input() inputValue: any;
  @Input() field: any;
  @Input() title?: string;
  @Output() returnValue: EventEmitter<any> = new EventEmitter();

  isVisible: boolean = true;
  scrollTop: number = 0;
  searchText: string = "";
  highlight: string = "";
  taxonomyList: any[];
  taxonomyTree: TreeNode[] = [];

  @ViewChild('panel', { read: ElementRef }) public panel: ElementRef<any>;
  @ViewChild('panel0', { read: ElementRef }) public panel0: ElementRef<any>;

  constructor(
    private taxonomyListService: TaxonomyListService,
    private msgsvc: UserMessageService,
    public activeModal: NgbActiveModal) { }

  ngOnInit() {
    this.taxonomyListService.get(0).subscribe((result) => {
      if (result != null && result != undefined)
          this.buildTaxonomyTree(result);

      this.taxonomyList = [];
      for (var i = 0; i < result.length; i++) {
          this.taxonomyList.push({ "taxonomy": result[i].label });
      }

      this.setTreeVisible(true);

    }, (err) => {
        console.error("Failed to load taxonomy terms from server: "+err.message);
        this.msgsvc.warn("Failed to load taxonomy terms; you may have problems editing the "+
                        "topics assigned to this record.");
    });
  }

  /*
    *   build taxonomy tree
    */
  buildTaxonomyTree(result: any) {
    let allTaxonomy: any = result;
    var tempTaxonomyTree = {}
    if (result != null && result != undefined) {
        tempTaxonomyTree["data"] = this.arrangeIntoTaxonomyTree(result);
        this.taxonomyTree.push(tempTaxonomyTree);
    }

    this.taxonomyTree = <TreeNode[]>this.taxonomyTree[0].data;
  }

  private arrangeIntoTaxonomyTree(paths) {
      const tree = [];
      paths.forEach((path) => {
          var fullpath: string;
          if (path.parent != null && path.parent != undefined && path.parent != "")
              fullpath = path.parent + ":" + path.label;
          else
              fullpath = path.label;

          const pathParts = fullpath.split(':');
          let currentLevel = tree; // initialize currentLevel to root

          for (var j = 0; j < pathParts.length; j++) {
              let tempId: string = '';
              for (var k = 0; k < j + 1; k++) {
                  tempId = tempId + pathParts[k];
                  // tempId = tempId + pathParts[k].replace(/ /g, "");
                  if (k < j) {
                      tempId = tempId + ": ";
                  }
              }

            // check to see if the path already exists.
            const existingPath = currentLevel.filter(level => level.data.treeId === tempId);
            if (existingPath.length > 0) {
                // The path to this item was already in the tree, so don't add it again.
                // Set the current level to this path's children  
                currentLevel = existingPath[0].children;
            } else {
                let newPart = null;
                newPart = {
                    data: {
                        treeId: tempId,
                        name: pathParts[j],
                        researchTopic: tempId,
                        bkcolor: 'white'
                    }, children: [],
                    expanded: false
                };
                currentLevel.push(newPart);
                currentLevel = newPart.children;
            }
          };
      });
      return tree;
  }

  /* 
  *   Save contact info when click on save button in pop up dialog
  */
  saveTopic() {
    this.returnValue.emit(this.inputValue);
    this.activeModal.close('Close click');
  }

  /**
   * Delete a topic
   */
  deleteTopic(index: number) {
    this.setTreeVisible(true);
    this.searchAndExpandTaxonomyTree(this.inputValue[this.field][index], false);
    this.inputValue[this.field] = this.inputValue[this.field].filter(topic => topic != this.inputValue[this.field][index]);
    this.refreshTopicTree();
    console.log('this.inputValue.length', this.inputValue[this.field].length);
  }

  /**
   * Update the topic list
   */
  updateTopics(rowNode: any) {
    const existingTopic = this.inputValue[this.field].filter(topic => topic == rowNode.node.data.researchTopic);
    if (existingTopic == undefined || existingTopic == null || existingTopic.length == 0) {
      this.inputValue[this.field].push(rowNode.node.data.researchTopic);

      // Reset search text box
      if (this.searchText != "") {
        this.searchText = "";
        this.onSearchTextChange();
      }
    }
  }

  /*
  *   Set text color if the given topic already exists
  */
  getTopicColor(rowNode: any) {
    // console.log("this.tempTopics", this.tempTopics);
    const existingTopic = this.inputValue[this.field].filter(topic => topic == rowNode.node.data.researchTopic);
    if (existingTopic == undefined || existingTopic == null || existingTopic.length <= 0) {
      return ROW_COLOR;
    } else {
      return 'lightgrey';
    }
  }

  /*
  *   Set cursor type
  */
  getTopicCursor(rowNode: any) {
    const existingTopic = this.inputValue[this.field].filter(topic0 => topic0 == rowNode.node.data.researchTopic);
    if (existingTopic == undefined || existingTopic == null || existingTopic.length <= 0)
      return 'pointer';
    else
      return 'default';
  }

  searchAndExpandTaxonomyTree(topic: string, option: boolean) {
    var index: number;

    this.expandTree(this.taxonomyTree, false);
    this.setTreeVisible(true, 'white');
    // First hide all tree node
    // this.setTreeVisible(false);
    this.resetTreeBackColor(this.taxonomyTree);
    var treeNode: TreeNode = null;
    for (let i = 0; treeNode == null && i < this.taxonomyTree.length; i++) {
      treeNode = this.searchTreenode(this.taxonomyTree[i], topic);
    }
    if (treeNode != null) {
      if (treeNode.parent != null)
        this.setVisible(treeNode.parent.children, true);

      treeNode.data.visible = true;
      if (option)
        treeNode.data.bkcolor = 'lightyellow';
      else
        treeNode.data.bkcolor = 'white';
    }

    if (option) {
      var child = treeNode;
      while (treeNode != null) {
        if (treeNode.parent != null) {
          treeNode.parent.expanded = true;
          treeNode.parent.data.visible = true;
        }
        child = treeNode;
        treeNode = treeNode.parent;
      }

      index = this.taxonomyTree.findIndex(x => x === child);
    }

    this.isVisible = false;
    setTimeout(() => {
      this.isVisible = true;
    }, 0);

    setTimeout(() => {
      this.panel0.nativeElement.scrollTop = index * 40;
    }, 1);

  }

  rowVisibility(rowData: any) {
    if (rowData.visible)
      return "block";
    else
      return "none";
  }

  setTreeVisible(visible: boolean, backgroundColor?: string) {
    this.setVisible(this.taxonomyTree, visible, backgroundColor);
  }

  setVisible(tree: TreeNode[], option: boolean, backgroundColor?: string) {
    if (tree == undefined || tree == null) return;

    for (let i = 0; i < tree.length; i++) {
      if (tree[i].data != null && tree[i].data != undefined) {
        tree[i].data.visible = option;
        if (backgroundColor != null)
          tree[i].data.bkcolor = backgroundColor;
      }

      if (tree[i].children != null && tree[i].children != undefined && tree[i].children.length > 0) {
        this.setVisible(tree[i].children, option, backgroundColor);
      }
    }
  }

  /*
  *   Refresh the taxonomy tree 
  */
  refreshTopicTree() {
    this.isVisible = false;
    setTimeout(() => {
      this.isVisible = true;
    }, 0);
  }

  /*
  *   Expand/collapse treenodes
  */
  expandTree(tree: TreeNode[], option: boolean) {
    for (let i = 0; i < tree.length; i++) {
      tree[i].expanded = option;
      if (tree[i].children.length > 0) {
        this.expandTree(tree[i].children, option);
      }
    }
  }

  /*
  *   Expand/collapse treenodes
  */
  resetTreeBackColor(tree: TreeNode[]) {
    for (let i = 0; i < tree.length; i++) {
      tree[i].data.bkcolor = 'white';
      if (tree[i].children.length > 0) {
        this.resetTreeBackColor(tree[i].children);
      }
    }
  }

  /*
  *   search treeNode
  */
  searchTreenode(tree: TreeNode, topic: string) {
    if (tree.data.researchTopic == topic) {
      return tree;
    } else if (tree.children != null) {
      var i;
      var result = null;
      for (i = 0; result == null && i < tree.children.length; i++) {
        result = this.searchTreenode(tree.children[i], topic);
      }
      return result;
    }
    return null;
  }

  /*
  *   Return row background color
  */
  rowBackColor(rowData: any) {
    if (this.highlight == "") {
      if (rowData == null || rowData == undefined)
        return "white";
      else
        return rowData.bkcolor;
    } else {
      if (this.highlight == rowData.name) {
        return "#cccccc";
      }
    }
  }

  /*
   *   Return row background color
   */
  rowColor(rowNode: any) {
    if (this.highlight == "") {
      return this.getTopicColor(rowNode);
    } else {
      if (this.highlight == rowNode.node.data.name) {
        return "white";
      } else {
        return this.getTopicColor(rowNode);
      }
    }
  }

  /*
  *   Display all topics
  */
  showAllTopics() {
      this.searchText = "";
    this.setTreeVisible(true);
    this.expandTree(this.taxonomyTree, false);

    this.isVisible = false;
    setTimeout(() => {
      this.isVisible = true;
    }, 0);
  }

  /*
  *   When user changes the search text
  */
  onSearchTextChange() {
    var tree: any;
    this.setTreeVisible(false, 'white');
    this.expandTree(this.taxonomyTree, true);
    for (var i = 0; i < this.taxonomyTree.length; i++)
      this.setTreenodeVisible(this.taxonomyTree[i], this.searchText);

    this.refreshTopicTree();
  }

  /*
  *   search treeNode, if found set visible to true
  */
  setTreenodeVisible(tree: TreeNode, topic: string) {
    if (tree.data.researchTopic.toLowerCase().indexOf(topic.toLowerCase()) > -1) {
      if (tree != null) {
        tree.data.bkcolor = "#E7FFFE";
        if (tree.parent == null) {
          tree.data.visible = true;
          this.setVisible(tree.children, true);
        }
        else {
          tree.parent.data.visible = true;
          this.setVisible(tree.parent.children, true);
        }
      }
      return tree;
    } else if (tree.children != null) {
      var result = null;
      for (var i = 0; result == null && i < tree.children.length; i++) {
        this.setTreenodeVisible(tree.children[i], topic);
      }
    }
    return tree;
  }

  /*
   *   This function is used to track ngFor loop
   */
  trackByFn(index: any, author: any) {
    return index;
  }

  setHighlight(rowData: any) {
    if (rowData == "")
      this.highlight = "";
    else
      this.highlight = rowData.name;
  }
}
