import { Component, OnInit, Input, SimpleChanges, Output, EventEmitter, Inject } from '@angular/core';
import * as _ from 'lodash-es';
import { SearchService } from '../../shared/search-service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-pagination',
  templateUrl: './pagination.component.html',
  styleUrls: ['./pagination.component.css']
})
export class PaginationComponent implements OnInit {
    // pager object
    pager: any = {};
    prevPage: number = 1;
    startPage: number = 0;
    endPage: number = 0;
    // currentPage: number = 1;
    subscription: Subscription = new Subscription();

    @Input() totalItems: number = 0;
    @Input() currentPage: number = 1;
    @Input() pageSize: number = 10; // Default page size is 10

    constructor(private searchService: SearchService) { 

    }

    ngOnInit() {
        this.updatePager(this.currentPage);

        this.subscription.add(this.searchService.watchCurrentPage().subscribe(page => {
            if(!page) page=1;

            if(this.currentPage == page){
                return;
            }else{
                this.currentPage = page;
                this.updatePager(this.currentPage);
            }           
        }));

        this.subscription.add(this.searchService.watchTotalItems().subscribe(totalItems => {
            if(!totalItems) totalItems=0;

            if(this.totalItems == totalItems){
                return;
            }else{
                this.totalItems = totalItems;
                this.updatePager(this.currentPage);
            }           
        }));
    }

    /**
     * On destroy, unsubscribe all subscriptions
     */
    ngOnDestroy(): void {
        this.currentPage = 1;
        this.setPage(1);
        this.subscription.unsubscribe();
    }

    /**
     * Update the pager control based on the given page number
     * @param page - page number to set to
     */
    updatePager(page: number) {
        if (page < 1) {
            return;
        }
        this.prevPage = page;
        // get pager object from service
        this.pager = this.getPager(page);
    }

    /**
     * Tell parent page which page to query
     * @param page - page number to set to
     */
    setPage(page: number){
        this.currentPage = page;
        this.pager = this.getPager();
        // this.currentPageOutput.emit(page);

        this.searchService.setCurrentPage(page);
    }

    /**
     * Return the pager object based on given page
     * @param currentPage - current page number
     */    
    getPager(currentPage: number = this.currentPage){
        let totalPages = Math.ceil(this.totalItems / this.pageSize);

        if(currentPage > totalPages) {
            currentPage = 1;
            this.currentPage = 1;
        }

        let startPage: number, endPage: number;

        if (totalPages <= 5) {
            startPage = 1;
            endPage = totalPages;
        } else {
            if (currentPage <= 3) {
                startPage = 1;
                endPage = 5;
            } else if (currentPage + 1 >= totalPages) {
                startPage = totalPages - 4;
                endPage = totalPages;
            } else {
                startPage = currentPage - 2;
                endPage = currentPage+2;
            }
        }

        // the first and last pages are always displayed (except total pages = 1)
        // Following pages is used to display page #2 to total pages -1 (display 3 pages a time)
        let pages = _.range(startPage+1, endPage);

        // If total page is less than 3, pages will be hidden. 
        // But we want to set a value so it won't be null.
        if(totalPages < 3) pages = [1];

        // return object with all pager properties required by the view
        return {
            totalItems: this.totalItems,
            currentPage: currentPage,
            pageSize: this.pageSize,
            totalPages: totalPages,
            startPage: startPage,
            endPage: endPage,
            pages: pages
        };
    }
}
