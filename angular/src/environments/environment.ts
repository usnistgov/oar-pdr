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
    useMetadataService: true,
    useCustomizationService: true
};

export const config: LPSConfig = {
    locations: {
        orgHome: "https://nist.gov/",
        portalBase: "https://data.nist.gov/",
        pdrHome: "https://data.nist.gov/pdr/",
        pdrSearch: "https://data.nist.gov/sdp/",
        mdService:   "https://data.nist.gov/od/id/",
        taxonomyService: "https://data.nist.gov/rmm/taxonomy"
    },
    APIs: {
        customization: "https://data.nist.gov/customization",
        // customization: "https://testdata.nist.gov/customization",
        // distService: "https://data.nist.gov/od/ds/",
        distService: "https://testdata.nist.gov/od/ds/",
        mdService: "https://data.nist.gov/od/id/",
        mdSearch:  "https://data.nist.gov/rmm/",
        metrics:   "https://data.nist.gov/rmm/usagemetrics",
        taxonomy:   "https://data.nist.gov/rmm/taxonomy",
        rpaBackend: "https://data.nist.gov/rpa/"
    },
    mode: "dev",
    status: "Dev Version",
    appVersion: "v1.3.X",
    production: context.production,
    editEnabled: false,
    gacode: "not-set",
    screenSizeBreakPoint: 1060,
    bundleSizeAlert: 500000000,
    // Decide how many seconds to wait to refresh metrics after user download one/more files
    delayTimeForMetricsRefresh: 300,
    standardNISTTaxonomyURI: "https://data.nist.gov/od/dm/nist-themes/"  
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
        "@type": ["nrdp:PublicDataResource"],
        "@id": "ark:/88434/mds0000fbk",
        "title": "Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32",
        "contactPoint": {
            "hasEmail": "mailto:patricia.flanagan@nist.gov",
            "fn": "Patricia Flanagan"
        },
        "modified": "2019-03-27 12:24:31",
        "issued": "2019-04-05T16:04:26.0",
        "ediid": "26DEA39AD677678AE0531A570681F32C1449",
        "landingPage": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
        "version": "1.0.1",
        "firstIssued": "2019-03-27 00:00:00",
        "revised": "2019-03-28 12:24:31",
        "annotated": "2019-03-29 12:24:31",
        "releaseHistory": {
            "@id": "ark:/88434/mds0000fbk/pdr:v",
            "@type": [ "nrdr:ReleaseHistory" ],
            "hasRelease": [
            {
                "version": "1.0.0",
                "issued": "2019-03-27 00:00:00",
                "@id": "ark:/88434/mds0000fbk/pdr:v/1.0.0",
                "location": "https://data.nist.gov/od/id/mds0000fbk/pdr:v/1.0.0",
                "description": "initial release"
            },
            {
                "version": "1.1.0",
                "issued": "2019-03-28 12:24:31",
                "@id": "ark:/88434/mds0000fbk/pdr:v/1.1.0",
                "location": "https://data.nist.gov/od/id/ark:/88434/mds0000fbk/pdr:v/1.0.0",
                "description": "data file update"
            },
            {
                "version": "1.1.2",
                "issued": "2019-03-29 12:24:31",
                "@id": "ark:/88434/mds0000fbk/pdr:v/1.1.2",
                "location": "https://data.nist.gov/od/id/ark:/88434/mds0000fbk/pdr:v/1.1.2",
                "description": "metadata update"
            }
            ]},
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
    test2: {
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
        "@id": "ark:/88434/mds0000fbk2",
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
    },
    test3: {
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
        "@id": "ark:/88434/mds0000fbk3",
        "doi": "doi:10.18434/mds0000fbk3",
        "title": "Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32",
        "contactPoint": {
            "hasEmail": "mailto:patricia.flanagan@nist.gov",
            "fn": "Patricia Flanagan"
        },
        "modified": "2019-03-28",
        "ediid": "test3",
        "issued": "2019-03-28 00:00:00",
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
                "issued": "2019-03-28 00:00:00",
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
        "accessLevel": "restricted public",
        "rights": "brief statement goes here",
        "license": "https://www.nist.gov/open/license",
        "components": [
            {
                "accessURL": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
                "description": "This page presents a registration form that must be completed to download the restricted data. Multiple Encounter Dataset (MEDS-I) is a test corpus organized from an extract of submissions of deceased persons with prior multiple encounters. MEDS is provided to assist the FBI and partner organizations refine tools, techniques, and procedures for face recognition as it supports Next Generation Identification (NGI), forensic comparison, training, and analysis, and face image conformance and inter-agency exchange standards. The MITRE Corporation (MITRE) prepared MEDS in the FBI Data Analysis Support Laboratory (DASL) with support from the FBI Biometric Center of Excellence.",
                "title": "Gateway for Registered Data Access",
                "format": {
                    "description": "JPEG formatted images"
                },
                "mediaType": "application/zip",
                "downloadURL": "http://nigos.nist.gov:8080/nist/sd/32/NIST_SD32_MEDS-I_face.zip",
                "filepath": "NIST_SD32_MEDS-I_face.zip",
                "@type": [
                    "nrdp:RestrictedAccessPage",
                    "nrdp:AccessPage"
                ],
                "@id": "cmps/NIST_SD32_MEDS-I_face.zip",
                "_extensionSchemas": [
                    "https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/AccessPage"
                ]
            },
            {
                "accessURL": "https://www.nist.gov/itl/iad/image-group/special-database-32-multiple-encounter-dataset-meds",
                "description": "zip file with html page with jpeg images of faces.",
                "title": "Multiple Encounter Dataset(MEDS-I)",
                "format": {
                    "description": "zip file with html and jpeg formatted images"
                },
                "mediaType": "application/zip",
                "downloadURL": "http://nigos.nist.gov:8080/nist/sd/32/NIST_SD32_MEDS-I_html.zip",
                "filepath": "NIST_SD32_MEDS-I_html.zip",
                "@type": [
                    "nrdp:DataFile",
                    "dcat:Distribution",
                    "nrdp:AccessPage"
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
                    "nrd:Hidden",
                    "nrdp:AccessPage",
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
    test4: {
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
            "nrda:ScienceTheme"
        ],
        "@id": "ark:/88434/mds0000fbk4",
        "title": "Multiple Encounter Dataset (MEDS-I) - NIST Special Database 32",
        "contactPoint": {
            "hasEmail": "mailto:patricia.flanagan@nist.gov",
            "fn": "Patricia Flanagan"
        },
        "modified": "2019-03-27 12:24:31",
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
                "version": "1.0.2",
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
    DNAScienceTheme: {
        "_schema": "https://data.nist.gov/od/dm/nerdm-schema/v0.5#",
        "topic": [
            {
                "scheme": "https://data.nist.gov/od/dm/nist-themes-forensics/v1.0",
                "tag": "Forensics: DNA and biological evidence",
                "@type": "Concept"
            }
        ],
        "keyword": [
            "forensics",
            "dna"
        ],
        "_extensionSchemas": [
            "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.5#/definitions/PublicDataResource",
            "https://data.nist.gov/od/dm/nerdm-schema/agg/v0.1#/definitions/Aggregation"
        ],
        "landingPage": "https://www.nist.gov/itl/iad/image-group",
        "title": "NIST Research in DNA and biological evidence.",
        "theme": [
            "Forensics:DNA and biological evidence"
        ],
        "version": "1.0.0",
        "programCode": [
            "006:045"
        ],
        "@context": [
            "https://data.nist.gov/od/dm/nerdm-pub-context.jsonld",
            {
                "@base": "ark:/88434/mds991133"
            }
        ],
        "description": [
            "DNA is a complex molecule that contains the instructions for building and maintaining the bodies of humans and other organisms. With the exception of red blood cells, every cell in your body has DNA. And with the exception of identical twins, everyone’s DNA is different. If someone leaves blood, semen or other biological material at a crime scene, scientists can use it as DNA evidence and create a DNA profile, or genetic fingerprint of that person. That profile can be used to search a DNA database for a possible suspect, to associate a suspect with evidence left at a crime scene, or to link two crimes that may have been committed by the same person."
        ],
        "bureauCode": [
            "006:55"
        ],
        "contactPoint": {
            "hasEmail": "mailto:dna-forensics@nist.gov",
            "fn": "NIST DNA research Group"
        },
        "accessLevel": "public",
        "@id": "ark:/88434/mds991122",
        "publisher": {
            "name": "National Institute of Standards and Technology",
            "@type": "org:Organization"
        },
        "doi": "doi:10.18434/T4/1502474",
        "license": "https://www.nist.gov/open/license",
        "language": [
            "en"
        ],
        "modified": "2022-01-01 12:01:02",
        "ediid": "6F1714704711023AE053245706818C1A1936",
        "versionHistory": [
            {
                "issued": "2021-12-31",
                "version": "1.0.0",
                "@id": "ark:/88434/mds991122",
                "location": "https://data.nist.gov/od/id/ark:/88434/mds991122",
                "description": "initial release"
            }
        ],
        "@type": [
            "nrda: ScienceTheme",
            "nrdp: PublicDataResource"
        ],
        "Facilitators": [
            {
                "middleName": "",
                "familyName": "Fiumara",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Gregory",
                "@type": "foaf:Person",
                "fn": "Greg Fiumara",
                "jobTitle": "PI"
            }
        ],
        "Creators": [
            {
                "middleName": "",
                "familyName": "Brady",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Mary",
                "@type": "foaf:Person",
                "fn": "Mary Brady",
                "jobTitle": "PI"
            }
        ],
        "componenets": [
            {
                "@type": [
                    "nrda:DynamicResourceSet",
                    "nrdp:SearchPage"
                ],
                "_extensionSchemas": [
                    "https://data.nist.gov/od/dm/nerdm-schema/agg/v0.1#/definitions/DynamicResourceSet"
                ],
                "searchURL": "/rmm/records?isPartOf.@id=ark:/88434/mds991133",
                "name": "DNA and Biological Evidence data"
            }
        ],
        "isPartOf": [
            {
                "title": "NIST Forensics Research.",
                "proxyFor": "ark:/88434/mds9911",
                "resType": [
                    "nrda:Aggregation",
                    "nrdp:PublicDataResource"
                ]
            }
        ]
    },
    BiometricsScienceTheme: {
        "_schema": "https://data.nist.gov/od/dm/nerdm-schema/v0.5#",
        "topic": [
            {
                "scheme": "https://data.nist.gov/od/dm/nist-themes-forensics/v1.0",
                "tag": "Forensics: Biometrics",
                "@type": "Concept"
            },
            {
                "scheme": "https://data.nist.gov/od/dm/nist-themes/v1.1",
                "tag": "Information Technology: Biometrics",
                "@type": "Concept"
            }
        ],
        "keyword": [
            "latent",
            "biometrics",
            "forensics"
        ],
        "_extensionSchemas": [
            "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.5#/definitions/PublicDataResource",
            "https://data.nist.gov/od/dm/nerdm-schema/agg/v0.1#/definitions/Aggregation"
        ],
        "landingPage": "https://www.nist.gov/itl/iad/image-group",
        "title": "NIST Research in Biometric forensics.",
        "theme": [
            "Information Technology: Biometrics",
            "Forensics: Biometrics"
        ],
        "version": "1.0.0",
        "programCode": [
            "006:045"
        ],
        "@context": [
            "https://data.nist.gov/od/dm/nerdm-pub-context.jsonld",
            {
                "@base": "ark:/88434/mds991122"
            }
        ],
        "description": [
            "This is Biometrics research projects collection. There are many different projects are created here."
        ],
        "bureauCode": [
            "006:55"
        ],
        "contactPoint": {
            "hasEmail": "mailto:biometrics@nist.gov",
            "fn": "NIST Biometrics Group"
        },
        "accessLevel": "public",
        "@id": "ark:/88434/mds991122",
        "publisher": {
            "name": "National Institute of Standards and Technology",
            "@type": "org:Organization"
        },
        "doi": "doi:10.18434/T4/1502474",
        "license": "https://www.nist.gov/open/license",
        "language": [
            "en"
        ],
        "modified": "2022-02-15 12:01:02",
        "ediid": "BiometricsScienceTheme",
        "versionHistory": [
            {
                "issued": "2021-12-31",
                "version": "1.0.0",
                "@id": "ark:/88434/mds991122",
                "location": "https://data.nist.gov/od/id/ark:/88434/mds991122",
                "description": "initial release"
            }
        ],
        "@type": [
            "nrda: ScienceTheme",
            "nrdp: PublicDataResource"
        ],
        "Facilitators": [
            {
                "middleName": "",
                "familyName": "Fiumara",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Gregory",
                "@type": "foaf:Person",
                "fn": "Greg Fiumara",
                "jobTitle": "PI"
            }
        ],
        "Creators": [
            {
                "middleName": "",
                "familyName": "Brady",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Mary",
                "@type": "foaf:Person",
                "fn": "Mary Brady",
                "jobTitle": "PI"
            }
        ],
        "componenets": [
            {
                "@type": [
                    "nrda:DynamicResourceSet",
                    "nrdp:SearchPage"
                ],
                "_extensionSchemas": [
                    "https://data.nist.gov/od/dm/nerdm-schema/agg/v0.1#/definitions/DynamicResourceSet"
                ],
                "searchURL": "/rmm/records?isPartOf.@id=ark:/88434/mds991122",
                "name": "Biometrics Data"
            }
        ],
        "isPartOf": [
            {
                "title": "NIST Forensics Research. ",
                "proxyFor": "ark:/88434/mds9911",
                "resType": [
                    "nrda:Aggregation",
                    "nrdp:PublicDataResource"
                ]
            }
        ]
    },
    forensics:{
        "_schema": "https://data.nist.gov/od/dm/nerdm-schema/v0.2#",
        "topic": [
            {
                "scheme": "https://data.nist.gov/od/dm/nist-themes-forensics/v1.0",
                "tag": "Forensics: Biometrics",
                "@type": "Concept"
            },
            {
                "scheme": "https://data.nist.gov/od/dm/nist-themes-forensics/v1.0",
                "tag": "Forensics",
                "@type": "Concept"
            },
            {
                "scheme": "https://data.nist.gov/od/dm/nist-themes/v1.1",
                "tag": "Forensics",
                "@type": "Concept"
            },
            {
                "scheme": "https://data.nist.gov/od/dm/nist-themes/v1.1",
                "tag": "Information Technology: Biometrics",
                "@type": "Concept"
            }
        ],
        "keyword": [
            "latent",
            "digital forensics",
            "biometrics",
            "forensics"
        ],
        "_extensionSchemas": [
            "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/PublicDataResource",
            "https://data.nist.gov/od/dm/nerdm-schema/science-initiative-schema/v0.1#/definitions/ResearchInitiative"
        ],
        "landingPage": "https://www.nist.gov/forensic-science/research-focus-areas",
        "title": "NIST Forensics Research Data",
        "theme": [
            "Information Technology",
            "Forensics",
            "Materials"
        ],
        "version": "1.0.0",
        "programCode": [
            "006:045"
        ],
        "@context": [
            "https://data.nist.gov/od/dm/nerdm-pub-context.jsonld",
            {
                "@base": "ark:/88434/mds9911"
            }
        ],
        "description": [
            "NIST research in several forensic disciplines, including DNA, ballistics, fingerprint analysis, trace evidence, and digital, among others. We provide physical reference standards and data that help forensic laboratories validate their analytical methods and ensure accurate test results"
        ],
        "bureauCode": [
            "006:55"
        ],
        "contactPoint": {
            "hasEmail": "mailto:gregory.fiumara@nist.gov",
            "fn": "Gregory Fiumara"
        },
        "accessLevel": "public",
        "@id": "ark:/88434/mds9911",
        "publisher": {
            "name": "National Institute of Standards and Technology",
            "@type": "org:Organization"
        },
        "license": "https://www.nist.gov/open/license",
        "language": [
            "en"
        ],
        "modified": "2018-06-14 01:02:03",
        "ediid": "ark:/88434/mds9911",
        "versionHistory": [
            {
                "issued": "2021-12-25",
                "version": "1.0.0",
                "@id": "ark:/88434/mds90911",
                "location": "https://data.nist.gov/od/id/ark:/88434/mds9911",
                "description": "initial release"
            }
        ],
        "facilitators": [
            {
                "middleName": "",
                "familyName": "Guttman",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Barbara",
                "@type": "foaf:Person",
                "fn": "Barbara Guttman",
                "jobTitle": "Program Lead"
            },
            {
                "middleName": "",
                "familyName": "Fiumara",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics Biometrics division"
                    }
                ],
                "orcid": "",
                "givenName": "Gregory",
                "@type": "foaf:Person",
                "fn": "Gregory Fiumara",
                "jobTitle": "Program Lead"
            },
            {
                "middleName": "",
                "familyName": "Navarro",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Marcela",
                "@type": "foaf:Person",
                "fn": "Marcela Navarro",
                "jobTitle": "Program Lead"
            },
            {
                "middleName": "",
                "familyName": "Vallone",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Peter",
                "@type": "foaf:Person",
                "fn": "Peter Vallone",
                "jobTitle": "Program Lead"
            },
            {
                "middleName": "",
                "familyName": "Lund",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Steve",
                "@type": "foaf:Person",
                "fn": "Steve Lund",
                "jobTitle": "Program Lead"
            },
            {
                "middleName": "",
                "familyName": "Taylor",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Melissa",
                "@type": "foaf:Person",
                "fn": "Melissa Taylor",
                "jobTitle": "Program Lead"
            }
        ],
        "creators": [
            {
                "middleName": "",
                "familyName": "Brady",
                "affiliation": [
                    {
                        "@type": "org:Organization",
                        "title": "NIST Forensics division"
                    }
                ],
                "orcid": "",
                "givenName": "Mary",
                "@type": "foaf:Person",
                "fn": "Mary Brady",
                "jobTitle": "PI"
            }
        ],
        "@type": [
            "nrda: ScienceTheme",
            "nrda: Aggregation",
            "nrdp: PublicDataResource"
        ],
        "components": [
            {
                "@type": [
                    "nrda:DynamicResourceSet", "nrdp:SearchPage"
                ],
                "searchURL": "/rmm/records?isPartOf.@id=ark:/88434/mds9911",
                "accessURL": "http://localhost:5555/#/search?q=isPartOf.@id%3Dark:/88434/mds9911&alternateView=forensics",
                "title": "All Forensics Data Collection",
                "description": "The search URL here queries all the data which is part of Forensics data collection."
            },
            {
                "@type": [
                    "nrda:DynamicResourceSet", "nrdp:SearchPage"
                ],
                "searchURL": "/rmm/records?isPartOf.@id=ark:/88434/mds991133",
                "accessURL": "https://data.nist.gov/sdp/#/search?q=isPartOf.@id%3Dark:/88434/mds991133&alternateView=forensics",
                "title": "DNA and Biological Evidence data collection",
                "description": "Search URL for the DNA and Biological evidence data collection."
            },
            {
                "@type": [
                    "nrda:DynamicResourceSet", "nrdp:SearchPage"
                ],
                "searchURL": "/rmm/records?isPartOf.@id=ark:/88434/mds991122",
                "accessURL": "https://data.nist.gov/sdp/#/search?q=isPartOf.@id%3Dark:/88434/mds991122&alternateView=forensics",
                "title": "Biometrics Data Collection",
                "description": "Search URL for the biometrics data collection."
            }
    
        ]
    }
};

