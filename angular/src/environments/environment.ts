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
    useMetadataService: false,
    useCustomizationService: false
};

export const config: LPSConfig = {
    locations: {
        orgHome: "https://nist.gov/",
        portalBase: "https://data.nist.gov/",
        pdrHome: "https://data.nist.gov/pdr/",
        pdrSearch: "https://data.nist.gov/sdp/",
        mdService:   "https://data.nist.gov/rmm/records/",
        taxonomyService: "https://data.nist.gov/rmm/taxonomy"
    },
    mdAPI: "https://data.nist.gov/rmm/records/",
    metricsAPI: "https://data.nist.gov/rmm/usagemetrics/",
    // customizationAPI: "https://testdata.nist.gov/customization/",
    customizationAPI: "https://datapubtest.nist.gov/customization/",
    mode: "dev",
    status: "Dev Version",
    appVersion: "v1.3.X",
    production: context.production,
    editEnabled: false,
    distService: "https://testdata.nist.gov/od/ds/",
    gacode: "not-set",
    screenSizeBreakPoint: 1060,
    bundleSizeAlert: 500000000,
    // Decide how many seconds to wait to refresh metrics after user download one/more files
    delayTimeForMetricsRefresh: 300  
}

export const testdata: {} = {
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
        "modified": "2019-03-28 12:24:31",
        "issued": "2019-04-05T16:04:26.0",
        "ediid": "26DEA39AD677678AE0531A570681F32C1449",
        "landingPage": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
        "version": "1.0.1",
        "versionHistory": [
            {
                "version": "1.0.0",
                "issued": "2019-03-27 00:00:00",
                "@id": "ark:/88434/mds0000fbk",
                "location": "https://data.nist.gov/od/id/ark:/88434/mds0000fbk",
                "description": "initial release"
            },
            {
                "version": "1.0.1",
                "issued": "2019-03-28 12:24:31",
                "@id": "ark:/88434/mds0000fbkmds1103vzr",
                "location": "https://data.nist.gov/od/id/ark:/88434/mds0000fbk",
                "description": "metadata update"
            }
        ],
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
                "refType":"IsDocumentedBy",
                "title":"In-situ Raman spectroscopic measurements of the deformation region in indented glasses",
                "issued":"2020-02",
                "citation":"Gerbig, Y. B., & Michaels, C. A. (2020). In-situ Raman spectroscopic measurements of the deformation region in indented glasses. Journal of Non-Crystalline Solids, 530, 119828. doi:10.1016/j.jnoncrysol.2019.119828\n",
                "label":"Journal of Non-Crystalline Solids: In-situ Raman spectroscopic measurements of the deformation region in indented glasses",
                "location":"https://doi.org/10.1016/j.jnoncrysol.2019.119828",
                "@id":"#ref:10.1016/j.jnoncrysol.2019.119828",
                "@type":["schema:Article"],
                "_extensionSchemas":["https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/DCiteReference"]
            },
            {
                "refType":"IsCitedBy",
                "title":"Indentation device forin situRaman spectroscopic and optical studies",
                "issued":"2012-12",
                "citation":"Gerbig, Y. B., Michaels, C. A., Forster, A. M., Hettenhouser, J. W., Byrd, W. E., Morris, D. J., & Cook, R. F. (2012). Indentation device forin situRaman spectroscopic and optical studies. Review of Scientific Instruments, 83(12), 125106. doi:10.1063/1.4769995\n",
                "location":"https://doi.org/10.1063/1.4769995",
                "@id":"#ref:10.1063/1.4769995",
                "@type":["schema:Article"],
                "_extensionSchemas":["https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/DCiteReference"]
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
                    "nrdp:Hidden",
                    "nrdp:AccessPage",
                    "dcat:Distribution"
                ],
                "@id": "cmps/NIST_SD32_MEDS-I_face.zip",
                "_extensionSchemas": [
                    "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/AccessPage"
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
            },
            {
                "accessURL": "https://doi.org/10.18434/mds0000fbk",
                "description": "DOI Access to landing page",
                "title": "DOI Access to \"Multiple Encounter Dataset (MEDS-I)\"",
                "@type": [
                    "nrdp:DataFile",
                    "dcat:Distribution"
                ],
                "@id": "#doi:10.18434/mds0000fbk",
                "_extensionSchemas": [
                    "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/"
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
        ],
        "_updateDetails": [{
            "_userDetails": { "userId": "dsn1", "userName": "Deoyani", "userLastName": "Nandrekar Heinis", "userEmail": "deoyani.nandrekarheinis@nist.gov" },
            "_updateDate": "2019-12-03T15:50:32.490+0000"
        },
        {
            "_userDetails": { "userId": "dsn1", "userName": "Deoyani", "userLastName": "Nandrekar Heinis", "userEmail": "deoyani.nandrekarheinis@nist.gov" },
            "_updateDate": "2019-12-03T15:50:53.208+0000"
        }
        ]

    },

    
    "test2": {
        "@context": [
            "https://www.nist.gov/od/dm/nerdm-pub-context.jsonld",
            {
                "@base": "ark:/88434/mds0000fbk"
            }
        ],
        "_schema": "https://www.nist.gov/od/dm/nerdm-schema/v0.1#",
        "_extensionSchemas": [
            "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataPublication"
        ],
        "@type": [
            "nrdp:PublicDataResource"
        ],
        "@id": "ark:/88434/mds0000fbk",
        "ediid": "ark:/88434/mds0000fbk",
        "doi": "doi:XXXXX/MMMMM",
        "title": "Test2",
        "version": "12.1",
        "authors": [
            {
                "familyName": "Doe",
                "givenName": "John",
                "fn": "John Doe",
                "orcid": "0000-0000-0000-0000"
            },
            {
                "familyName": "Plant",
                "givenName": "Robert",
                "fn": "R. Plant"
            }
        ],
        "contactPoint": {
            "hasEmail": "mailto:patricia.flanagan@nist.gov",
            "fn": "Patricia Flanagan"
        },
        "modified": "2011-07-11",
        "landingPage": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
        "description": [ "para1", "para2" ],
        "keyword": [],
        "publisher": {
            "@type": "org:Organization",
            "name": "National Institute of Standards and Technology"
        },
        "components": [
            {
                "@type": [ "nrdp:DataFile", "dcat:Distribution" ],
                "filepath": "README.txt",
                "size": "784",
                "mediaType": "text/plain",
                "downloadURL": "https://data.nist.gov/od/ds/mds0000fbk/README.txt"
            },
            {
                "@type": [ "nrdp:Subcollection" ],
                "filepath": "data",
            },
            {
                "@type": [ "nrdp:Subcollection", "nrd:Hidden" ],
                "filepath": "secret",
            },
            {
                "@type": [ "nrdp:DataFile", "dcat:Distribution" ],
                "filepath": "data/file.csv",
                "size": "21784",
                "mediaType": "text/csv",
                "downloadURL": "https://data.nist.gov/od/ds/mds0000fbk/data/file.csv"
            },
            {
                "@type": [ "nrdp:DataFile", "nrd:Hidden" ],
                "filepath": "data/secret.csv",
                "size": "15784",
                "mediaType": "text/csv",
                "downloadURL": "https://data.nist.gov/od/ds/mds0000fbk/data/file.csv"
            }
        ]
    }
};

