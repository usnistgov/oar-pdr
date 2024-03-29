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
    collectionThemesWithCount: TreeNode[];
    collectionThemesTree: TreeNode[];
    collectionShowMoreLink: boolean;
    collectionSelectedThemesNode: any[];
}