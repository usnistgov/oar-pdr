import { Component, OnInit, ElementRef } from '@angular/core';
import { Title, Meta} from '@angular/platform-browser';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { TreeNode } from 'primeng/primeng';
import { MenuItem } from 'primeng/api';
import * as _ from 'lodash';
import 'rxjs/add/operator/map';
import { Subscription } from 'rxjs/Subscription';
import { environment } from '../../environments/environment';
import { AppConfig } from '../shared/config-service/config.service';

@Component({
  selector: 'app-landing',
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css']
})
export class LandingComponent implements OnInit {
    layoutCompact: boolean = true;
    layoutMode: string = 'horizontal';
    profileMode: string = 'inline';
    // msgs: Message[] = [];
    exception : string;
    errorMsg: string;
    status: string;
    searchValue:string;
    record:any = [];
    keyword:string;
    findId: string;
    leftmenu: MenuItem[];
    rightmenu: MenuItem[];
    similarResources: boolean = false;
    similarResourcesResults: any[]=[];
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
    private distApi : string = environment.DISTAPI;
    private landing : string = environment.LANDING;
    private sdpLink : string = environment.SDPAPI;
    private displayIdentifier :string;
    private dataHierarchy: any[]=[];
    isResultAvailable: boolean = true;
    isId : boolean = true;
    displayContact: boolean = false; 
    private meta: Meta;
  /**
   * Creates an instance of the SearchPanel
   *
   */
  constructor(private route: ActivatedRoute, private el: ElementRef, 
              private titleService: Title, private appConfig : AppConfig, private router: Router
              ) {
    
    this.rmmApi = this.appConfig.getRMMapi();
    this.distApi = this.appConfig.getDistApi();
    this.landing = this.appConfig.getLandingBackend();

    router.events.subscribe(s => {
      if (s instanceof NavigationEnd) {
        const tree = router.parseUrl(router.url);
        if (tree.fragment) {
          const element = document.querySelector("#" + tree.fragment);
          
          if (element) { 
            element.scrollIntoView(true); 
           }
        }
      }
    });
  }

   /**
   * If Search is successful populate list of keywords themes and authors
   */
  onSuccess(searchResults:any[]) {
    
    if(searchResults["ResultCount"] === undefined || searchResults["ResultCount"] !== 1)
      this.record = searchResults;
    else if(searchResults["ResultCount"] !== undefined && searchResults["ResultCount"] === 1)
      this.record = searchResults["ResultData"][0];
    this.type = this.record['@type'];
    this.titleService.setTitle(this.record['title']);
    // this.meta.addTag({ "testdescription": this.record['description'] });
    this.createDataHierarchy();
    if(this.record['doi'] !== undefined && this.record['doi'] !== "" )
      this.isDOI = true;
    if( "hasEmail" in this.record['contactPoint'])  
     this.isEmail = true;
    if(this.record["@id"] === undefined || this.record["@id"] === "" ){
        this.isId = false;
        return;
    }
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
    //this.msgs.push({severity:'error', summary:this.errorMsg + ':', detail:this.status + ' - ' + this.exception});
  }

