import { Injectable } from '@angular/core';
import { HttpClient, HttpRequest, HttpResponse, HttpHandler, HttpEvent, HttpInterceptor, HTTP_INTERCEPTORS } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { delay, mergeMap, materialize, dematerialize } from 'rxjs/operators';
import { TestDataService } from '../shared/testdata-service/testDataService';
import { DownloadService } from '../shared/download-service/download-service.service';
 
@Injectable()
export class FakeBackendInterceptor implements HttpInterceptor {
 
    constructor(private testDataService: TestDataService,
    private downloadService: DownloadService,
    private http: HttpClient) { }
    
    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // array in local storage for registered users

        let sampleData: any = '{"_id" : "5bc4c4dfb4c0630145163c71","_schema" : "https://data.nist.gov/od/dm/nerdm-schema/v0.2#","topic" : [],"references" : [{"refType" : "IsReferencedBy","_extensionSchemas" : ["https://data.nist.gov/od/dm/nerdm-schema/v0.2#/definitions/DCiteReference"],"@id" : "#ref:10.1007/s10694-016-0646-7","@type" : [ "deo:BibliographicReference"],"location" : "https://doi.org/10.1007/s10694-016-0646-7"}],"_extensionSchemas" : [ "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/PublicDataResource"],"landingPage" : "https://www.nist.gov/el/fire-research-division-73300/national-fire-research-laboratory-73306/measurement-behavior-steel","dataHierarchy" : [{"filepath" : "NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx"}, {"filepath" : "NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256"}, {"filepath" : "NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx"}, {"filepath" : "NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256"}],"title" : "Measurement of the Behavior of Steel Beams under Localized Fire Exposure","theme" : [ "Structural fire resistance"],"inventory" : [{"forCollection" : "","descCount" : 5,"childCollections" : [],"childCount" : 5,"byType" : [{"descCount" : 5,"forType" : "dcat:Distribution","childCount" : 5}, {"descCount" : 1,"forType" : "nrd:Hidden","childCount" : 1}, {"descCount" : 2,"forType" : "nrdp:ChecksumFile","childCount" : 2}, {"descCount" : 2,"forType" : "nrdp:DataFile","childCount" : 2}, {"descCount" : 4,"forType" : "nrdp:DownloadableFile","childCount" : 4}]}],"programCode" : [ "006:045"],"@context" : [ "https://data.nist.gov/od/dm/nerdm-pub-context.jsonld", {"@base" : "ark:/88434/mds0147p62"}],"description" : ["A total of nine localized fire tests on steel beams were designed and conducted in the National Fire Research Laboratory as part of its commissioning project, including thermal tests (Tests 1 through 5) and four-point bending test at ambient (Test 6) and elevated temperatures (Tests 7 through 9). All the tested specimens were nominally 6.2-m long W16×26 beams made of ASTM A992 steel. Each specimen was supported by one of the two following connections: (i) simple support (Tests 1 through 8), and (ii) double-angles bolted to laterally braced support columns (Test 9). The midspan of each specimen was exposed to an open-flame fire using the 1-m2 natural gas burners. The burner was located 1.1 m below the bottom flange of the beam at midspan. A four-point flexural loading scheme was used to apply concentrated forces at two locations 2.44 m apart around midspan. The data included temperatures, the heat release rates from the burner, and structural measurements including forces, displacements and strains. The Type B standard uncertainties in various measurements were also included. Overall, the test results showed that the heating rate of the specimen was sensitive to the prescribed heat release rate-time relationship. However, the thermal gradient developed in the fire-exposed cross sections of the beam never achieved linearity under the localized fire exposure. Regardless of the connection types and fire conditions (i.e., steady-state or transient-state fire), the beams exhibited a similar behavior and failure mode. When subjected to combined fire and flexural loads, the beam specimens exhibited the lateral-torsional buckling followed by runaway vertical displacements at midspan. Additional details of experimental procedures and uncertainty analysis for this experimental series are provided in the following publications:1) Zhang, C., Choe, L., Gross, J., Ramesh, S., Bundy, M. (2017). Engineering Approach for Designing a Thermal Test of Real-scale Steel Beam Exposed to Localized Fire. Fire Technology, Vol 53, Issue 4, pp 1535-1554. DOI: 10.1007/s10694-016-0646-72) Choe, L., Ramesh, S., Zhang, C., Gross, J. (2016). The Performance of Structural Steel Beams Subjected to a Localized Fire. The 9th International Conference on Structures in Fire (SiF 16), June 8-10, 2016, Princeton, NJ."],"language" : ["en"],"bureauCode" : [ "006:55"],"contactPoint" : {"hasEmail" : "mailto:lisa.choe@nist.gov","fn" : "Lisa Choe"},"accessLevel" : "public","@id" : "ark:/88434/mds0147p62","publisher" : {"@type" : "org:Organization","name" : "National Institute of Standards and Technology"},"doi" : "doi:10.18434/M37H4G","keyword" : [ "steel beam; localized fire; thermal and mechanical behavior; experimental test"],"license" : "https://www.nist.gov/open/license","modified" : "2017-08-14","ediid" : "5BD6911D381AB2E3E0531A57068151FA1869","components" : [ {"filepath" : "NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx","mediaType" : "text/plain","downloadURL" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx","@id" : "cmps/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx","@type" : [ "nrdp:DataFile", "nrdp:DownloadableFile", "dcat:Distribution"],"_extensionSchemas" : [ "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/DataFile"]}, {"description" : "SHA-256 checksum value for NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx","algorithm" : {"tag" : "sha256","@type" : "Thing"},"filepath" : "NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256","mediaType" : "text/plain","downloadURL" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256","@id" : "cmps/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256","@type" : ["nrdp:ChecksumFile", "nrdp:DownloadableFile", "dcat:Distribution"],"_extensionSchemas" : [ "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/ChecksumFile"]},{"filepath" : "NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx","mediaType" : "text/plain","downloadURL" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx","@id" : "cmps/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx","@type" : [ "nrdp:DataFile",    "nrdp:DownloadableFile", "dcat:Distribution"],"_extensionSchemas" : [ "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/DataFile"]}, {"description" : "SHA-256 checksum value for NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx","algorithm" : {"tag" : "sha256","@type" : "Thing"},"filepath" : "NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256","mediaType" : "text/plain","downloadURL" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256","@id" : "cmps/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256","@type" : [ "nrdp:ChecksumFile", "nrdp:DownloadableFile", "dcat:Distribution"],"_extensionSchemas" : [ "https://data.nist.gov/od/dm/nerdm-schema/pub/v0.2#/definitions/ChecksumFile"]}, {"accessURL" : "https://doi.org/10.18434/M37H4G","@id" : "#doi:10.18434/M37H4G","@type" :["nrd:Hidden","dcat:Distribution"]}],"@type" : [ "nrdp:PublicDataResource"]}';

