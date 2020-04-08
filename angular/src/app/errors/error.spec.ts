import { Injector, ErrorHandler } from "@angular/core";

import { AppErrorHandler } from "./error";

/*
 * Note this test suite provides low coverage of the handler as it does not provide 
 * routing infrastructure.
 */

describe('AppErrorHandler', function() {
    let injector : Injector = Injector.create([]);
    let platid : Object = "browser";

    it('handleError()', function() {
        let hdlr : ErrorHandler = new AppErrorHandler(platid, injector);
        expect(function() {hdlr.handleError(new Error("Test error"));}).not.toThrow();
    });
});
