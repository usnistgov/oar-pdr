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
    data: string = "";
    label: string = "";
    expanded = false;
    keyname: string = '';
    parent = null;
    
    constructor(label: string='', expanded: boolean = false, key: string=null, data: string = '') {
        this.label = label;
        this.data = data;
        this.keyname = key;
        if(!key) this.keyname = label;
    }

   /**
     * insert or update a node within this tree corresponding to the given data cart item
     * @return CartTreeNode   the node that was inserted or updated
     */
    upsertNodeFor(item: any[]) : TreeNode {
        let levels = item[0].split(":");
        for(let i = 0; i < levels.length; i++) {
            levels[i] = levels[i].trim();
        }
        return this._upsertNodeFor(levels, item);
    }

    _upsertNodeFor(levels: string[], item: any[]) : TreeNode {
        // find the node corresponding to the given item in the data cart 
        for (let child of this.children) {
            if (child.keyname == levels[0]) {
                if (levels.length > 1)
                    return child._upsertNodeFor(levels.slice(1), item);
                else {
                    // child.updateData(item);
                    child.label = levels[0] + "---" + item[1];
                    child.count = item[1];
                    child.data = levels[0];
                    return child;
                }
            }
        }

        // ancestor does not exist yet; create it
        // let key = (this.keyname) ? this.keyname + '/' + levels[0] : levels[0];
        let key = levels[0];
        let label = levels[0];
        let data = levels[0];
        let count = 0;
        if (levels.length == 1) {
            count =  item[1];
            label += "---" + item[1]; 
        }
        let child = new FilterTreeNode(label, false, key, data);
        child.parent = this;
        this.children = [...this.children, child];
        if (levels.length > 1)
            return child._upsertNodeFor(levels.slice(1), item);

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