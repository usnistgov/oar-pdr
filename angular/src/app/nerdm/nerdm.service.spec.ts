import * as nerdm from './nerdm';
import * as nerdsvc from './nerdm.service';
import { Observable } from 'rxjs';
import * as rxjs from 'rxjs';

describe('TransferMetadataService', function() {

    let trx : nerdm.MetadataTransfer;
    let svc : nerdsvc.MetadataService;
    let tdata : nerdm.NerdmRes = {
        "@id":  "ark:/88888/goober",
        ediid: "goober",
        title: "A Good Test"
    };

    beforeEach(() => {
        trx = new nerdm.MetadataTransfer();
        trx.set(nerdsvc.NERDM_MT_PREFIX+"goober", tdata);
        svc = new nerdsvc.TransferMetadataService(trx);
    });

    it("getMetadata", function(done) {
        let t1 = svc.getMetadata("goober");
        t1.subscribe((data) => { expect(data).toEqual(tdata); },
                     (err)  => { fail(err); });

        let t2 = svc.getMetadata("gomer");
        t2.subscribe((data) => { expect(data).toBeUndefined(); },
                     (err)  => { fail(err);  });

        rxjs.merge(t1, t2).subscribe(null, null, () => { done(); });
    });

});

class FailingMetadataService extends nerdsvc.MetadataService {
    getMetadata(id : string) : Observable<nerdm.NerdmRes> {
        throw new Error("delegate service resorted to.");
    }
};

describe('CachingMetadataService', function() {

    let trx : nerdm.MetadataTransfer;
    let svc : nerdsvc.MetadataService;
    let tdata : nerdm.NerdmRes = {
        "@id":  "ark:/88888/goober",
        ediid: "goober",
        title: "A Good Test"
    };

    beforeEach(() => {
        trx = new nerdm.MetadataTransfer();
        trx.set("goober", tdata);
        svc = new nerdsvc.CachingMetadataService(new FailingMetadataService(), trx);
    });

    it('getMetadata() via cache', function(done) {
        let t1 = svc.getMetadata("goober");
        t1.subscribe((data) => { expect(data).toEqual(tdata); },
                     (err)  => { fail(err); },
                     ()     => { done(); });
    });

    it('getMetadata() via delegate', function() {
        expect(() => { svc.getMetadata("gomer") }).toThrowError();
    });
});

describe('TransmittingMetadataService', function() {
    // Note: this does not demonstrate caching to the MetadatService

    let trx : nerdm.MetadataTransfer;
    let svc : nerdsvc.MetadataService;
    let tdata : nerdm.NerdmRes = {
        "@id":  "ark:/88888/goober",
        ediid: "goober",
        title: "A Good Test"
    };

    beforeEach(() => {
        trx = new nerdm.MetadataTransfer();
    });

    it('getMetadata() via cache', function(done) {
        trx.set(nerdsvc.NERDM_MT_PREFIX+"goober", tdata);
        svc = new nerdsvc.TransmittingMetadataService(new FailingMetadataService(), trx);

        let t1 = svc.getMetadata("goober");
        t1.subscribe((data) => { expect(data).toEqual(tdata); },
                     (err)  => { fail(err); },
                     ()     => { done(); });
    });

    it('getMetadata() via delegate', function() {
        trx.set(nerdsvc.NERDM_MT_PREFIX+"goober", tdata);
        svc = new nerdsvc.TransmittingMetadataService(new FailingMetadataService(), trx);

        expect(() => { svc.getMetadata("gomer") }).toThrowError();
    });

    it('getMetadata() caching to MetadataTransfer', function(done) {
        let cache : nerdm.MetadataTransfer = new nerdm.MetadataTransfer();
        cache.set("goober", tdata);
        svc = new nerdsvc.TransmittingMetadataService(
                  new nerdsvc.CachingMetadataService(
                      new FailingMetadataService(), cache), trx);
        expect(trx.labels().length).toBe(0);

        svc.getMetadata("goober").subscribe(
            (data) => {
                // successfully pulled data from underlying service
                expect(data).toEqual(tdata);

                // data was cached to the MetadataTransfer object so that it can be
                // serialized to the output HTML page. 
                expect(trx.labels().length).toBe(1);
                expect(trx.get(nerdsvc.NERDM_MT_PREFIX+"goober")).toBe(tdata);
            },
            (err) => {  fail(err);  },
            () => {  done();  }
        );
    });
});
