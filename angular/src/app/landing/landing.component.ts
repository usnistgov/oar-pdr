import { Component, OnInit, OnDestroy, AfterViewInit, ElementRef, ViewChildren } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormBuilder, FormGroup } from '@angular/forms';

import { BrowserModule ,Title} from '@angular/platform-browser';

import { ActivatedRoute }     from '@angular/router';
// import { SearchService } from '../shared/index';

import 'rxjs/add/operator/map';
import { Subscription } from 'rxjs/Subscription';
import { SelectItem } from 'primeng/primeng';
import { Message } from 'primeng/components/common/api';
import { TreeModule,TreeNode, Tree, MenuItem,OverlayPanelModule,
  FieldsetModule,PanelModule,ContextMenuModule,
  MenuModule, DialogModule } from 'primeng/primeng';
import * as _ from 'lodash';
import { CommonModule } from '@angular/common';

import { Collaspe } from './collapseDirective/collapse.directive';

import { environment } from '../../environments/environment';
import { SearchResolve } from "./search-service.resolve";
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
//import * as jsPDF  from 'jspdf';
import { CommonVarService } from "../shared/common-var/index";
declare var Ultima: any;
declare var jQuery: any;

@Component({
  selector: 'app-landing',
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css']
})
export class LandingComponent implements OnInit {
  name = 'World';
    layoutCompact: boolean = true;
    layoutMode: string = 'horizontal';
    profileMode: string = 'inline';
    msgs: Message[] = [];
    exception : string;
    errorMsg: string;
    status: string;
    errorMessage: string;
    errorMessageArray: string[];
    //searchResults: any[] = [];
    searchValue:string;
    recordDisplay:any = [];
    keyword:string;
    summaryCandidate: any[];
    findId: string;
    leftmenu: MenuItem[];
    rightmenu: MenuItem[];
    similarResources: boolean = false;
    similarResourcesResults: any[]=[];
    qcriteria:string = '';
    selectedFile: TreeNode;
    isDOI = false;
    isEmail = false;
    citeString:string = '';
    type: string = '';
    process : any[];
    requestedId : string = '';
    isCopied: boolean = false;
    distdownload: string = '';
    serviceApi: string = '';
    metadata: boolean = false;
    pdrApi : string = "environment.PDRAPI";
    private _routeParamsSubscription: Subscription;
    private files: TreeNode[] = [];
    private fileHierarchy : TreeNode;
    private rmmApi : string = environment.RMMAPI;
    private sdpLink : string = environment.SDPAPI;
    private distApi : string = environment.DISTAPI;
    private metaApi : string = environment.METAPI;
    private landing : string = environment.LANDING;
    private displayIdentifier :string;
    private dataHierarchy: any[]=[];
    isResultAvailable: boolean = true;
    contenteditable:boolean = false;
    editContent: boolean = false;
    loginuser: boolean = false;

    displayContact: boolean = false;

    
  /**
   * Creates an instance of the SearchPanel
   *
   */
  constructor(private route: ActivatedRoute, private el: ElementRef, 
              private titleService: Title, private commonVar : CommonVarService) {
   
    this.commonVar.userObservable.subscribe(value => {
      this.loginuser = value;
      console.log(this.loginuser);
    })
    
  }

