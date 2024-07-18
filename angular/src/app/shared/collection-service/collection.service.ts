import { Injectable } from '@angular/core';
import { Themes, ThemesPrefs, Collections, Collection, ColorScheme, CollectionThemes } from '../../shared/globals/globals';
import * as CollectionData from '../../../assets/site-constants/collections.json';

@Injectable({
  providedIn: 'root'
})
export class CollectionService {
    //  Array to define the collection order
    collectionOrder: string[] = [];

    allCollections: any = {};

    constructor() {
        // this.collectionOrder = Object.keys(CollectionData).sort(function(a,b){return CollectionData[a]["displayOrder"]-CollectionData[b]["displayOrder"]});

        this.collectionOrder = Object.keys(CollectionData).sort(function(a,b){return CollectionData[a]["displayOrder"]-CollectionData[b]["displayOrder"]});

        this.collectionOrder = this.collectionOrder.filter(function(v) { return v !== 'default' });
     }

    getCollectionOrder() {
        return this.collectionOrder;
    }

    /**
     * Loads collection data from json file for nist and given collection
     * @param collection collection to be loaded
     * @returns collection object list that contains nist and collection data
     */
    loadAllCollections() {
        for(let col of this.collectionOrder) {
            this.allCollections[col] = this.loadCollection(col);
        }

        return this.allCollections;
    }

    /**
     * Loads collection data from json file for given collection
     * @param collection collection to be loaded
     * @returns collection object
     */
    loadCollection(collection: string) {
        if(collection)
            return Object.assign(new Collection(), CollectionData[collection]);  
        else    
            return Object.assign(new Collection(), CollectionData[Collections.DEFAULT]);  
    }
}
