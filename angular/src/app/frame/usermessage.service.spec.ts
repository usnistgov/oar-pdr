import { UserMessageService } from './usermessage.service';

describe('UserMessageService', () => {

    let message : string = null;
    let type : string = null;
    let svc : UserMessageService = null;

    let subscriber = {
        next: (msg) => {
            message = msg.text;
            type = msg.type;
        }
    }

    beforeEach(() => {
        message = null;
        type = null;
        svc = new UserMessageService();
    })

    it('sends tip', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.tip("50c");
        expect(message).toEqual("50c");
        expect(type).toEqual("tip");
    });

    it('sends tip', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.tip("50c");
        expect(message).toEqual("50c");
        expect(type).toEqual("tip");
        svc.tip("a dollar");
        expect(message).toEqual("a dollar");
        expect(type).toEqual("tip");
    });

    it('sends instruction', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.instruct("Stop!");
        expect(message).toEqual("Stop!");
        expect(type).toEqual("instruction");
        svc.tip("a dollar");
        expect(message).toEqual("a dollar");
        expect(type).toEqual("tip");
    });

    it('sends warning', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.warn("Beware.");
        expect(message).toEqual("Beware.");
        expect(type).toEqual("warning");
        svc.tip("a dollar");
        expect(message).toEqual("a dollar");
        expect(type).toEqual("tip");
    });

    it('sends an error', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.error("tsk");
        expect(message).toEqual("tsk");
        expect(type).toEqual("error");
        svc.tip("a dollar");
        expect(message).toEqual("a dollar");
        expect(type).toEqual("tip");
    });

    it('sends a system error', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.syserror("ouch");
        expect(message).toEqual("ouch");
        expect(type).toEqual("syserror");
        svc.tip("a dollar");
        expect(message).toEqual("a dollar");
        expect(type).toEqual("tip");
    });

    it('sends a celebration', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.celebrate("sing!");
        expect(message).toEqual("sing!");
        expect(type).toEqual("celebration");
        svc.tip("a dollar");
        expect(message).toEqual("a dollar");
        expect(type).toEqual("tip");
    });

    it('sends an informational item', () => {
        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();
        svc.inform("I am");
        expect(message).toEqual("I am");
        expect(type).toEqual("information");
        svc.tip("a dollar");
        expect(message).toEqual("a dollar");
        expect(type).toEqual("tip");
    });

    
    it('can receive messages without a subscriber', () => {
        expect(message).toBeNull();
        expect(type).toBeNull();

        svc.tip("50c");
        expect(message).toBeNull();
        expect(type).toBeNull();

        svc._subscribe(subscriber);
        expect(message).toBeNull();
        expect(type).toBeNull();

        svc.instruct("Just Do It(TM)");
        expect(message).toEqual("Just Do It(TM)");
        expect(type).toEqual("instruction");
    });
    
        

});