   /**
   * If Search is successful populate list of keywords themes and authors
   */
  onSuccess(searchResults:any[]) {
    // let rmmdata = [
    //     {"_id":{"timestamp":1508225827,"machineIdentifier":8777488,"processIdentifier":291,"counter":16692557,"time":1508225827000,"date":1508225827000,"timeSecond":1508225827},"_schema":"https://www.nist.gov/od/dm/nerdm-schema/v0.1#","topic":[{"scheme":"https://www.nist.gov/od/dm/nist-themes/v1.0","tag":"Physics: Optical physics","@type":"Concept"}],"references":[{"refType":"IsReferencedBy","_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/v0.1#/definitions/DCiteDocumentReference"],"@id":"#ref:10.1364/OE.24.014100","@type":"deo:BibliographicReference","location":"https://dx.doi.org/10.1364/OE.24.014100"}],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/PublicDataResource"],"landingPage":"https://www.nist.gov/nvl/project-index-optical-method-sorting-nanoparticles-size","dataHierarchy":[{"filepath":"1491_optSortSphEvaluated20160701.cdf"},{"filepath":"1491_optSortSphEvaluated20160701.cdf.sha256"},{"filepath":"1491_optSortSphEvaluated20160701.nb"},{"filepath":"1491_optSortSph20160701.m"},{"filepath":"1491_optSortSphEvaluated20160701.nb.sha256"},{"filepath":"1491_optSortSph20160701.m.sha256"}],"title":"OptSortSph: Sorting Spherical Dielectric Particles in a Standing-Wave Interference Field","theme":["Optical physics"],"inventory":[{"forCollection":"","descCount":7,"childCollections":[],"childCount":7,"byType":[{"descCount":7,"forType":"dcat:Distribution","childCount":7},{"descCount":1,"forType":"nrd:Hidden","childCount":1},{"descCount":6,"forType":"nrdp:DataFile","childCount":6}]}],"programCode":["006:045"],"@context":["https://www.nist.gov/od/dm/nerdm-pub-context.jsonld",{"@base":"ark:/88434/mds00hw91v"}],"description":["Software to predict the optical sorting of particles in a standing-wave laser interference field"],"language":["en"],"bureauCode":["006:55"],"contactPoint":{"hasEmail":"mailto:zachary.levine@nist.gov","fn":"Zachary Levine"},"accessLevel":"public","@id":"ark:/88434/mds00hw91v","publisher":{"@type":"org:Organization","name":"National Institute of Standards and Technology"},"doi":"doi:10.18434/T4SW26","keyword":["optical sorting","laser interference field","nanoparticles","convection of fluid"],"license":"https://www.nist.gov/open/license","modified":"2016-07-01","ediid":"3A1EE2F169DD3B8CE0531A570681DB5D1491","components":[{"description":"A .cdf version of the Mathematica notebook. A reader for this file is available at: http://www.wolfram.com/cdf/","filepath":"1491_optSortSphEvaluated20160701.cdf","title":"CDF version of the Mathematica notebook","mediaType":"application/vnd.wolfram.player","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.cdf","@id":"cmps/1491_optSortSphEvaluated20160701.cdf","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSphEvaluated20160701.cdf.sha256","title":"SHA-256 file for the CDF version of the Mathematica notebook","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.cdf.sha256","@id":"cmps/1491_optSortSphEvaluated20160701.cdf.sha256","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"accessURL":"https://doi.org/10.18434/T4SW26","description":"Software to predict the optical sorting of particles in a standing-wave laser interference field","format":"Digital Object Identifier, a persistent identifier","title":"DOI access for OptSortSph: Sorting Spherical Dielectric Particles in a Standing-Wave Interference Field","mediaType":"application/zip","@id":"#doi:10.18434/T4SW26","@type":["nrd:Hidden","dcat:Distribution"]},{"filepath":"1491_optSortSphEvaluated20160701.nb","title":"Download for the Mathematica notebook","mediaType":"application/mathematica","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.nb","@id":"cmps/1491_optSortSphEvaluated20160701.nb","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSph20160701.m","title":"ASCII version of the code (without documentation)","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSph20160701.m","@id":"cmps/1491_optSortSph20160701.m","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSphEvaluated20160701.nb.sha256","title":"SHA-256 file for Mathematica download file","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSphEvaluated20160701.nb.sha256","@id":"cmps/1491_optSortSphEvaluated20160701.nb.sha256","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]},{"filepath":"1491_optSortSph20160701.m.sha256","title":"SHA-256 file for ASCII version of the code","mediaType":"text/plain","downloadURL":"https://s3.amazonaws.com/nist-midas/1491_optSortSph20160701.m.sha256","@id":"cmps/1491_optSortSph20160701.m.sha256","@type":["nrdp:DataFile","dcat:Distribution"],"_extensionSchemas":["https://www.nist.gov/od/dm/nerdm-schema/pub/v0.1#/definitions/DataFile"]}],"@type":["nrdp:PublicDataResource"]}];
        
    if(searchResults["ResultCount"] === undefined || searchResults["ResultCount"] !== 1)
      this.recordDisplay = searchResults;
    else if(searchResults["ResultCount"] !== undefined && searchResults["ResultCount"] === 1)
      this.recordDisplay = searchResults["ResultData"][0];

      //this.recordDisplay = rmmdata[0];
       this.type = this.recordDisplay['@type'];
    this.titleService.setTitle(this.recordDisplay['title']);
    console.log(this.recordDisplay['title']);
    this.createDataHierarchy();
    if(this.recordDisplay['doi'] !== undefined && this.recordDisplay['doi'] !== "" )
      this.isDOI = true;
    if(this.recordDisplay['contactPoint'].hasEmail !== undefined && this.recordDisplay['contactPoint'].hasEmail !== "")
      this.isEmail = true;
    
    this.updateLeftMenu();
    this.updateRightMenu();
  }