       let bundlePlanRes : any = '{"status" : "warnings","messages" : [ "Some urls are not added due to unsupported host.", "Additional message here." ],"notIncluded" : [ {"filePath" : "/1894/license2.pdf","downloadUrl" : "https://project-open-data.cio.gov/v1.1/schema","message" : "Not valid Url."} ],"bundleNameFilePathUrl" : [ {"bundleName" : "testdownload-1.zip","includeFiles" : [ {"filePath" :"5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx"},{"filePath" :"5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256"} ]},{"bundleName": "testdownload-2.zip","includeFiles" : [ {"filePath" : "5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx"},{"filePath" : "5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256"} ]} ],"postEach" : "_bundle"}';
        // let bundlePlanRes : any = '{"status" : "warnings","messages" : [ "Some urls are not added due to unsupported host.", "Additional message here." ],"bundleNameFilePathUrl" : [ {"bundleName" : "testdownload-1.zip","includeFiles" : [ {"filePath" :"5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx"},{"filePath" :"5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_08112017.xlsx.sha256"} ]},{"bundleName": "testdownload-2.zip","includeFiles" : [ {"filePath" : "5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx"},{"filePath" : "5BD6911D381AB2E3E0531A57068151FA1869/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256","downloadUrl" : "https://s3.amazonaws.com/nist-midas/1856/NFRL_LocalizedFireTest_SteelBeam_09012017.xlsx.sha256"} ]} ],"postEach" : "_bundle"}';


        // let httpRequest: any[] = [
        //     {"url":"https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip","body":null,"reportProgress":true,"withCredentials":false,"responseType":"blob","method":"GET","headers":{"normalizedNames":{},"lazyUpdate":null,"headers":{}},"params":{"updates":null,"cloneFrom":null,"encoder":{},"map":null},"urlWithParams":"https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip"}
        // ];
            
        // wrap in delayed observable to simulate server api call
        return of(null).pipe(mergeMap(() => {
            // get bundlePlan
            if (request.url.endsWith('/od/ds/_bundle_plan') && request.method === 'POST') {
                return of(new HttpResponse({ status: 200, body: JSON.parse(bundlePlanRes) }));
            }

            if (request.url.endsWith('/rmm/records/5BD6911D381AB2E3E0531A57068151FA1869') && request.method === 'GET') {
                return of(new HttpResponse({ status: 200, body: JSON.parse(sampleData) }));
        }
            

            // get bundle
            // if (request.url.endsWith('/od/ds/_bundle') && request.method === 'POST') {
            //     // return new Observable(observer => {
            //     //     observer.next(this.testDataService.getBundle('https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip', params););
            //     //     observer.complete();
            //     //   });
            //     // return this.testDataService.getBundle('https://s3.amazonaws.com/nist-midas/1858/20170213_PowderPlate2_Pad.zip', bundlePlanRes);
            //     console.log("Handling /od/ds/_bundle:");

            //     const duplicate = request.clone({
            // method: 'get' 
            //     })
            //     return next.handle(request);
            // }
            
            // pass through any requests not handled above
            return next.handle(request);
            
        }))
    
        // call materialize and dematerialize to ensure delay even if an error is thrown (https://github.com/Reactive-Extensions/RxJS/issues/648)
        .pipe(materialize())
        .pipe(delay(500))
        .pipe(dematerialize());
    }
}
 
export let fakeBackendProvider = {
    // use fake backend in place of Http service for backend-less development
    provide: HTTP_INTERCEPTORS,
    useClass: FakeBackendInterceptor,
    multi: true
};