  /**
   * Update Leftside menu on landing page
   */
  updateLeftMenu(){
    var itemsMenu: MenuItem[] = [];
    var descItem = this.createMenuItem ("Description",'',(event)=>{
      this.metadata = false; this.similarResources =false;
      this.router.navigate(['/od/id/', this.record.ediid],{fragment:'description'});
    },'');

    var refItem = this.createMenuItem ("References",'',(event)=>{
      this.metadata = false; this.similarResources =false;
      this.router.navigate(['/od/id/', this.record.ediid],{fragment:'reference'});

    },'');

    var filesItem = this.createMenuItem("Data Access",'', (event)=>{
      this.metadata = false;
      this.similarResources =false;
      this.router.navigate(['/od/id/', this.record.ediid],{fragment:'dataAccess'});
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
      items: itemsMenu
    }
  ];
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
      
  this.serviceApi = this.landing+"records?@id="+this.record['@id']; 
  if(!_.includes(this.landing, "rmm"))
    this.serviceApi = this.landing+this.record['ediid'];
  this.distdownload = this.distApi+"ds/zip?id="+this.record['@id'];
      
  var itemsMenu: any[] = [];
  var homepage = this.createMenuItem("Visit Home Page",  "faa faa-external-link", '',this.record['landingPage']);
  var download = this.createMenuItem("Download all data","faa faa-file-archive-o", '', this.distdownload);
  var metadata = this.createMenuItem("Export JSON", "faa faa-file-o",'',this.serviceApi);
    
      
  let authlist = "";
  if (this.record['authors']) {    
      for(let auth of this.record['authors']) authlist = authlist+auth.familyName+",";
  }
        
  var resourcesByAuthor = this.createMenuItem ('Resources by Authors',"faa faa-external-link","",this.sdpLink+"/#/search?q=authors.familyName="+authlist+"&key=&queryAdvSearch=yes");
  var similarRes = this.createMenuItem ("Similar Resources", "faa faa-external-link", "",this.sdpLink+"/#/search?q=keyword="+this.record['keyword']+"&key=&queryAdvSearch=yes");                
  var license = this.createMenuItem("License Statement",  "faa faa-external-link","",this.record['license'] ) ;
  var citation = this.createMenuItem('Cite this resource', "faa faa-angle-double-right",(event)=>{ this.getCitation(); this.showDialog(); },'');


    itemsMenu.push(homepage);
    if (this.files.length != 0) 
      itemsMenu.push(download);
    itemsMenu.push(metadata);   

  this.rightmenu = [{ label: 'Access ', items: itemsMenu },
      { label: 'Use',   items: [ citation, license ] },
      { label: 'Find',   items: [ similarRes, resourcesByAuthor ]}];
  
  }

  getCitation(){
    this.citeString = "";
    let date =  new Date(); 
      if(this.record['authors'] !==  null && this.record['authors'] !==  undefined){
        for(let author of this.record['authors']) { 
          if(author.familyName !== null && author.familyName !== undefined) 
            this.citeString += author.familyName +' ';
          if(author.givenName !== null && author.givenName !== undefined) 
            this.citeString +=  author.givenName+' ';
          if(author.middleName !== null && author.middleName !== undefined) 
            this.citeString += author.middleName;
        }
      } else if(this.record['contactPoint']) {
          if(this.record['contactPoint'].fn !== null && this.record['contactPoint'].fn !== undefined)
            this.citeString += this.record['contactPoint'].fn;
      }
      if(this.record['issued'] !==  null && this.record['issued'] !==  undefined){
        this.citeString += " ("+ _.split(this.record['issued'],"-")[0]+") ";}
      if(this.citeString !== "") this.citeString +=", ";
      if(this.record['title']!== null && this.record['title']!== undefined )
        this.citeString += this.record['title'] +", ";
      if(this.record['publisher']){
        if(this.record['publisher'].name !== null && this.record['publisher'].name !== undefined)
          this.citeString += this.record['publisher'].name;
      }
      if(this.isDOI)   this.citeString += ", "+ this.record['doi'];
      this.citeString += " (Accessed: "+ date.getFullYear()+"-"+(date.getMonth()+1)+"-"+date.getDate()+")";
  }

  /**
   * Get the params OnInit
   */
  ngOnInit() {

    var paramid = this.route.snapshot.paramMap.get('id');
    this.files =[];
    
      this.route.data.map(data => data.searchService )
       .subscribe((res)=>{
         this.onSuccess(res);
       }, error =>{
       console.log("There is an error in searchservice.");
       this.onError(" There is an error");
       });
    
  }

  ngAfterViewInit(){}

  //This is to check if empty
  isEmptyObject(obj) {
    return (Object.keys(obj).length === 0);
  }

  createDataHierarchy(){
    if (this.record['dataHierarchy'] == null )
      return;
    for(let fields of this.record['dataHierarchy']){
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
    if(Array.isArray(this.record['references']) ){
      for(let ref of this.record['references'] ){
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
  showContactDialog() {
    this.displayContact = true;
  }
}
