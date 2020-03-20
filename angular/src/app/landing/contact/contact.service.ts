import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class ContactService {

    constructor() { }

    public getBlankContact() : ContactPoint {
        return {
            "fn": "",
            "hasEmail": "",
            "address": [""]
        }
    }
}

export interface ContactPoint {
    fn: string,
    hasEmail: string,
    address: string[]
}
