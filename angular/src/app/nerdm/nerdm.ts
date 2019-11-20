/**
 * Classes and interfaces to support the NERDm metadata infrastructure
 */
import { Injectable, InjectionToken } from '@angular/core';

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

