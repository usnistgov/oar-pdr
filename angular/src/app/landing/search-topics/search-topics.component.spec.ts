import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchTopicsComponent } from './search-topics.component';
import { FormsModule } from '@angular/forms';
import { DataTableModule, TreeModule } from 'primeng/primeng';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { TreeNode } from 'primeng/api';
import { TestDataService } from '../../shared/testdata-service/testDataService';

describe('SearchTopicsComponent', () => {
  let component: SearchTopicsComponent;
  let fixture: ComponentFixture<SearchTopicsComponent>;
  let tempTopics: string[];
  let taxonomyTree: TreeNode[] = [];
  let record: any;
  let compiled: any;
  let outputValue: any;
  let saveButton: any;
  let treeNodeLink: any;
  var tempTaxonomyTree = {};

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [SearchTopicsComponent],
      imports: [FormsModule, DataTableModule, TreeModule],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [NgbActiveModal, TestDataService]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    tempTopics = ["Bioscience: Genomic measurements"];
    taxonomyTree = [];

    let newPart = null;
    newPart = {
      data: {
        treeId: "Test1",
        name: "Test1",
        researchTopic: "Test1",
        bkcolor: 'white'
      }, children: [],
      expanded: false
    };
    taxonomyTree.push(newPart);

    const record: any = require('../../../assets/sample2.json');

    fixture = TestBed.createComponent(SearchTopicsComponent);
    component = fixture.componentInstance;
    component.tempTopics = tempTopics;
    component.taxonomyTree = taxonomyTree;
    // component.record = record;
    component.recordEditmode = false;

    saveButton = fixture.nativeElement.getElementsByTagName('button')[1];
    treeNodeLink = fixture.nativeElement.getElementsByTagName('span')[1];
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have title: Research Topics', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('#title').innerText).toEqual('Research Topics');
    expect(fixture.nativeElement.getElementsByTagName('span')[0].innerText).toEqual('Bioscience: Genomic measurements');

    expect((fixture.nativeElement.getElementsByTagName('p-treeTable')[0].value)[0].data.name).toEqual('Test1');
  });

  it('saveTopic() should be called', () => {
    component.passEntry.subscribe((value) => {
      outputValue = value;
    });
    spyOn(component, 'saveTopic');
    saveButton.click();
    expect(component.saveTopic).toHaveBeenCalled();
  });

  it('First topic should be Bioscience: Genomic measurements', () => {
    component.passEntry.subscribe((value) => {
      console.log("value", value);
      outputValue = value;
    });

    saveButton.click();
    expect(outputValue[0]).toEqual("Bioscience: Genomic measurements");
  });

  it("Return value should contain Topic2", () => {
    component.passEntry.subscribe((value) => {
      outputValue = value;
    });

    component.tempTopics.push("Topic2");
    saveButton.click();
    expect(outputValue[1]).toEqual("Topic2");
  });
});
