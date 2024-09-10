import { SelectItem, TreeNode } from 'primeng/api';

export class Themes {
    static readonly SCIENCE_THEME = 'ScienceTheme';
    static readonly DEFAULT_THEME = 'DefaultTheme';
}

export class Collections {
    static readonly DEFAULT = 'NIST';
    static readonly FORENSICS = 'Forensics';
    static readonly SEMICONDUCTORS = 'Semiconductors';
}

let _theme = {};
_theme[Themes.SCIENCE_THEME] = "ScienceTheme";
_theme[Themes.DEFAULT_THEME] = "DefaultTheme";

let _sourceLabel = {};
_sourceLabel[Themes.SCIENCE_THEME] = "Collection";
_sourceLabel[Themes.DEFAULT_THEME] = "Dataset";

export class ThemesPrefs {
    private static readonly _lTheme = _theme;
    private static readonly _lSourceLabel = _sourceLabel;

    public static getTheme(type: string) {
        if(! type || type == '') {
            return ThemesPrefs._lTheme[Themes.DEFAULT_THEME]
        }

        if(! ThemesPrefs._lTheme[type]) {
            return ThemesPrefs._lTheme[Themes.DEFAULT_THEME]
        }

        return ThemesPrefs._lTheme[type]
    }

    public static getResourceLabel(theme: string) {
        if(! theme || theme == '') {
            return ThemesPrefs._lSourceLabel[Themes.DEFAULT_THEME]
        }

        if(! ThemesPrefs._lSourceLabel[theme]) {
            return ThemesPrefs._lSourceLabel[Themes.DEFAULT_THEME]
        }

        return ThemesPrefs._lSourceLabel[theme]
    }
}

/**
 * A TreeNode that knows how to insert and update items from a data cart
 */
export class FilterTreeNode implements TreeNode {
    children = [];
    count: number = 0;
    data: string[] = [];
    label: string = "";
    ediids: string[] = [];
    expanded = false;
    keyname: string = '';
    parent = null;
    level: number = 1;
    selectable: boolean = true;
    unspecified: boolean[] = [];
    
    constructor(label: string='', expanded: boolean = false, key: string=null, data: string = '', count: number = 0, selectable: boolean = true, level: number = 1) {
        this.label = label;
        if(data && !this.data.includes(data))
            this.data.push(data);
        this.count = count;
        this.selectable = selectable;
        this.level = level;
        this.keyname = key;
        if(!key) this.keyname = label;
    }

   /**
     * insert or update a node within this tree corresponding to the given data cart item
     * @return CartTreeNode   the node that was inserted or updated
     */
    upsertNodeFor(item: any[], level:number = 1, searchResults: any = null, collection: string = null, taxonomyURI: any = {}) : TreeNode {
        let levels = item[0].split(":");
        for(let i = 0; i < levels.length; i++) {
            levels[i] = levels[i].trim();
        }
        
        return this._upsertNodeFor(levels, item, level, searchResults, collection, taxonomyURI);
    }

    _upsertNodeFor(levels: string[], item: any[], level: number = 1, searchResults: any = null, collection: string=null, taxonomyURI: any = {}) : TreeNode {
        let nodeLabel: string = ''; 
        // find the node corresponding to the given item in the data cart 
        for (let child of this.children) {
            if (child.keyname == levels[0]) {
                if(searchResults) {
                    for (let resultItem of searchResults) {
                        let found: boolean = false;
                        if(resultItem.topic && resultItem.topic.length > 0){
                            for(let topic of resultItem.topic) {
                                if(topic['scheme'].indexOf(taxonomyURI[collection]) >= 0) {
                                    if(collection == Collections.DEFAULT) {
                                        if(topic.tag.includes(item[0])) {
                                            found = true;
                                            break;
                                        }
                                    }else{
                                        if(topic.tag == item[0]) {
                                            found = true;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
    
                        if(found){
                            if(!child.ediids.includes(resultItem.ediid)){
                                child.ediids.push(resultItem.ediid);
                                child.count++;
                            }
                        }        
                    }
                }

                if (levels.length > 1){
                    return child._upsertNodeFor(levels.slice(1), item, level+1, searchResults, collection, taxonomyURI);
                }else {
                    child.label = levels[0] + "---" + item[1];
                    if(!child.data.includes(item[0]))
                        child.data.push(item[0]);

                    return child;
                }
            }
        }

        // ancestor does not exist yet; create it
        let key = levels[0];
        let label = levels[0];
        let data = item[0];

        let count = 0;
        if (levels.length == 1) {
            label += "---" + item[1]; 
        }

        if(levels[0] == "Unspecified") {
            count = item[1];
        }

        let child = new FilterTreeNode(label, false, key, data, count, true, level+1);
        child.parent = this;
        this.children = [...this.children, child];

        //Add only unique dataset to the count
        if(searchResults) {
            for (let resultItem of searchResults) {
                let found: boolean = false;
                if(resultItem.topic && resultItem.topic.length > 0){
                    for(let topic of resultItem.topic) {
                        if(topic['scheme'].indexOf(taxonomyURI[collection]) >= 0) {
                            if(collection == Collections.DEFAULT) {
                                if(topic.tag.includes(data)) {
                                    found = true;
                                    break;
                                }
                            }else{
                                if(topic.tag == data) {
                                    found = true;
                                    break;
                                }
                            }
                        }
                    }
                }

                if(found){
                    if(!child.ediids.includes(resultItem.ediid)){
                        child.ediids.push(resultItem.ediid);
                        child.count++;
                    }
                }        
            }
        }

        if (levels.length > 1){
            return child._upsertNodeFor(levels.slice(1), item, level+1, searchResults, collection, taxonomyURI);
        }
        return child;
    }    
}

export class Collection {
    bannerUrl: string;
    taxonomyURI: string;
    color: ColorScheme;
    theme: CollectionThemes;
}

export interface ColorScheme {
    default: string;
    light: string;
    lighter: string;
    dark: string;
    hover: string;
}

export interface CollectionThemes {
    collectionThemes: SelectItem[];
    collectionThemesAllArray: string[];
    collectionUnspecifiedCount: number;
    collectionUniqueThemes: string[];
    collectionThemesWithCount: FilterTreeNode[];
    collectionThemesTree: FilterTreeNode[];
    collectionShowMoreLink: boolean;
    collectionSelectedThemesNode: any[];
}