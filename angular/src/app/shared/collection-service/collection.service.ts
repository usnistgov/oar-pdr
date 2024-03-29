import { Injectable } from '@angular/core';
import { Themes, ThemesPrefs, Collections, Collection, ColorScheme, CollectionThemes } from '../../shared/globals/globals';
import * as CollectionData from '../../../assets/site-constants/collections.json';

@Injectable({
  providedIn: 'root'
})
export class CollectionService {

    constructor() { }

    /**
     * Loads collection data from json file for nist and given collection
     * @param collection collection to be loaded
     * @returns collection object list that contains nist and collection data
     */
    loadCollections(collection: string) {
        let allCollections = {}; 

        // Load collection data from config file
        allCollections[Collections.DEFAULT.toLowerCase()] = this.localCollectionData(Collections.DEFAULT.toLowerCase())

        if(collection){
            allCollections[collection.toLowerCase()] = this.localCollectionData(collection.toLowerCase())
        }

        return allCollections;
    }

    /**
     * Loads collection data from json file for given collection
     * @param collection collection to be loaded
     * @returns collection object
     */
    localCollectionData(collection: string) {
        if(collection)
            return Object.assign(new Collection(), CollectionData[collection.toLowerCase()]);  
        else    
            return Object.assign(new Collection(), CollectionData[Collections.DEFAULT.toLowerCase()]);  
    }
}
