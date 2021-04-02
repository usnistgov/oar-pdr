import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { AppConfig } from '../config/config';
import { NerdmRes, NERDResource } from './nerdm';

/**
 * Labels identifying schemas
 */
export class SchemaLabel {

    /** NERDm Resource */
    static readonly NERDM_RESOURCE = "NERDm#Resource";

    /** Schema.org JSON-LD schema, as harvested by Google */
    static readonly SCHEMA_ORG = "schema.org";

}

/**
 * a type alias for an object that can be converted to JSON.  This is not as strict as it could be.
 */
export type JSONObject = {[name: string]: any};

/**
 * a type alias for a function that converts a NerdmRes record to either an arbitrary object or string
 */
export type NerdmConverter = (md: NerdmRes) => JSONObject|string;

/**
 * convert a NERDm metadata record to a schema.org JSON-LD record
 */
export function nerdm2schemaorg(nerdm: NerdmRes) : JSONObject {
    let res = new NERDResource(nerdm);

    let out: JSONObject = {
        '@context': "https://schema.org",
        '@type': "Dataset",
        'about': nerdm['@id'],
        'name':  nerdm['title'],
        'version': nerdm['version'] || "1",
        'description': nerdm['description'].join("\n"),
        'license': nerdm['license'],
        'audience': {
            '@type': "Audience",
            'audienceType': 'researchers'
        },
        'citation': res.getCitation(),
        'datePublished': nerdm['issued'],
        'dateModified':  nerdm['modified'],
        'inLanguage': nerdm['language'],
        'schemaVersion': 'http://schema.org/version/10.0/', 
        'mainEntityOfPage': nerdm['landingPage'],
        'url': 'https://data.nist.gov/od/id/' + nerdm['ediid']
    };
    if (nerdm.doi) out['sameAs'] = nerdm.doi.replace(/^doi:/, "https://doi.org/");
    if (nerdm.accessLevel == "public") out['isAccessibleForFree'] = true;

    // add topics (and themes) to keywords
    out['keywords'] = JSON.parse(JSON.stringify(nerdm['keyword']));
    if (nerdm.topic) out.keywords.push(...nerdm.topic.map(t => t.tag));

    // publisher
    if (nerdm['publisher']) {
        out['publisher'] = JSON.parse(JSON.stringify(nerdm['publisher']));
        out['publisher']['@type'] = "Organization";
    }

    // contact point => maintainer
    if (nerdm['contactPoint']) {
        let person: JSONObject = { "@type": "Person" };
        person["name"] = nerdm['contactPoint'].fn;

        if(nerdm['contactPoint']['hasEmail']){
            person["email"] = nerdm['contactPoint']['hasEmail'];
            let p = nerdm['contactPoint']['hasEmail'].indexOf(':');
            if (p >= 0) person["email"] = nerdm['contactPoint']['hasEmail'].substring(p+1);
        }
        out['maintainer'] = person;
    }

    // Author
    if (nerdm['authors']) {
        let authors = [];
        let auth = null;
        let fn = '';
        for (let nerd of nerdm['authors']) {
            auth = { "@type": "Person" };
            if (nerdm.familyName) {
                fn = nerdm.familyName;
                auth['familyName'] = nerdm.familyName;
            }
            if (nerdm.givenName) {
                auth['givenName'] = nerdm.givenName;
                if (fn) fn += ", " + nerdm.givenName;
                if (nerdm.middleName) fn += " " + nerdm.middleName;
            }
            if (nerdm.fullName)
                auth['name'] = nerdm.fullName;
            else if (fn)
                auth['name'] = fn;

            authors.push(auth);
        }

        if (authors.length > 0) out['creator'] = authors;
    }
    else if (out['maintainer']) {
        out['creator'] = [out['maintainer']];
    }
    else {
        out['creator'] = [out['publisher']];
    }

    return out;
}

/**
 * a wrapper for metadata is some format.  Its properties help identify the schema and format of the 
 * metadata as well as give access to the wrapped metadata.  The serialize() function converts the metadata
 * to a string for delivery over the web.
 *
 * The key properties are:
 *   * md -- the metadata itself; metadata an object if it's to be encoded in JSON 
 *   * label -- a string identifying the schema the metadata conforms to;  This value is usually
 *              one of those defined in SchemaLabel
 *   * contentType - the content type to use when delivering the metadata over the web
 */
