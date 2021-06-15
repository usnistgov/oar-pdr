import { Component, OnInit, Input, Output, EventEmitter, ViewChild, ElementRef, HostListener } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { SearchService } from '../../../shared/search-service/index';
import { deepCopy } from '../../../utils';
import { AuthorService } from '../author.service';

@Component({
  selector: 'app-author-popup',
  templateUrl: './author-popup.component.html',
  styleUrls: ['./author-popup.component.css']
})
export class AuthorPopupComponent implements OnInit {
  @Input() inputValue: any;
  @Input() field: string;
  @Input() title?: string;
  @Output() returnValue: EventEmitter<any> = new EventEmitter();

  isAuthorCollapsed: boolean = false;
  originalAuthors: any;
  errorMsg: any;
  affiliationList: any[] = [];

  @ViewChild('authors') private myScrollContainer: ElementRef;

  constructor(
    public activeModal: NgbActiveModal,
    private searchService: SearchService,
    private authorService: AuthorService) { 

    }

  ngOnInit() {
    if (this.inputValue != undefined)
      this.originalAuthors = deepCopy(this.inputValue);
    else
      this.inputValue = {};

    this.getAffiliationList();
  }


  /*
  *   Get a list of current affiliation
  */
  getAffiliationList() {
    this.searchService.getAllRecords().subscribe((result) => 
    {
      for (var i = 0; i < result.ResultData.length; i++) 
      {
        if (result.ResultData[i].authors != undefined && result.ResultData[i].authors != null) 
        {
          for (var j = 0; j < result.ResultData[i].authors.length; j++) 
          {
            if (result.ResultData[i].authors[j].affiliation != undefined) 
            {
              for (var k = 0; k < result.ResultData[i].authors[j].affiliation.length; k++) 
              {
                if (result.ResultData[i].authors[j].affiliation[k].title != undefined) 
                {
                  const existingAffiliation = this.affiliationList.filter(aff => aff.name === result.ResultData[i].authors[j].affiliation[k].title && aff.subunits === "");
                  if (existingAffiliation.length == 0) {
                    this.affiliationList.push({ "name": result.ResultData[i].authors[j].affiliation[k].title, "subunits": "" })
                    // this.organizationList.push(result.ResultData[i].authors[j].affiliation[k].title);
                  }
                }
              }
            }
          }
        }
      }
      this.affiliationList.sort((a, b) => a.name.localeCompare(b.name));
      //Put "National Institute of Standards and Technology" on top of the list
      this.affiliationList = this.affiliationList.filter(entry => entry.name != "National Institute of Standards and Technology");
      this.affiliationList.unshift({ name: "National Institute of Standards and Technology", subunits: "" });
    }, (error) => {
      console.log("There was an error getting records list.");
      console.log(error);
      this.errorMsg = error;
    });
  }

  /*
  *   Return icon class based on collapse status (top level)
  */
  getAuthorClass() {
    if (this.isAuthorCollapsed) {
      return "faa faa-arrow-circle-down icon-white";
    } else {
      return "faa faa-arrow-circle-up icon-white";
    }
  }

  /*
  *   Save author info and close popup dialog
  */
  saveAuthorInfo() 
  {
    if(this.finalValidation())
    {
        this.returnValue.emit(this.inputValue);
        this.activeModal.close('Close click')
    }
  }

  /**
   *  Final validation
   */
  finalValidation()
  {
      var validated = true;

      for(let author of this.inputValue.authors)
      {
        //Validate ORCID value
        if(!this.orcid_validation(author.orcid))
        {
            author.orcidValid = false;
            validated = false;
        }
      }

      return validated;
  }

  /**
   * ORCID validation for UI
   * @param author - author object
   */
  validateOrcid(author)
  {
    if(!this.orcid_validation(author.orcid))
    {
        author.orcidValid = false;
    }else{
        author.orcidValid = true;
    }
  }

  /**
   *  ORCID validation
   */
  orcid_validation(orcid):boolean
  {
      //Allow blank
      if(orcid == '') return true;

      const URL_REGEXP = /^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]$/;
      if (URL_REGEXP.test(orcid)) {
          return true;
      }

