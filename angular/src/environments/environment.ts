/*
 * Angular build-time environments data.
 * 
 * Environment Label: dev (default)
 *
 * When building under the dev environment mode, the contents of this file will get built into 
 * the application.  
 *
 * This is the default version of this file.  When the app is built via `ng build --env=label`,
 * the contents of ./environment.label.ts will be used instead.  
 */
import { LPSConfig } from '../app/config/config';

export const context = {
    production: false,
    useMetadataService: false
};

export const config : LPSConfig = {
    locations: {
        orgHome:     "https://nist.gov/",
        portalBase:  "https://data.nist.gov/",
        pdrHome:     "https://data.nist.gov/pdr/",
        pdrSearch:   "https://data.nist.gov/sdp/"
    },
    mode:        "dev",
    status:      "Dev Version",
    appVersion:  "v1.2.X",
    production:  context.production,
    editEnabled: true
}

export const testdata : {} = {
  test1: {
    "@context": [
        "https://www.nist.gov/od/dm/nerdm-pub-context.jsonld",
        {
            "@base": "ark:/88434/mds0000fbk"
        }
    ],
    "_schema": "https://www.nist.gov/od/dm/nerdm-schema/v0.1#",
    "_extensionSchemas": [
        "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/PublicDataResource"
    ],
    "@type": [
        "nrdp:PublicDataResource"
    ],
    "@id": "ark:/88434/mds0000fbk",
    "title": "Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32",
    "contactPoint": {
        "hasEmail": "mailto:patricia.flanagan@nist.gov",
        "fn": "Patricia Flanagan"
    },
    "modified": "2011-07-11",
    "ediid": "26DEA39AD677678AE0531A570681F32C1449",
    "landingPage": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
    "description": [
        "Multiple Encounter Dataset (MEDS-I) is a test corpus organized from an extract of submissions of deceased persons with prior multiple encounters. MEDS is provided to assist the FBI and partner organizations refine tools, techniques, and procedures for face recognition as it supports Next Generation Identification (NGI), forensic comparison, training, and analysis, and face image conformance and inter-agency exchange standards. The MITRE Corporation (MITRE) prepared MEDS in the FBI Data Analysis Support Laboratory (DASL) with support from the FBI Biometric Center of Excellence."
    ],
    "keyword": [
        "face",
        "biometrics",
        "forensic"
    ],
    "theme": [
        "Biometrics"
    ],
    "topic": [
        {
            "@type": "Concept",
            "scheme": "https://www.nist.gov/od/dm/nist-themes/v1.0",
            "tag": "Information Technology: Biometrics"
        }
    ],
    "references": [
        {
            "@type": "deo:BibliographicReference",
            "@id": "#ref:publications/multiple-encounter-dataset-i-meds-i",
            "refType": "IsReferencedBy",
            "location": "https://www.nist.gov/publications/multiple-encounter-dataset-i-meds-i",
            "_extensionSchemas": [
                "https://www.nist.gov/od/dm/nerdm-schema/v0.1#/definitions/DCiteDocumentReference"
            ]
        }
    ],
    "accessLevel": "public",
    "license": "https://www.nist.gov/open/license",
    "components": [
        {
            "accessURL": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
            "description": "Zip file with JPEG formatted face image files.",
            "title": "Multiple Encounter Dataset (MEDS)",
            "format": {
                "description": "JPEG formatted images"
            },
            "mediaType": "application/zip",
            "downloadURL": "http://nigos.nist.gov:8080/nist/sd/32/NIST_SD32_MEDS-I_face.zip",
            "filepath": "NIST_SD32_MEDS-I_face.zip",
            "@type": [
                "nrdp:DataFile",
                "dcat:Distribution"
            ],
            "@id": "cmps/NIST_SD32_MEDS-I_face.zip",
            "_extensionSchemas": [
                "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"
            ]
        },
        {
            "accessURL": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
            "description": "zip file with html page with jpeg images of faces",
            "title": "Multiple Encounter Dataset(MEDS-I)",
            "format": {
                "description": "zip file with html and jpeg formatted images"
            },
            "mediaType": "application/zip",
            "downloadURL": "http://nigos.nist.gov:8080/nist/sd/32/NIST_SD32_MEDS-I_html.zip",
            "filepath": "NIST_SD32_MEDS-I_html.zip",
            "@type": [
                "nrdp:DataFile",
                "dcat:Distribution"
            ],
            "@id": "cmps/NIST_SD32_MEDS-I_html.zip",
            "_extensionSchemas": [
                "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"
            ]
        }
    ],
    "publisher": {
        "@type": "org:Organization",
        "name": "National Institute of Standards and Technology"
    },
    "language": [
        "en"
    ],
    "bureauCode": [
        "006:55"
    ],
    "programCode": [
        "006:045"
    ]
  }
};

