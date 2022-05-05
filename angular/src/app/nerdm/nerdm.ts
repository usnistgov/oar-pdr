/**
 * Classes and interfaces to support the NERDm metadata infrastructure
 */
import { Injectable, InjectionToken } from '@angular/core';
import { Themes, ThemesPrefs } from '../shared/globals/globals';
import * as _ from 'lodash-es';

/**
 * a representation of a NERDm Component
 */
export interface NerdmComp {
    
    /**
     * the primary, local identifier for the resource
     */
    "@type" : string[];

    /**
     * the primary, local identifier for the resource
     */
    "@id"? : string;

    /**
     * the title of the component
     */
    title? : string;

    /**
     * the path to the component within a file hierarchy.  This is only applicable to 
     * DataFile and Subcollection components.
     */
    filepath? : string;

    /**
     * other parameters are expected
     */
    [propName: string]: any;
}

/**
 * a representation of a NERDm Resource 
 */
export interface NerdmRes {

    /**
     * the primary, local identifier for the resource
     */
    "@id" : string;

    /**
     * the title of the resource
     */
    title : string;

    /**
     * the list of components that are part of this resource
     */
    components? : NerdmComp[];

    /**
     * other parameters are expected
     */
    [propName: string]: any;
}

/**
 * a class interpreting a NerdmRes record.  This class wraps a NerdmRes object in an 
 * interface that provides functions that generate views on that information useful to 
 * displaying it.
 */
export class NERDResource {

    /**
     * wrap a NerdRes record (the data that describes a data resource)
     */
    constructor(public data : NerdmRes) { }

    /**
     * return the recommend text for citing this resource
     */
    getCitation() : string {
      if(this.data != null){
        if (this.data['citation'])
            return this.data.citation;

        let out = ""
        if (this.data['authors']) {
            for (let i = 0; i < this.data['authors'].length; i++) {
                let author = this.data['authors'][i];
                if (author.familyName !== null && author.familyName !== undefined)
                    out += author.familyName + ', ';
                if (author.givenName !== null && author.givenName !== undefined)
                    out += author.givenName;
                if (author.middleName !== null && author.middleName !== undefined)
                    out += ' ' + author.middleName;
                if (i != this.data['authors'].length - 1)
                    out += ', ';
            }
        }
        else if (this.data['contactPoint'] && this.data['contactPoint']['fn']) {
            out += this.data['contactPoint']['fn'];
        }
        else if (this.data['publisher'] && this.data['publisher']['name']) {
            out += this.data['publisher']['name'];
        }
        else {
            out += "National Institute of Standards and Technology";
        }

        let date = this.data['issued'];
        if (! date)
            date = this.data['modified'];
        if (date)
            out += ' (' + date.split('-')[0] + ')';

        if (this.data['title'])
            out += ', ' + this.data['title'];
        if (this.data['publisher'] && this.data['publisher']['name']) 
            out += ', ' + this.data['publisher']['name'];

        if (this.data['doi']) {
            let doi = this.data['doi'];
            if (doi.startsWith("doi:"))
                doi = "https://doi.org/" + doi.split(':').slice(1).join(':')
            out += ', ' + doi;
        }
        else if (this.data['landingPage']) {
            out += ', ' + this.data['landingPage'];
        }

        date = new Date();
        out += " (Accessed " + date.getFullYear() + '-'
        let n = date.getMonth() + 1;
        n = (n < 10) ? "0" + n.toString() : n.toString();
        out += n + '-';
        n = date.getDate();
        n = (n < 10) ? "0" + n.toString() : n.toString();
        out += n + ')';
        
        return out;
      }
      else
      {
        return "";
      }
    }

    static _isstring(v : any, i?, a?) : boolean {
        return typeof v === 'string' || v instanceof String;
    }
    static _stripns(t : string, i?, a?) : string {
        return t.substr(t.indexOf(':')+1);
    }
    static _striptypes(cmp : {}, typeprop : string = "@type") : string[] {
        if (! cmp[typeprop]) return [];

        let out = cmp[typeprop]
        if (this._isstring(out)) out = [ out ];
        if (! Array.isArray(out)) return []

        return out.filter(this._isstring).map(this._stripns).sort()
    }
    static _typesintersect(obj : {}, types : string[], typeprop : string = "@type") : boolean {
        // we will assume that types is strictly an ordered array of strings
        let ctypes : string[] = this._striptypes(obj, typeprop).sort();

        for(var c of ctypes) {
            for(var t of types) {
                if (t == c) return true;  // found a matching type!
                if (t > c) break;
            }
        }
        return false;
    }

    /**
     * return true if there is an intersection between a given set of types
     * and the values in the "@type" property of a given object
     * @param obj    an object with the "@type" property; false will be returned 
     *               if the property does not exist or if it is not of type string 
     *               or array.
     * @param types  a string or an array of string type labels.  Any prepended 
     *               namespace prefixes will be ignored.  
     */
    static objectMatchesTypes(obj : {}, types : string|string[]) : boolean {
        if (this._isstring(types)) types = [types as string]
        if (! Array.isArray(types)) return false;
        types = types.filter(this._isstring).map(this._stripns).sort();

        return this._typesintersect(obj, types, "@type");
    }