  /**
   * If search is unsuccessful push the error message
   */
  onError(error:any) {
    this.exception = (<any>error).ex;
    this.errorMsg = (<any>error).message;
    this.status = (<any>error).httpStatus;
    this.msgs.push({severity:'error', summary:this.errorMsg + ':', detail:this.status + ' - ' + this.exception});
  }

  /**
   * Update Leftside menu on landing page
   */
  updateLeftMenu(){
    var itemsMenu: any[] = [];
    var descItem = this.createMenuItem ("Description",'',(event)=>{
      this.metadata = false; this.similarResources =false;
    },'');

    var refItem = this.createMenuItem ("References",'',(event)=>{
      this.metadata = false; this.similarResources =false;

    },'');

    var filesItem = this.createMenuItem("Files",'', (event)=>{
      this.metadata = false;
      this.similarResources =false;
    },'');

    var metaItem = this.createMenuItem("Metadata",'',(event)=>{
      this.metadata = true; this.similarResources =false;},'');

    itemsMenu.push(descItem);
    if(this.checkReferences())
      itemsMenu.push(refItem);
    if(this.files.length !== 0)
      itemsMenu.push(filesItem);
    itemsMenu.push(metaItem);

    this.leftmenu = [{
      label: 'Table of Contents',
      command: (event)=>{ window.location.href="#";},
      items: itemsMenu
    }];
  }

  viewmetadata(){
    this.metadata = true; this.similarResources =false;
  }
  createMenuItem(label :string, icon:string, command: any, url : string ){
    let testItem : any = {};
    testItem.label = label;
    testItem.icon = icon;
    if(command !== '')
      testItem.command = command;
    if(url !== '')
      testItem.url = url;
    return testItem;
  }

  
/**
 * Update right side panel on landing page
 */
updateRightMenu(){
      
      this.serviceApi = this.landing+"records?@id="+this.recordDisplay['@id']; 
      if(!_.includes(this.landing, "rmm"))
        this.serviceApi = this.landing+this.recordDisplay['ediid'];

      this.distdownload = this.distApi+"ds/zip?id="+this.recordDisplay['@id'];
      //this.distdownload = this.distApi+"/"+this.recordDisplay['@id']+"?format=zip";
      
    var itemsMenu: any[] = [];
    var homepage = this.createMenuItem("Visit Home Page",  "faa faa-external-link", '',this.recordDisplay['landingPage']);
    var download = this.createMenuItem("Download all data","faa faa-file-archive-o", '', this.distdownload);
    var metadata = this.createMenuItem("Export JSON", "faa faa-file-o",'',this.serviceApi);
    
    var licenseItem = this.createMenuItem("License Statement",  "faa faa-external-link","",
                        this.recordDisplay['license'] ) ;

    var similarRes = this.createMenuItem ("Similar Resources", "faa faa-external-link", "",
                       this.sdpLink+"/#/search?q=keyword="+this.recordDisplay['keyword']+"&key=&queryAdvSearch=yes");                 
      
        let authlist = "";
        if (this.recordDisplay['authors']) {    
            for(let auth of this.recordDisplay['authors'])
                authlist = authlist+auth.familyName+",";
        }
        
    var resourcesByAuthor = this.createMenuItem ('Resources by Authors',"faa faa-external-link","",
                     this.sdpLink+"/#/search?q=authors.familyName="+authlist+"&key=&queryAdvSearch=yes");
   

      itemsMenu.push(homepage);
        if (this.files.length != 0)
            itemsMenu.push(download);
        itemsMenu.push(metadata);   
         
      this.rightmenu = [{
            label: 'Access ', 
            items: itemsMenu
        },
        {
            label: 'Use', 
            items: [
                {label: 'Cite this resource',  icon: "faa faa-angle-double-right",command: (event)=>{
                    this.citeString = "";
                    let date =  new Date(); 

                    if(this.recordDisplay['authors'] !==  null && this.recordDisplay['authors'] !==  undefined){

                        for(let author of this.recordDisplay['authors']) { 
                         if(author.familyName !== null && author.familyName !== undefined) 
                            this.citeString += author.familyName +' ';
                         if(author.givenName !== null && author.givenName !== undefined) 
                            this.citeString +=  author.givenName+' ';
                         if(author.middleName !== null && author.middleName !== undefined) 
                            this.citeString += author.middleName;
                         this.citeString +=", ";
                        }
                    } 
                    else if(this.recordDisplay['contactPoint']) {
                        if(this.recordDisplay['contactPoint'].fn !== null && this.recordDisplay['contactPoint'].fn !== undefined)
                        this.citeString += this.recordDisplay['contactPoint'].fn+ ", ";
                    }
                    if(this.recordDisplay['title']!== null && this.recordDisplay['title']!== 'undefined' )
                        this.citeString += this.recordDisplay['title'] +", ";
                    if(this.recordDisplay['doi']!== null && this.recordDisplay['doi']!== 'undefined' )
                        this.citeString += this.recordDisplay['doi'];
                    this.citeString += ", access:"+date;
                    this.showDialog();
              }},
             licenseItem
           ]
        },{
            label: 'Find',   items: [
                similarRes,
                resourcesByAuthor
                ]
      }
    ];
  }