export class MetadataEnvelope {

    /**
     * wrap metadata in an envelope
     * @param label        a label that identifies the schema that the metadata conforms to.  This 
     *                     is normally one of the contants defined in SchemaLabel
     * @param md           the metadata being wrapped
     * @param contentType  the MIME type to use when delivering the metadata over the web
     */
    constructor(public label: string, public md: {}|string, public contentType: string) { }

    /**
     * serialize the metadata into a string for delivery over the web.
     *
     * This implementation assumes that the metadata has already been serialized if the md field is 
     * a string; the md value is returned without change.  If it is an object, it will serialize it 
     * by dumping it as JSON.
     */
    public serialize() : string {
        if (typeof this.md === 'string')
            return this.md
        return JSON.stringify(this.md, null, 2);
    }
}

let _cvt_supported = [ SchemaLabel.SCHEMA_ORG ];
let _cvt_defcvtrs = {};
_cvt_defcvtrs[SchemaLabel.SCHEMA_ORG] = [nerdm2schemaorg, "application/ld+json"];

/**
 * a service that converts NERDm metadata into other formats.  
 * 
 * The injected AppConfig sets the labels for the metadata formats that should be embedded into 
 * landing pages.
 */
@Injectable()
export class NerdmConversionService {
    private _embedLabels: string[] = [];
    private _cvtrs: {[nm: string]: NerdmConverter} = {};
    private _cnttps: {[nm: string]: string} = {};

    private static readonly _supported = _cvt_supported;
    private static readonly _defcvtrs = _cvt_defcvtrs;

    constructor(config : AppConfig) {
        for (let fmt in NerdmConversionService._defcvtrs) {
            let cvtparms = NerdmConversionService._defcvtrs[fmt];
            this.supportConversion(fmt, cvtparms[0], cvtparms[1]);
        }

        let labels: string|string[] = config.get("embedMetadata", []);
        if (!labels) labels = [];
        if (typeof labels === 'string') labels = [labels];
        for(let fmt of labels) {
            if (this.supportsFormat(fmt))
                this._embedLabels.push(fmt);
            else
                console.warn("Unsupport format for embedding: "+fmt);
        }
    }

    /**
     * register a format conversion function to support with a given format name
     */
    supportConversion(format: string, func: NerdmConverter, ctype: string) : void {
        this._cvtrs[format] = func;
        this._cnttps[format] = ctype;
    }
        
    /**
     * return a list of labels for the metadata formats support by this conversion service
     */
    public supportedFormats() : string[] {
        return Object.keys(this._cvtrs);
    }

    /**
     * return true if the format with the given label is supported via this service
     */
    public supportsFormat(format : string) : boolean {
        return !!this._cvtrs[format];
    }

    /**
     * return a list of the labels for metadata formats configured to be embedded into Landing Pages
     */
    public formatsToEmbed() : string[] { return this._embedLabels; }

    /**
     * add a format to embed.  The input format label must one of the supported labesl returned by 
     * supportedFormats() or it will be ignored.
     */
    public addFormatToEmbed(format : string) : boolean {
        if (! this.supportsFormat(format))
            return false;
        if (! this._embedLabels.includes(format))
            this._embedLabels.push(format);
        return true;
    }

    _getConvertFunc(format: string) : NerdmConverter {
        return this._cvtrs[format];
    }
    _getContentTypeFor(format: string) : string {
        return this._cnttps[format];
    }

    /**
     * convert the given NERDm Resource record into the schema/format specified by the given format label. 
     * If the returned converted value is a string, the caller should assume that it has already been 
     * serialized.  If it is an object; the caller should assume it is serializable into JSON.  A null
     * value indicates that format is not supported.  
     */
    public convertTo(md : NerdmRes, format : string) : MetadataEnvelope {
        let cvt = this._getConvertFunc(format);
        if (! cvt) return null;   // format not supported
        return new MetadataEnvelope(format, cvt(md), this._cnttps[format]);
    }

    /**
     * convert the given NERDm Resource into each of the formats configured to be embeded into a landing page.
     */
    public convertToEmbedFormats(md : NerdmRes) : Observable<MetadataEnvelope> {
        return new Observable(subscriber => {
            for (let fmt of this._embedLabels) {
                subscriber.next(this.convertTo(md, fmt));
            }
        });
    }
}
