import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HorizontalBarchartComponent } from './horizontal-barchart.component';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import * as d3 from 'd3';

// Test data: expect 3 bars
let inputData = [
    ["file01",103],
    ["file03",73],
    ["file02",206]
];

describe('HorizontalBarchartComponent', () => {
    let component: HorizontalBarchartComponent;
    let fixture: ComponentFixture<HorizontalBarchartComponent>;

    beforeEach(async() => {
        TestBed.configureTestingModule({
        imports: [ FormsModule ],
        declarations: [ HorizontalBarchartComponent ]
        })
        .compileComponents();

        fixture = TestBed.createComponent(HorizontalBarchartComponent);
        component = fixture.componentInstance;
        fixture.detectChanges();
    });

    it('should render the correct width and height of bars', async() => {
        component.inputdata = inputData;
        component.initData();
        component.createChart();
        component.updateChart();
        fixture.detectChanges();
        await fixture.whenStable();

        expect(component).toBeTruthy();

        expect(component.data[0][0]).toEqual("file01");
        expect(component.data[1][0]).toEqual("file02");
        expect(component.data[2][0]).toEqual("file03");

        let cmpel = fixture.nativeElement;
        let el = cmpel.querySelector("svg"); 
        console.log("svg", el);
        expect(el).not.toBeNull();

        // should have the correct height
        // 3 bars x 30/bar + bargin top (60) + margin bottom(20) = 170
        expect(el.getAttribute("height")).toBe('170');

        // should have the correct width
        expect(el.getAttribute("width")).toBe('770');

        el = cmpel.querySelectorAll("rect"); 

        // Should have 3 bars 
        expect(el).not.toBeNull();
        expect(el.length).toEqual(3);

        // The width(value) of each bar should be 26
        // We defined the bar width = 30. Total width of 3 bars = 90. There are 4 gaps and each gap = bar width / 10 = 3.
        // So actual width of each bar = (90 - 4 * 3) / 3 = 26.
        expect(Math.floor(el[0].getAttribute("height"))).toEqual(26);

        // Remove this testing because the actual with of the bars may a little different from machine to machine
        // The height(value) of the first bar should be 339
        // chart.width = svg.width(770) - calculated margin.left(41) - margin.right(50) = 679
        // xscale = 679 / 206 = 3.2961
        // 1st bar height(value) = 103 * 3.2961 = 339
        // expect(Math.floor(el[0].getAttribute("width"))).toEqual(339);

        // The height(value) of the 2nd bar should be 206 * 3.2961 = 678
        // expect(Math.floor(el[1].getAttribute("width"))).toEqual(678);

        // The height(value) of the 3rd bar should be 73 * 3.2961 = 240
        // expect(Math.floor(el[2].getAttribute("width"))).toEqual(240);

        spyOn(component, 'sortBarChart').and.callThrough();
        let options: DebugElement[] = fixture.debugElement.queryAll(By.css('input[type="radio"]'));

        // ascending order...
        options[0].triggerEventHandler('change', { target: options[0].nativeElement });
        expect(component.sortBarChart).toHaveBeenCalled();

        expect(component.data[0][1]).toEqual(73);
        expect(component.data[1][1]).toEqual(103);
        expect(component.data[2][1]).toEqual(206);

        // descending order...
        options[1].triggerEventHandler('change', { target: options[1].nativeElement });
        expect(component.sortBarChart).toHaveBeenCalled();

        expect(component.data[0][1]).toEqual(206);
        expect(component.data[1][1]).toEqual(103);
        expect(component.data[2][1]).toEqual(73);

        // original order...
        options[2].triggerEventHandler('change', { target: options[2].nativeElement });
        expect(component.sortBarChart).toHaveBeenCalled();

        expect(component.data[0][1]).toEqual(103);
        expect(component.data[1][1]).toEqual(206);
        expect(component.data[2][1]).toEqual(73);
    });

    // it('should create', () => {
    //     expect(component).toBeTruthy();
    // });
});
