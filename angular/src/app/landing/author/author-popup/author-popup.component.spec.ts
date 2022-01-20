import { ComponentFixture, TestBed, waitForAsync  } from '@angular/core/testing';
import { AuthorPopupComponent } from './author-popup.component';
import { FormsModule } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { SearchService } from '../../../shared/search-service/index';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigModule } from '../../../config/config.module';
import { TransferState, StateKey } from '@angular/platform-browser';

describe('AuthorPopupComponent', () => {
  let component: AuthorPopupComponent;
  let fixture: ComponentFixture<AuthorPopupComponent>;
  let newAuthor = {
    "authors": [
      {
        "familyName": "Dow",
        "fn": "John Dow",
        "givenName": "John",
        "middleName": "",
        "affiliation": [
          {
            "@id": "",
            "title": "",
            "subunits": [""],
            "@type": [
              ""
            ]
          }
        ],
        "orcid": "0000-1832-8812-1125",
        "isCollapsed": false,
        "fnLocked": false,
        "dataChanged": false,
        "orcidValid": true
      }]
  };

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AuthorPopupComponent ],
      imports: [FormsModule,        
        RouterTestingModule,
        HttpClientTestingModule,
        ConfigModule],
      schemas: [NO_ERRORS_SCHEMA],
      providers: [NgbActiveModal, SearchService, TransferState]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    let tempAuthors = {author: newAuthor};

    fixture = TestBed.createComponent(AuthorPopupComponent);
    component = fixture.componentInstance;
    component.inputValue = tempAuthors;
    component.title = 'author';
    fixture.detectChanges();
  });

  it('Should create', () => {
    expect(component).toBeTruthy();
  });

  it('ORCID check', () => {
    expect(component.orcid_validation(newAuthor.authors[0].orcid)).toBeTruthy();
    component.validateOrcid(newAuthor.authors[0]);
    expect(newAuthor.authors[0].orcidValid).toBeTruthy();

    newAuthor.authors[0].orcid = "0000-1832-8812-112";
    component.validateOrcid(newAuthor.authors[0]);
    expect(newAuthor.authors[0].orcidValid).toBeFalsy();

    component.inputValue = newAuthor;
    expect(component.finalValidation()).toBeFalsy();
  });
});
