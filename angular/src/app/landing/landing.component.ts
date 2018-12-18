import { Component, OnInit, ElementRef } from '@angular/core';
import { Title, Meta} from '@angular/platform-browser';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { TreeNode } from 'primeng/primeng';
import { MenuItem } from 'primeng/api';
import * as _ from 'lodash';
import 'rxjs/add/operator/map';
import { Subscription } from 'rxjs/Subscription';
import { AppConfig } from '../shared/config-service/config.service';
import {  PLATFORM_ID, APP_ID, Inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { CartService } from '../datacart/cart.service';
import { CommonVarService } from '../shared/common-var'

interface reference {
  refType? : string,
  "@id"? : string,
  label? : string,
  location? : string
}
function compare_versions(a: string, b: string) : number {
  let aflds : any[] = a.split(".");
  let bflds : any[] = b.split(".");
  let toint = function(el, i, a) {
      let e = null;
      try {
          return parseInt(el);
      } catch (e) {
          return el;
      }
  }
  aflds = aflds.map(toint);
  bflds = bflds.map(toint);
  let i :number = 0;
  let out : number = 0;
  for (i=0; i < aflds.length && i < bflds.length; i++) {
      if (typeof aflds[i] === "number") {
          if (typeof bflds[i] === "number") {
              out = <number>aflds[i] - <number>bflds[i];
              if (out != 0) return out;
          }
          else 
              return +1;
      }
      else if (typeof bflds[i] === "number") 
          return -1;
      else
          return a.localeCompare(b);
  }
  return out;
}
function compare_dates(a : string, b : string) : number {
  if (a.includes("Z"))
      a = a.substring(0, a.indexOf("Z"));
  if (a.includes("Z"))
      b = b.substring(0, a.indexOf("Z"));
   let asc = -1, bsc = -1;
  try {
      asc = Date.parse(a);
      bsc = Date.parse(b);
  } catch (e) { return 0; }
   return asc - bsc;
}
function compare_histories(a, b) {
  let out = 0;
  if (a.issued && b.issued)
      out = compare_dates(a.issued, b.issued);
  if (out == 0)
      out = compare_versions(a.version, b.version);
  return out;
}
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
    private _routeParamsSubscription: Subscription;
    private files: TreeNode[] = [];
    private fileHierarchy : TreeNode;
    private rmmApi : string = '';
    private distApi : string = '';
    private landing : string = '';
    private sdpLink : string = '';
    pdrApi : string = '';
    private displayIdentifier :string;
    private dataHierarchy: any[]=[];
    isResultAvailable: boolean = true;
    isId : boolean = true;
    displayContact: boolean = false; 
    private meta: Meta;
    private newer : reference = {};  
    navigationSubscription : any;
  /**
   * Creates an instance of the SearchPanel
   *
   */
  constructor(private route: ActivatedRoute, private el: ElementRef, 
              private titleService: Title, private appConfig : AppConfig, private router: Router
              ,@Inject(PLATFORM_ID) private platformId: Object,
              @Inject(APP_ID) private appId: string,
              private cartService: CartService,
              private commonVarService: CommonVarService) {
    
    this.rmmApi = this.appConfig.getRMMapi();
    this.distApi = this.appConfig.getDistApi();
    this.landing = this.appConfig.getLandingBackend();
    this.pdrApi = this.appConfig.getPDRApi();
    this.sdpLink = this.appConfig.getSDPApi();
  }

   /**
   * If Search is successful populate list of keywords themes and authors
   */
  onSuccess(searchResults:any[]) {
    if(searchResults["ResultCount"] === undefined || searchResults["ResultCount"] !== 1)
      this.record = searchResults;
    else if(searchResults["ResultCount"] !== undefined && searchResults["ResultCount"] === 1)
      this.record = searchResults["ResultData"][0];

      if(this.record["@id"] === undefined || this.record["@id"] === "" ){
        this.isId = false;
        return;
    }  

    this.type = this.record['@type'];
    this.titleService.setTitle(this.record['title']);
    //this.meta.addTag({ "testdescription": this.record['description'] });
    //let dh = new ResComponents(this.record['components']).dataHierarchy();
    this.createNewDataHierarchy();
    if(this.record['doi'] !== undefined && this.record['doi'] !== "" )
      this.isDOI = true;
    if( "hasEmail" in this.record['contactPoint'])  
     this.isEmail = true;
     this.assessNewer();
    
    this.updateMenu();

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
      testItem.target ="_blank";
  return testItem;
}


/**
 * Update menu on landing page
 */
updateMenu(){
      
  this.serviceApi = this.landing+"records?@id="+this.record['@id']; 
  if(!_.includes(this.landing, "rmm"))
    this.serviceApi = this.landing+this.record['ediid'];
  this.distdownload = this.distApi+"ds/zip?id="+this.record['@id'];
      
  var itemsMenu: MenuItem[] = [];
  var metadata = this.createMenuItem("Export JSON", "faa faa-file-o",'',this.serviceApi);   
  let authlist = "";
  if (this.record['authors']) {    
      for(let auth of this.record['authors']) authlist = authlist+auth.familyName+",";
  }
  
  var resourcesByAuthor = this.createMenuItem ('Resources by Authors',"faa faa-external-link","",
                                   this.sdpLink+"/#/search?q=authors.familyName="+authlist+"&key=&queryAdvSearch=yes");
  var similarRes = this.createMenuItem ("Similar Resources", "faa faa-external-link", "",
                              this.sdpLink+"/#/search?q="+this.record['keyword']+"&key=&queryAdvSearch=yes");                
  var license = this.createMenuItem("Fair Use Statement",  "faa faa-external-link","",this.record['license'] ) ;
  var citation = this.createMenuItem('Citation', "faa faa-angle-double-right",
                          (event)=>{ this.getCitation(); this.showDialog(); },'');
  var metaItem = this.createMenuItem("View Metadata","faa faa-bars",
                          (event)=>{ this.goToSelection(true, false, 'metadata'); },'');
  itemsMenu.push(metaItem);
  itemsMenu.push(metadata);   

  var descItem = this.createMenuItem ("Description","faa faa-arrow-circle-right",
                            (event)=>{ this.goToSelection(false, false, 'description'); },"");

  var refItem = this.createMenuItem ("References","faa faa-arrow-circle-right ",
                            (event)=>{ this.goToSelection(false,false, 'reference'); },'');

  var filesItem = this.createMenuItem("Data Access","faa faa-arrow-circle-right", 
                            (event)=>{ this.goToSelection(false,false,'dataAccess');  },'');

  var itemsMenu2:MenuItem[] = [];
      itemsMenu2.push(descItem);
  if(this.files.length !== 0 || (this.record['landingPage'] && this.record['landingPage'].indexOf('/od/id') === -1 ))
        itemsMenu2.push(filesItem);
  if(this.record['references'])
        itemsMenu2.push(refItem);
 
  this.rightmenu = [ { label: 'Go To ..', items: itemsMenu2},
      { label: 'Record Details', items: itemsMenu },
      { label: 'Use',   items: [ citation, license ] },
      { label: 'Find',   items: [ similarRes, resourcesByAuthor ]}];
}

/**
 * Function creates Citation string to be displayed by using metadata in the record
 */
 getCitation(){
    this.citeString = "";
    let date =  new Date(); 
      if(this.record['authors'] !==  null && this.record['authors'] !==  undefined){
         for( let i=0; i < this.record['authors'].length; i++){
             let author = this.record['authors'][i];
             if(author.familyName !== null && author.familyName !== undefined)
                 this.citeString += author.familyName +', ';
             if(author.givenName !== null && author.givenName !== undefined)
                 this.citeString +=  author.givenName;
             if(author.middleName !== null && author.middleName !== undefined)
                 this.citeString += author.middleName;
             if( i != this.record['authors'].length-1 )    
                  this.citeString +=', ' ;
         }

      } else if(this.record['contactPoint']) {
          if(this.record['contactPoint'].fn !== null && this.record['contactPoint'].fn !== undefined)
            this.citeString += this.record['contactPoint'].fn;
      }
      if(this.record['issued'] !==  null && this.record['issued'] !==  undefined){
        this.citeString += " ("+ _.split(this.record['issued'],"-")[0]+")";}
      if(this.citeString !== "") this.citeString +=", ";
      if(this.record['title']!== null && this.record['title']!== undefined )
        this.citeString += this.record['title'] +", ";
      if(this.record['publisher']){
        if(this.record['publisher'].name !== null && this.record['publisher'].name !== undefined)
          this.citeString += this.record['publisher'].name;
      }
      if(this.isDOI) {
        var doistring= "https://doi.org/"+_.split(this.record['doi'],':')[1];
        this.citeString += ", "+doistring  ;
      } 
      this.citeString += " (Accessed "+ date.getFullYear()+"-"+(date.getMonth()+1)+"-"+date.getDate()+")";
  }

  /**
   * Get the params OnInit
   */
  ngOnInit() {
    this.searchValue = this.route.snapshot.paramMap.get('id');
    this.commonVarService.setEdiid(this.searchValue);
    this.files =[];
    this.route.data.map(data => data.searchService )
      .subscribe((res)=>{
        this.onSuccess(res);
      }, error =>{
        console.log("There is an error in searchservice.");
        this.onError(" There is an error");
        // throw new ErrorComponent(this.route);
      });
  }

  goToSelection(isMetadata: boolean, isSimilarResources: boolean, sectionId : string){
    this.metadata = isMetadata; this.similarResources =isSimilarResources;
     if(window.location.href.includes("ark"))
      this.router.navigate(['/od/id/ark:/88434/'+this.searchValue],{fragment:sectionId});
     else
      this.router.navigate(['/od/id/', this.record.ediid],{fragment:sectionId});
      this.useFragment();
  }

  useFragment(){
    this.router.events.subscribe(s => {
      if (s instanceof NavigationEnd) {
        const tree = this.router.parseUrl(this.router.url);
        if (tree.fragment) {
          const element = document.querySelector("#" + tree.fragment);
          if (element) { 
            //element.scrollIntoView(); 
            setTimeout(() => {
            element.scrollIntoView({behavior: "smooth", block: "start", inline: "nearest"});
           }, 1);
        }
      }
    }});
  }

  ngAfterViewInit(){
    this.useFragment();
    var recordid ;
    if (this.record != null && isPlatformBrowser(this.platformId) )  {
      recordid = this.searchValue;
      if(window.location.href.includes("ark"))
        recordid = "ark:/88434/"+this.searchValue;
      window.history.replaceState( {} , '', '/od/id/'+this.searchValue );
    }
  }

  //This is to check if empty
  isEmptyObject(obj) {
    return (Object.keys(obj).length === 0);
  }

  filescount : number = 0;
  createNewDataHierarchy(){
    var testdata = {}
    // console.log("this.record: ");
    // console.log(this.record);
    if(this.record['components'] != null){
      testdata["data"] = this.arrangeIntoTree(this.record['components']);
      this.files.push(testdata);
    }
  }
  //This is to create a tree structure
  private arrangeIntoTree(paths) {
    const tree = [];
    // This example uses the underscore.js library.
    var i = 0;
    var tempfiletest = "";
    
    paths.forEach((path) => { 
     
      if(path.filepath && !path['@type'].includes('nrd:Hidden')) 
      {
        if(!path.filepath.startsWith("/"))
          path.filepath = "/"+path.filepath;

        const pathParts = path.filepath.split('/');
        pathParts.shift(); // Remove first blank element from the parts array.
        let currentLevel = tree; // initialize currentLevel to root
        
        // console.log("path:");
        // console.log(path);

        pathParts.forEach((part) => { 
          // check to see if the path already exists.
          const existingPath = currentLevel.filter(level => level.data.name === part);
          if (existingPath.length > 0) {
            
            // The path to this item was already in the tree, so don't add it again.
            // Set the current level to this path's children  
            currentLevel = existingPath[0].children;
          } else {
              const newPart = {
                data : {
                  id: i,
                  name : part,
                  mediatype: path.mediaType,
                  size: path.size,
                  downloadURL: path.downloadURL,
                  description: path.description,
                  filetype: path['@type'][0],
                  resId: path["filepath"].replace(/^.*[\\\/]/, ''),
//                  resId: path["@id"].replace(/^.*[\\\/]/, ''),
                  fullPath: path.filepath,
                  isSelected: false,
                  downloadProgress: 0,
                  downloadInstance: null,
                  zipFile: null
                },children: []
              };
              
              currentLevel.push(newPart);
              currentLevel = newPart.children;
            // }
          }
          this.filescount = this.filescount+1;
        });
      }
      i= i+1;
   });
   return tree;
  }

  visibleHistory = false;
  expandHistory() {
    this.visibleHistory = ! this.visibleHistory;
    return this.visibleHistory;
  }
   /**
   * create an HTML rendering of a version string for a NERDm VersionRelease.  
   * If there is information available for linking to version's home page, a 
   * link is returned.  Otherwise, just the version is returned (prepended 
   * with a "v").
   */
  renderRelVer(relinfo, thisversion) {
      if (thisversion == relinfo.version)
          return "v"+relinfo.version;
      return this.renderRelAsLink(relinfo, "v"+relinfo.version);
  }
   renderRelAsLink(relinfo, linktext) {
      let out : string = linktext;
      if (relinfo.location) 
          out = '<a href="'+relinfo.location+'">'+linktext+'</a>';
      else if (relinfo.refid) {
          if (relinfo.refid.startsWith("doi:"))
              out = '<a href="https://doi.org/'+relinfo.refid.substring(4)+'">'+linktext+'</a>';
          else if (relinfo.refid.startsWith("ark:/88434/"))
              out = '<a href="https://data.nist.gov/od/id/'+relinfo.refid+'">'+linktext+'</a>';
      }
      return out;
  }
   /**
   * return a rendering of a release's ID.  If possible, the ID will be 
   * rendered as a link.  If there is no ID, a link with the text "View..." 
   * is returned. 
   */
  renderRelId(relinfo, thisversion) {
      if (thisversion == relinfo.version)
          return "this version";
       let id : string = "View...";
      if (relinfo.refid) id = relinfo.refid;
      return this.renderRelAsLink(relinfo, id);
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

  /**
   * analyze the given resource metadata to determine if a newer version is 
   * available.  Currently, this looks in three places (in order) within the 
   * NERDm record:
   * <ol>
   *   <li> the 'isReplacedBy' property </li>
   *   <li> as a 'isPreviousVersionOf' reference in the references list.
   *   <li> in the 'versionHistory' property </li>
   * </ol>
   * The checks for last two places may be removed in a future release. 
   */
  assessNewer() {
    if (! this.record) return;
     // look for the 'isReplacedBy'; this is expected to be inserted into the
    // record on the fly by the server based on the values of 'replaces' in
    // all other resources.
    if (this.record['isReplacedBy']) {
        this.newer = this.record['isReplacedBy'];
        if (! this.newer['refid']) this.newer['refid'] = this.newer['@id'];
        return;
    }
     // look for a reference with refType="isPreviousVersionOf"; the
    // referenced resource is a newer version. 
    if (this.record['references']) {
        for (let ref of this.record['references']) {
            if (ref.refType == "IsPreviousVersionOf" && (ref.label || ref.refid)) {
                this.newer = ref;
                if (! this.newer['refid']) this.newer['refid'] = this.newer['@id'];
                if (! this.newer.label) this.newer.label = ref.newer.refid;
                return;
            }
        }
    }
     // look at the version history to see if there is a newer version listed
    if (this.record['version'] && this.record['versionHistory']) {
        let history = this.record['versionHistory'];
        history.sort(compare_histories);
        
        var thisversion = this.record['version'];
        var p = thisversion.indexOf('+');    // presence indicates this is an update
        if (p >= 0) thisversion = thisversion.substring(0, p)   // strip off +...
        
        if (compare_histories(history[history.length-1],
                              { version: thisversion,
                                issued: this.record['modified']  }) > 0)
        {
            // this version is older than the latest one in the history
            this.newer = history[history.length-1];
            if (! this.newer['refid']) this.newer['refid'] = this.newer['@id'];
            this.newer['label'] = this.newer['version'];
            if (! this.newer['location'] && this.newer['refid']) {
                if (this.newer['refid'].startsWith("doi:"))
                    this.newer.location = 'https://doi.org/'+this.newer['refid'].substring(4);
                else if (this.newer['refid'].startsWith("ark:/88434/"))
                    this.newer.location = 'https://data.nist.gov/od/id/'+this.newer['refid'].substring(4);
            }
        }
    }
 }

}
