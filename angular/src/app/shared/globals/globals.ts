export class Themes {
    static readonly SCIENCE_THEME = 'ScienceTheme';
    static readonly DEFAULT_THEME = 'DefaultTheme';
}

export class Collections {
    static readonly DEFAULT = 'Default';
    static readonly DEFAULT_NAME = 'default';
    static readonly FORENSICS = 'Forensics';
    static readonly FORENSICS_NAME = 'forensics';
    static readonly SEMICONDUCTORS = 'Semiconductors';
    static readonly SEMICONDUCTORS_NAME = 'Semiconductors';
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

export class ColorDef {
    static readonly DEFAULT = 'default';
    static readonly DARK = 'Dark';
    static readonly LIGHT = 'light';
    static readonly LIGHT2 = 'lights';
    static readonly DARK_HOVER = 'dark-hover';
}

let _color = {};
_color[ColorDef.DEFAULT] = "-background-default";
_color[ColorDef.DARK] = "-background-dark";
_color[ColorDef.LIGHT] = "-background-light";
_color[ColorDef.LIGHT2] = "-background-light2";
_color[ColorDef.DARK_HOVER] = "-background-dark-hover";

export class ColorPrefs {
    private static readonly _lColor = _color;

    public static getColorStr(collection: string, color: string) {
        return "var(--" + collection.toLowerCase() + ColorPrefs._lColor[color] + ")";
    }    
}

export class Collection {
    bannerUrl: string;
    taxonomyURI: string;
    color: ColorScheme;
}

export interface ColorScheme {
    default: string;
    light: string;
    lighter: string;
    dark: string;
    hover: string;
}