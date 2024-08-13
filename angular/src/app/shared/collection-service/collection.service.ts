import { Injectable } from '@angular/core';
import { Themes, ThemesPrefs, Collections, Collection, ColorScheme, CollectionThemes } from '../../shared/globals/globals';
import * as CollectionData from '../../../assets/site-constants/collections.json';
import { BehaviorSubject, Observable, throwError } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CollectionService {
    // Array to define the collection order
    collectionOrder: string[] = [];

    // list of collections for landing page display (topics)
    collectionForDisplay: string[] = [];

    allCollections: any = {};
    colorSchemes: any = {};
    colorSchemeSub = new BehaviorSubject<ColorScheme[]>([] as ColorScheme[]);

    constructor() {
        // this.collectionOrder = Object.keys(CollectionData).sort(function(a,b){return CollectionData[a]["displayOrder"]-CollectionData[b]["displayOrder"]});

        this.collectionOrder = Object.keys(CollectionData).sort(function(a,b){return CollectionData[a]["displayOrder"]-CollectionData[b]["displayOrder"]});

        this.collectionOrder = this.collectionOrder.filter(function(v) { return v !== 'default' });

        this.collectionForDisplay = Object.keys(CollectionData).sort(function(a,b){return CollectionData[a]["displayOrder"]-CollectionData[b]["displayOrder"]}).filter(key => CollectionData[key].landongPage); 
    }

    serviceInit() {


        this.loadAllCollections();
    }

    getColorScheme(collection: string) {
        return this.colorSchemes[collection];
    }

    /**
     * Set color scheme
     * @param colorScheme 
     */
    setColorScheme(colorScheme: ColorScheme[]) {
        let sub = this.colorSchemeSub;
        sub.next(colorScheme);
    }

    /**
     * Watch color scheme
     */
    watchColorScheme(): Observable<ColorScheme[]> {
        let sub = this.colorSchemeSub;
        return sub.asObservable();
    }

    getCollectionOrder() {
        return this.collectionOrder;
    }

    getCollectionForDisplay() {
        return this.collectionForDisplay;
    }

    /**
     * Loads collection data from json file for nist and given collection
     * @param collection collection to be loaded
     * @returns collection object list that contains nist and collection data
     */
    loadAllCollections() {
        for(let col of this.collectionOrder) {
            this.allCollections[col] = this.loadCollection(col);
            this.colorSchemes[col] = this.allCollections[col].color;
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