    /**
     * return True if one of the @types assigned to this resource matches the resource
     * type given
     * @param type   a resource type label (like "DataPublication" or "ScienceTheme").  The 
     *               value may include a namespace prefix, which is ignored.
     * @return boolean   True if the given type matches one of the assigned types
     */
    isType(restype: string) : boolean {
        return NERDResource.objectMatchesTypes(this, restype);
    }

    /**
     * return an array of the component objects that match any of the given @type labels.
     * The labels should not include namespace qualifiers
     */
    getComponentsByType(types : string|string[]) : any[] {
        if (! this.data['components'] || !Array.isArray(this.data['components']))
            return [];

        if (NERDResource._isstring(types)) types = [types as string]
        if (! Array.isArray(types)) return [];
        types = types.filter(NERDResource._isstring).map(NERDResource._stripns).sort();

        return this.data['components'].filter((c,i?,a?) => {
            return NERDResource._typesintersect(c, types as string[], "@type");
        });
    }

    /**
     * return the number resource components that match any of the given @type labels.  
     * The labels should not include namespace qualifiers
     */
    countComponentsByType(types : string|string[]) {
        return this.getComponentsByType(types).length;
    }

    /**
     * return the components that should appear in the file listing display
     */
    getFileListComponents() {
        let listable = ["DataFile", "Subcollection", "ChecksumFile"];
        let hidden = ["Hidden"];
        return this.getComponentsByType(listable)
            .filter((c) => { return ! NERDResource.objectMatchesTypes(c, hidden); });
    }

    /**
     * return the number of components that should appear in the file listing display
     */
    countFileListComponents() {
        return this.getFileListComponents().length;
    }

    /**
     * return a list of reference objects matching the given types
     */
    getReferencesByType(types : string|string[]) : any[] {
        if (! this.data['references'] || !Array.isArray(this.data['references']))
            return [];

        if (NERDResource._isstring(types)) types = [types as string]
        if (! Array.isArray(types)) return [];
        types = types.filter(NERDResource._isstring).sort();

        return this.data['references'].filter((c,i?,a?) => {
            return NERDResource._typesintersect(c, types as string[], "refType");
        });
    }

    /**
     * return a list of references that are marked as the primary references that 
     * describe the data resource.  This implementation selects out those marked as 
     * "isDocumentedBy" and "isSupplementTo".  
     */
    getPrimaryReferences() : any[] {
        return this.getReferencesByType(["IsDocumentedBy", "IsSupplementTo"]);
    }

    /**
     * analyze the NERDm resource metadata and return a label indicating the type of 
     * the resource described. 
     * @param resmd Nerdm record
     * @returns Resource Label
     */
    public resourceLabel(): string {
        if (this.data['@type'] instanceof Array && this.data['@type'].length > 0) {
            switch (this.data['@type'][0].replace(/\s/g, '')) {
                case 'nrd:SRD':
                    return "Standard Reference Data";
                case 'nrd:SRM':
                    return "Standard Reference Material";
                case 'nrdp:DataPublication':
                    return "Data Publication";
                case 'nrdp:PublicDataResource':
                    return "Public Data Resource";
                case 'nrda:ScienceTheme':
                    return "Science Theme";
            }
        }

        return "Data Resource";
    }

    /**
     * Return theme
     * @returns the first element of @type. If not exists, return "nist" (default)
     */
    public theme(): string {
        let theme : string = Themes.DEFAULT_THEME;

        if (this.data['@type'] instanceof Array && this.data['@type'].length > 0) {
            return ThemesPrefs.getTheme(this.data['@type'][0].replace(/\s/g, '').split(":")[1]);
        }

        return theme;
    }

    /**
     * Return science theme search url
     */
    public scienceThemeSearchUrl() {
        if(this.theme() == Themes.SCIENCE_THEME) {
            return this.data['components'][0].searchURL;
        }else{
            return "";
        }
    }
}

/**
 * a container for transmitting metadata between the server and the browser
 * versions of the app.  
 */
@Injectable()
export class MetadataTransfer {
    private store : {} = {};

    /**
     * return the metadata saved with the given label
     */
    get(label : string) : {} | undefined {
        return this.store[label] as {};
    }

    /**
     * save the metadata with the given label
     */
    set(label : string, data : {}) : void {
        this.store[label] = data;
    }

    /**
     * return true if metadata with the given label has been 
     * saved to this cache yet.
     */
    isSet(label : string) : boolean {
        return this.store.hasOwnProperty(label);
    }

    /**
     * return an array of the labels that metadata have been saved under
     */
    labels() : string[] {
        return Object.keys(this.store);
    }

    /**
     * serialize into JSON and return the metadata with the given label
     * An empty string is returned if no metadata with the label has been
     * saved yet. 
     */
    serialize(label : string) : string {
        if (! this.isSet(label))
            return "";
        return JSON.stringify(this.store[label], null, 2);
    }
}

