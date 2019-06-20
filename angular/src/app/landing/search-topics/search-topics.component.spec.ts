import { Component, Input, ChangeDetectorRef, NgZone, NO_ERRORS_SCHEMA, ViewChild, DebugElement } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchTopicsComponent } from './search-topics.component';
import { FormsModule } from '@angular/forms';
import { DataTableModule, TreeModule } from 'primeng/primeng';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { TreeNode } from 'primeng/api';

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
      providers: [NgbActiveModal]
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

    record = {"_schema":"https://data.nist.gov/od/dm/nerdm-schema/v0.1#","topic":[{"scheme":"https://www.nist.gov/od/dm/nist-themes/v1.0","tag":"Bioscience: Genomic measurements","@type":"Concept"}],"_extensionSchemas":["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/PublicDataResource"],"landingPage":null,"dataHierarchy":[{"children":[{"filepath":"1869/ddPCR%20Raw%20Data_Stein%20et%20al%20PLOSOne%202017.zip"}],"filepath":"1869"}],"title":"Steps to achieve quantitative measurements of microRNA using two-step droplet digital PCR","theme":["Genomic measurements"],"inventory":[{"forCollection":"","descCount":3,"childCollections":["1869"],"childCount":2,"byType":[{"descCount":2,"forType":"dcat:Distribution","childCount":1},{"descCount":1,"forType":"nrd:Hidden","childCount":1},{"descCount":1,"forType":"nrdp:DataFile","childCount":0},{"descCount":1,"forType":"nrdp:Subcollection","childCount":1}]},{"forCollection":"1869","descCount":1,"childCollections":[],"childCount":1,"byType":[{"descCount":1,"forType":"dcat:Distribution","childCount":1},{"descCount":1,"forType":"nrdp:DataFile","childCount":1}]}],"programCode":["006:045"],"@context":["https://data.nist.gov/od/dm/nerdm-pub-context.jsonld",{"@base":"ark:/88434/mds00b7z7j"}],"description":["description."],"language":["en"],"bureauCode":["006:55"],"contactPoint":{"hasEmail":"mailto:erica.stein@nist.gov","fn":"Erica Sawyer"},"accessLevel":"public","@id":"ark:/88434/mds00b7z7j","publisher":{"@type":"org:Organization","name":"National Institute of Standards and Technology"},"doi":"doi:10.18434/M32Q1V","keyword":["Biotechnology","microRNAs","Biological Measurements","Genomics","Research and Analysis Methods","quantitative analysis"],"license":"https://www.nist.gov/open/license","modified":"2017-10-19","ediid":"5BD6911D381AB2E3E0531A57068151FA1869","components":[{"_extensionSchemas":["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/Subcollection"],"@id":"cmps/1869","@type":["nrdp:Subcollection"],"filepath":"/1869"},{"filepath":"/1869/ddPCR%20Raw%20Data_Stein%20et%20al%20PLOSOne%202017.zip","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1869/ddPCR%20Raw%20Data_Stein%20et%20al%20PLOSOne%202017.zip","@id":"cmps/1869/ddPCR%20Raw%20Data_Stein%20et%20al%20PLOSOne%202017.zip","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://data.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"accessURL":"https://doi.org/10.18434/M32Q1V","@id":"#doi:10.18434/M32Q1V","@type":["nrd:Hidden","dcat:Distribution"]}],"@type":["nrdp:PublicDataResource"]};

    fixture = TestBed.createComponent(SearchTopicsComponent);
    component = fixture.componentInstance;
    component.tempTopics = tempTopics;
    component.taxonomyTree = taxonomyTree;
    component.record = record;
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

  it('Save button should be called2', () => {
    component.passEntry.subscribe((value) => {
      outputValue = value;
    });

    saveButton.click();
    expect(outputValue.topic[0].tag).toEqual("Bioscience: Genomic measurements");
  });

  it("Return value should contain Topic2", () => {
    component.passEntry.subscribe((value) => {
      outputValue = value;
    });

    component.tempTopics.push("Topic2");
    saveButton.click();
    expect(outputValue.topic[1].tag).toEqual("Topic2");
  });
});