  /**
   * Get the params OnInit
   */
  ngOnInit() {
     var paramid = this.route.snapshot.paramMap.get('id');
      this.files =[];
      this.route.data.map(data => data.searchService ).subscribe((res)=>{
        console.log("mydata ::::"+res);
        this.onSuccess(res);
    });
    
  }

  ngOnDestroy() {
    //this._routeParamsSubscription.unsubscribe();
  }

  ngAfterViewInit(){
  }
  //This is to check if empty
  isEmptyObject(obj) {
    return (Object.keys(obj).length === 0);
  }

  createDataHierarchy(){
    if (this.recordDisplay['dataHierarchy'] == null )
      return;
    for(let fields of this.recordDisplay['dataHierarchy']){
      if( fields.filepath != null) {
        if(fields.children != null)
          this.files.push(this.createChildrenTree(fields.children,
            fields.filepath));
        else
          this.files.push(this.createFileNode(fields.filepath,
            fields.filepath));
      }
    }
  }

  createChildrenTree(children:any[], filepath:string){
    let testObj:TreeNode = {};
    testObj= this.createTreeObj(filepath.split("/")[filepath.split("/").length-1],filepath);
    testObj.children=[];
    for(let child of children){
      let fname = child.filepath.split("/")[child.filepath.split("/").length-1];
      if( child.filepath != null) {
        if(child.children != null)
          testObj.children.push(this.createChildrenTree(child.children,
            child.filepath));
        else
          testObj.children.push(this.createFileNode(fname,
            child.filepath));
      }
    }
    return testObj;
  }

  createTreeObj(label :string, data:string){
    let testObj : TreeNode = {};
    testObj = {};
    testObj.label = label;
    testObj.data = data;
    if(label == "Files")
      testObj.expanded = true;
    testObj.expandedIcon = "faa faa-folder-open";
    testObj.collapsedIcon =  "faa faa-folder";
    return testObj;
  }
  createFileNode(label :string, data:string){
    let endFileNode:TreeNode = {};
    endFileNode.label = label;
    endFileNode.data = data;
    endFileNode.icon = "faa faa-file-o";
    endFileNode.expandedIcon = "faa faa-folder-open";
    endFileNode.collapsedIcon =  "faa fa-folder";
    return endFileNode;
  }

  clicked = false;
  expandClick(){
    this.clicked = !this.clicked;
    return this.clicked;
  }

  clickContact = false;
  expandContact(){
    this.clickContact = !this.clickContact;
    return this.clickContact;
  }
  display: boolean = false;

  showDialog() {
    this.display = true;
  }
  closeDialog(){
    this.display = false;
  }

  public setTitle( newTitle: string) {
    this.titleService.setTitle( newTitle );
  }
  
  checkReferences(){
    if(Array.isArray(this.recordDisplay['references']) ){
      for(let ref of this.recordDisplay['references'] ){
        if(ref.refType == "IsDocumentedBy") return true;
      }
    }
  }

  isArray(obj : any ) {
    return Array.isArray(obj);
  }

  isObject(obj: any)
  {
    if (typeof obj === "object") {
      return true;
    }
  }
  
  toggleContenteditable(event){
    var target = event.target || event.srcElement || event.currentTarget;
    var idAttr = target.attributes.id;
    var value = idAttr.nodeValue;
      alert(value);
    this.contenteditable = !this.contenteditable; //`this.` was missing in later assignment
  }
  editContents(){
    this.editContent = !this.editContent;
    this.contenteditable = !this.contenteditable;
  }
  saveContents(){
    this.contenteditable = !this.contenteditable;
  }
  showContactDialog() {
    this.displayContact = true;
  }
}
