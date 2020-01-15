import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class AuthorService {

    constructor() { }

    public getBlankAffiliation(): Affiliation {
        return {
            "@id": "",
            "title": "National Institute of Standards and Technology",
            "dept": "",
            "@type": [
                ""
            ]
        }
    }

    public getBlankAuthor(): Author {
        return {
            "familyName": "",
            "fn": "",
            "givenName": "",
            "middleName": "",
            "affiliation": [
                this.getBlankAffiliation()
            ],
            "orcid": "",
            "isCollapsed": false,
            "fnLocked": false,
            "dataChanged": false
        };
    }
}

/**
 * A container for affiliation info
 */

 export interface Affiliation {
    '@id': string,
    title: string,
    dept: string,
    "@type": [string]
 }
/**
 * A container for author info.
 */
export interface Author {
    // Family name
    familyName: string,
    // Full name
    fn: string,
    // Given name
    givenName: string,
    // Middle name
    middleName: string,
    // Affiliation
    affiliation: Affiliation[],
    // Orcid
    orcid: string,
    // flag for UI control - determind if current author detail info is collapsed
    isCollapsed: boolean,
    // flag for UI control - determind if current author's full name is locked
    fnLocked: boolean,
    // flag for UI control - determind if current author's info has been changed
    dataChanged: boolean
}

