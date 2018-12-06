// import {browser, element, by, By, $, $$, ExpectedConditions, protractor} from 'protractor';
// import * as _angular_ from "angular";
// declare global {
//   const angular: typeof _angular_;
// }


// describe('Landing Page', function() {
    
//   beforeEach(function() {

//     browser.ignoreSynchronization = true;
//    browser.addMockModule('httpMockertest','console.log("My test 1263512635!!@!")');
//     browser.addMockModule('httpMocker', function() {
//       angular.module('httpMocker', ['ngMockE2E'])
//       .run(function(httpBackend) {
//         console.log("Is it here");
//         httpBackend.whenGET('http://localhost/rmm/records/3A1EE2F169DD3B8CE0531A570681DB5D1491')
//           .respond(
//              {"_id":{"timestamp":1508225827,"machineIdentifier":8777488,"processIdentifier":291,"counter":16692557,"time":1508225827000,"date":1508225827000,"timeSecond":1508225827},"_schema":"https://www.nist.gov/od/dm/nerdm-schema/v0.1#","topic":[{"scheme":"https://www.nist.gov/od/dm/nist-themes/v1.0","tag":"Physics: Optical physics","@type":"Concept"}],"references":[{"refType":"IsReferencedBy","_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/v0.1#/definitions/DCiteDocumentReference"],"@id":"#ref:10.1364/OE.24.014100","@type":"deo:BibliographicReference","location":"https://dx.doi.org/10.1364/OE.24.014100"}],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/PublicDataResource"],"landingPage":"https://www.nist.gov/nvl/project-index-optical-method-sorting-nanoparticles-size","dataHierarchy":[{"filepath":"1491_optSortSphEvaluated20160701.cdf"},{"filepath":"1491_optSortSphEvaluated20160701.cdf.sha256"},{"filepath":"1491_optSortSphEvaluated20160701.nb"},{"filepath":"1491_optSortSph20160701.m"},{"filepath":"1491_optSortSphEvaluated20160701.nb.sha256"},{"filepath":"1491_optSortSph20160701.m.sha256"}],"title":"OptSortSph: Sorting Spherical Dielectric Particles in a Standing-Wave Interference Field","theme":["Optical physics"],"inventory":[{"forCollection":"","descCount":7,"childCollections":[],"childCount":7,"byType":[{"descCount":7,"forType":"dcat:Distribution","childCount":7},{"descCount":1,"forType":"nrd:Hidden","childCount":1},{"descCount":6,"forType":"nrdp:DataFile","childCount":6}]}],"programCode":["006:045"],"@context":["https://www.nist.gov/od/dm/nerdm-pub-context.jsonld",{"@base":"ark:/88434/mds00hw91v"}],"description":["Software to predict the optical sorting of particles in a standing-wave laser interference field"],"language":["en"],"bureauCode":["006:55"],"contactPoint":{"hasEmail":"mailto:zachary.levine@nist.gov","fn":"Zachary Levine"},"accessLevel":"public","@id":"ark:/88434/mds00hw91v","publisher":{"@type":"org:Organization","name":"National Institute of Standards and Technology"},"doi":"doi:10.18434/T4SW26","keyword":["optical sorting","laser interference field","nanoparticles","convection of fluid"],"license":"https://www.nist.gov/open/license","modified":"2016-07-01","ediid":"3A1EE2F169DD3B8CE0531A570681DB5D1491","components":[{"description":"A .cdf version of the Mathematica notebook. A reader for this file is available at: http://www.wolfram.com/cdf/","filepath":"1491_optSortSphEvaluated20160701.cdf","title":"CDF version of the Mathematica notebook","mediaType":"application/vnd.wolfram.player","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.cdf","@id":"cmps/1491_optSortSphEvaluated20160701.cdf","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSphEvaluated20160701.cdf.sha256","title":"SHA-256 file for the CDF version of the Mathematica notebook","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.cdf.sha256","@id":"cmps/1491_optSortSphEvaluated20160701.cdf.sha256","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"accessURL":"https://doi.org/10.18434/T4SW26","description":"Software to predict the optical sorting of particles in a standing-wave laser interference field","format":"Digital Object Identifier, a persistent identifier","title":"DOI access for OptSortSph: Sorting Spherical Dielectric Particles in a Standing-Wave Interference Field","mediaType":"application/zip","@id":"#doi:10.18434/T4SW26","@type":["nrd:Hidden","dcat:Distribution"]},{"filepath":"1491_optSortSphEvaluated20160701.nb","title":"Download for the Mathematica notebook","mediaType":"application/mathematica","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.nb","@id":"cmps/1491_optSortSphEvaluated20160701.nb","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSph20160701.m","title":"ASCII version of the code (without documentation)","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSph20160701.m","@id":"cmps/1491_optSortSph20160701.m","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSphEvaluated20160701.nb.sha256","title":"SHA-256 file for Mathematica download file","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.nb.sha256","@id":"cmps/1491_optSortSphEvaluated20160701.nb.sha256","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSph20160701.m.sha256","title":"SHA-256 file for ASCII version of the code","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSph20160701.m.sha256","@id":"cmps/1491_optSortSph20160701.m.sha256","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]}],"@type":["nrdp:PublicDataResource"]}
//           )
//       })
//     })
//   });
//   beforeEach(async () => {
//     return await browser.get('/od/id/3A1EE2F169DD3B8CE0531A570681DB5D1491');
//   });

//   it('should display top title of Landing page', async() => {
    
//     //var EC = protractor.ExpectedConditions;
//     var label = await element(by.css('.recordType b'));
//     expect(label.getText()).toContain('Public Data Resource');
//    });

//    it('should display title of landing page', function() {
//     //browser.get('/#/id/3A1EE2F169DD3B8CE0531A570681DB5D1491');
//     //browser.waitForAngular();
//     //var EC = protractor.ExpectedConditions;
//     var label = element.all(by.css('h2'));
//     expect(label.get(0).getText()).toMatch(/OptSortSph/i,
//       'should say something about "OptSortSph"');
//     //expect(label.get(0).getText()).toContain('OptSortSph: Sorting Spherical Dielectric Particles in a Standing-Wave Interference Field');
//    });
//   //  it('should show current  landing url', async() => {
//   //   var test = await browser.getCurrentUrl();
//   //   expect(test).toContain('/id/3A1EE2F169DD3B8CE0531A570681DB5D1491');
//   //  });

//   //  it('should show current url2', async() => {
//   //   var test = await browser.get('http://localhost:5555/#/id/3A1EE2F169DD3B8CE0531A570681DB5D1491');
//   //   expect(test).toContain('/od/id/3A1EE2F169DD3B8CE0531A570681DB5D1491');
//   //  });

// });