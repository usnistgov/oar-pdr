import { async, ComponentFixture, TestBed } from '@angular/core/testing';

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

    it('should initialize as a blank instruction', () => {
        makeComp();
        fixture.detectChanges();
        let cmpel = fixture.nativeElement;
        // console.log("messagebar root tag: "+cmpel.outerHTML);
        // expect(cmpel.getAttribute("class")).toEqual("messagebar");
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        expect(mbardiv.length).toEqual(1);
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);
        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("");
    });

    it('should display an error message on demand', () => {
        makeComp();
        component.error("Dang");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);

        expect(children[0].getAttribute("class")).toEqual("error");
        expect(children[0].innerHTML).toEqual("Dang");

        component.syserror("The quick brown fox jumped over the lazy dogs.  Every boy deserves favor.");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        children = mbardiv[0].querySelectorAll("div")        
        expect(children[0].getAttribute("class")).toEqual("syserror");
    });

    it('should display a syserror message on demand', () => {
        makeComp();
        component.syserror("SuperDang");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);

        expect(children[0].getAttribute("class")).toEqual("syserror");
        expect(children[0].innerHTML).toContain("SuperDang");
        expect(children[0].innerHTML).toContain("Oops!");

        component.instruct("logout");
        fixture.detectChanges();
        mbardiv = cmpel.querySelectorAll(".messagebar");
        children = mbardiv[0].querySelectorAll("div")        
        
        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("logout");
    });

    it('should display a warning message on demand', () => {
        makeComp();
        component.warn("Wait!");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);

        expect(children[0].getAttribute("class")).toEqual("warning");
        expect(children[0].innerHTML).toEqual("Wait!");

        component.instruct("logout");
        fixture.detectChanges();
        
        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("logout");
    });

    it('should display a celebratory message on demand', () => {
        makeComp();
        component.celebrate("Yay!");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);

        expect(children[0].getAttribute("class")).toEqual("celebration");
        expect(children[0].innerHTML).toEqual("Yay!");

        component.instruct("logout");
        fixture.detectChanges();
        
        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("logout");
    });

    it('should display a tip on demand', () => {
        makeComp();
        component.tip("Try it.");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);

        expect(children[0].getAttribute("class")).toEqual("tip");
        expect(children[0].innerHTML).toEqual("Try it.");

        component.instruct("logout");
        fixture.detectChanges();
        
        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("logout");
    });

    it('should display information on demand', () => {
        makeComp();
        component.inform("Good");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);

        expect(children[0].getAttribute("class")).toEqual("information");
        expect(children[0].innerHTML).toEqual("Good");

        component.instruct("logout");
        fixture.detectChanges();
        
        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("logout");
    });

    it('should display an instruction on demand', () => {
        makeComp();
        component.instruct("Press");
        fixture.detectChanges();
        
        let cmpel = fixture.nativeElement;
        let mbardiv = cmpel.querySelectorAll(".messagebar");
        let children = mbardiv[0].querySelectorAll("div")
        expect(children.length).toEqual(1);

        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("Press");

        component.instruct("logout");
        fixture.detectChanges();
        
        expect(children[0].getAttribute("class")).toEqual("instruction");
        expect(children[0].innerHTML).toEqual("logout");
    });

});
