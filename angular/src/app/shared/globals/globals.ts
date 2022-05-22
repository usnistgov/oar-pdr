export class Themes {
    static readonly SCIENCE_THEME = 'ScienceTheme';
    static readonly DEFAULT_THEME = 'DefaultTheme';
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