      return false;
  }

  /*
  *   This function is used to track ngFor loop
  */
  trackByFn(index: any, author: any) {
    return index;
  }

  /*
  *   Update full name when given name changed
  */
  onGivenNameChange(author: any, givenName: string) {
    author.dataChanged = true;
    if (!author.fnLocked) {
      author.fn = givenName + " " + (author.middleName == undefined ? " " : author.middleName + " ") + (author.familyName == undefined ? "" : author.familyName);
    }
  }

  /*
  *   Update full name when middle name changed
  */
  onMiddleNameChange(author: any, middleName: string) {
    author.dataChanged = true;
    if (!author.fnLocked) {
      author.fn = (author.givenName == undefined ? " " : author.givenName + " ") + middleName + " " + (author.familyName == undefined ? "" : author.familyName);
    }
  }

  /*
  *   Update full name when middle name changed
  */
  onFamilyNameChange(author: any, familyName: string) {
    author.dataChanged = true;
    if (!author.fnLocked) {
      author.fn = (author.givenName == undefined ? " " : author.givenName + " ") + (author.middleName == undefined ? " " : author.middleName + " ") + familyName;
    }
  }

  /*
  *   Lock full name when full name changed
  */
  onFullNameChange(author: any, familyName: string) {
    author.dataChanged = true;
    if (!author.fnLocked) {
      author.fnLocked = true;
    }
  }

  /*
  *   Return header bar background color based on the data status
  */
  getHeaderBackgroundColor(author: any) {
    if (author.dataChanged) {
      return "green";
    } else {
      return "burlywood";
    }
  }

  /*
  *   Return header bar background color based on the data status
  */
  getHeaderForegroundColor(author: any) {
    if (author.dataChanged) {
      return "white";
    } else {
      return "black";
    }
  }

  /*
  *   Return icon class based on collapse status
  */
  getTitleClass(author: any) {
    if (author.isCollapsed) {
      if (author.dataChanged) {
        return "faa faa-arrow-circle-down icon-white";
      } else {
        return "faa faa-arrow-circle-down";
      }
    } else {
      if (author.dataChanged) {
        return "faa faa-arrow-circle-up icon-white";
      } else {
        return "faa faa-arrow-circle-up";
      }
    }
  }

  /*
  *   Set image color
  */
  getTitleImgClass(author) {
    if (author.dataChanged) {
      return "filter-white";
    } else {
      return "filter-black";
    }
  }

  /*
  *   Add author
  */
  addAuthor() {
    var newAuthor = this.authorService.getBlankAuthor();
    this.inputValue.authors.push(newAuthor);
    
    setTimeout(() => {
        this.scrollToBottom(this.myScrollContainer.nativeElement);
    }, 0);
  }

  /**
   * Scroll to the bottom of the target element
   * @param el target element object
   */
  scrollToBottom(el): void {
    el.scroll({
        top: this.myScrollContainer.nativeElement.scrollHeight,
        left: 0,
        behavior: 'smooth'
    });
  }

  /*
  *   Discard current changes to the author, reset to original value
  */
  resetAuthor(author: any, i: number) {
    if (i > this.originalAuthors.authors.length-1) {
      this.deleteAuthor(author);
    } else {
      this.inputValue.authors[i] = deepCopy(this.originalAuthors.authors[this.inputValue.authors[i].originalIndex]);
      author.dataChanged = false;
      author.fnLocked = false;
      author.isCollapsed = false;
    }

  }

  /*
  *   Move author up
  */
  moveAuthorUp(author: any, i: number) {
    var tempAuth01 = deepCopy(this.inputValue.authors[i - 1]);
    var tempAuth02 = deepCopy(this.inputValue.authors[i]);
    this.inputValue.authors[i - 1] = deepCopy(tempAuth02);
    this.inputValue.authors[i] = deepCopy(tempAuth01);
    author.dataChanged = true;
  }

  /*
  *   Move author down
  */
  moveAuthorDown(author: any, i: number) {
    var tempAuth01 = deepCopy(this.inputValue.authors[i + 1]);
    var tempAuth02 = deepCopy(this.inputValue.authors[i]);
    this.inputValue.authors[i + 1] = deepCopy(tempAuth02);
    this.inputValue.authors[i] = deepCopy(tempAuth01);
    author.dataChanged = true;
  }

  /*
  *   Remove author from the list
  */
  deleteAuthor(author: any) {
    this.inputValue.authors = this.inputValue.authors.filter(obj => obj !== author);
  }

  /*
  *   Show/hide author details
  */
  handleAuthorDisplay() {
    this.isAuthorCollapsed = !this.isAuthorCollapsed;
    for (var author in this.inputValue.authors) {
      this.inputValue.authors[author].isCollapsed = this.isAuthorCollapsed;
    }
  }

  /*
  *   Add affiliation to an author
  */
  addAffiliation(i: number) {
    if (!this.inputValue.authors[i].affiliation)
      this.inputValue.authors[i].affiliation = [];

    this.inputValue.authors[i].affiliation.push(this.authorService.getBlankAffiliation());
    this.inputValue.authors[i].dataChanged = true;
  }

  /*
  *   Remove one affiliation from an author
  */
  deleteAffiliation(i: number, aff: any) {
    this.inputValue.authors[i].affiliation = this.inputValue.authors[i].affiliation.filter(obj => obj !== aff);
    this.inputValue.authors[i].dataChanged = true;
  }

  /*
  *   When affiliation name changed
  */
  affiliationNameChanged(message: string, i: number) {
    this.inputValue.authors[i].dataChanged = true;
  }

  /*
  *   When affiliation department/division changed
  */
  onDeptChange(author: any) {
    author.dataChanged = true;
  }
}
