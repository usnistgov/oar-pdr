import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HorizontalBarchartComponent } from './horizontal-barchart.component';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';
import * as d3 from 'd3';

// Test data: expect 3 bars
let inputData = [
    [".../file01",103,"/sub1/file01","file01"],
    ["file03",73,"/sub2/file03","file03"],
    ["file02",206,"/sub3/file02","file02"]
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

        expect(component.data[0][3]).toEqual("file01");
        expect(component.data[1][3]).toEqual("file02");
        expect(component.data[2][3]).toEqual("file03");

        let cmpel = fixture.nativeElement;
        let el = cmpel.querySelector("svg"); 
        expect(el).not.toBeNull();

        // should have the correct height
        // 3 bars x 30/bar + margin top (30) + margin bottom(20) = 140
        expect(el.getAttribute("height")).toBe('140');

        el = cmpel.querySelectorAll("rect"); 

        // Should have 3 bars 
        expect(el).not.toBeNull();
        expect(el.length).toEqual(3);

        // The width(value) of each bar should be 28
        // We defined the bar width = 30. Total width of 3 bars = 90. There are 2 gaps and each gap = bar width / 10 = 3.
        // So actual width of each bar = (90 - 2 * 3) / 3 = 28.
        expect(Math.floor(el[0].getAttribute("height"))).toEqual(28);

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
});
