import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';

import { MessageBarComponent } from './messagebar.component';

describe('MessageBarComponent', () => {
    let component : MessageBarComponent;
    let fixture : ComponentFixture<MessageBarComponent>;

    let makeComp = function() {
        TestBed.configureTestingModule({
            declarations: [ MessageBarComponent ],
            providers: []
        }).compileComponents();

        fixture = TestBed.createComponent(MessageBarComponent);
        component = fixture.componentInstance;
        // fixture.detectChanges();

        expect(component).toBeDefined();
    }

    it('should initialize with an empty list', () => {
        makeComp();
        fixture.detectChanges();
        let cmpel = fixture.nativeElement;
        // console.log("messagebar root tag: "+cmpel.outerHTML);
        // expect(cmpel.getAttribute("class")).toEqual("messagebar");
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(0);
    });

    it('should display an error message on demand', () => {
        makeComp();
        component.error("Dang");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // one message
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);  // message and dismiss icon

        expect(children[1].getAttribute("class")).toEqual("error");
        expect(children[1].innerHTML).toEqual("Dang");

        component.syserror("The quick brown fox jumped over the lazy dogs.  Every boy deserves favor.");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages
        children = mbardiv[1].querySelectorAll("div")        
        expect(children.length).toEqual(2);
        expect(children[1].getAttribute("class")).toEqual("syserror");
    });

    it('should display a syserror message on demand', () => {
        makeComp();
        component.syserror("SuperDang");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // one message
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);

        expect(children[1].getAttribute("class")).toEqual("syserror");
        expect(children[1].innerHTML).toContain("SuperDang");
        expect(children[1].innerHTML).toContain("Oops!");

        component.instruct("logout");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        children = mbardiv[1].querySelectorAll("div")        
        
        expect(children[1].getAttribute("class")).toEqual("instruction");
        expect(children[1].innerHTML).toEqual("logout");
    });

    it('should display a warning message on demand', () => {
        makeComp();
        component.warn("Wait!");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // one message
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);

        expect(children[1].getAttribute("class")).toEqual("warning");
        expect(children[1].innerHTML).toEqual("Wait!");

        component.instruct("logout");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages
        children = mbardiv[1].querySelectorAll("div")        
        
        expect(children[1].getAttribute("class")).toEqual("instruction");
        expect(children[1].innerHTML).toEqual("logout");
    });

    it('should display a celebratory message on demand', () => {
        makeComp();
        component.celebrate("Yay!");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // one message
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);

        expect(children[1].getAttribute("class")).toEqual("celebration");
        expect(children[1].innerHTML).toEqual("Yay!");

        component.instruct("logout");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages
        children = mbardiv[1].querySelectorAll("div")        
        
        expect(children[1].getAttribute("class")).toEqual("instruction");
        expect(children[1].innerHTML).toEqual("logout");
    });

    it('should display a tip on demand', () => {
        makeComp();
        component.tip("Try it.");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // one message
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);

        expect(children[1].getAttribute("class")).toEqual("tip");
        expect(children[1].innerHTML).toEqual("Try it.");

        component.instruct("logout");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages
        children = mbardiv[1].querySelectorAll("div")        
        
        expect(children[1].getAttribute("class")).toEqual("instruction");
        expect(children[1].innerHTML).toEqual("logout");
    });

    it('should display information on demand', () => {
        makeComp();
        component.inform("Good");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // one message
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);

        expect(children[1].getAttribute("class")).toEqual("information");
        expect(children[1].innerHTML).toEqual("Good");

        component.instruct("logout");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages
        children = mbardiv[1].querySelectorAll("div")        
        
        expect(children[1].getAttribute("class")).toEqual("instruction");
        expect(children[1].innerHTML).toEqual("logout");
    });

    it('should display an instruction on demand', () => {
        makeComp();
        component.instruct("Press");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // one message
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);

        expect(children[1].getAttribute("class")).toEqual("instruction");
        expect(children[1].innerHTML).toEqual("Press");

        component.instruct("logout");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages
        children = mbardiv[1].querySelectorAll("div")        
        
        expect(children[1].getAttribute("class")).toEqual("instruction");
        expect(children[1].innerHTML).toEqual("logout");
    });

    it('dismiss()', () => {
        makeComp();
        component.instruct("Press");
        component.warn("Now!");
        fixture.detectChanges();

        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages

        // remove the second one
        component.dismiss(1);
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);  // now, one message again
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(2);
        expect(children[1].innerHTML).toEqual("Press");
    });

    it('dismissAll()', () => {
        makeComp();
        component.instruct("Press");
        component.warn("Now!");
        fixture.detectChanges();

        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(2);  // now, two messages

        // remove the second one
        component.dismissAll();
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(0);  // now, one message again
    });

});
