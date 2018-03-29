//import { Directive, ElementRef, Input } from '@angular/core';

// @Directive({ selector: '[collapse]' })
// export class CollapseComponentComponent {
//     constructor(el: ElementRef) {
//        el.nativeElement.style.backgroundColor = 'yellow';
//     }
// }

import {Directive, Input, HostBinding,ElementRef, Renderer} from '@angular/core';

@Directive({selector: '[collapse]'})
export class Collaspe {

  layoutCompact: boolean = true;
  layoutMode: string = 'horizontal';
  darkMenu: boolean = false;
  profileMode: string = 'inline';
  

  constructor( private el: ElementRef, private ren: Renderer) {
  }
 // style
    @HostBinding('style.height')
    public height:string;
    // shown
    @HostBinding('class.in')
    @HostBinding('attr.aria-expanded')
    public isExpanded:boolean = true;
    // hidden
    @HostBinding('attr.aria-hidden')
    public isCollapsed:boolean = false;
    // stale state
    @HostBinding('class.collapse')
    public isCollapse:boolean = true;
    // animation state
    @HostBinding('class.collapsing')
    public isCollapsing:boolean = false;

    @Input()
     set collapse(value:boolean) {
        this.isExpanded = value;
        this.toggle();
    }

     get collapse():boolean {
        return this.isExpanded;
    }

   
    toggle() {
        if (this.isExpanded) {
            this.hide();
        } else {
            this.show();
        }
    }

    hide() {
        this.isCollapse = false;
        this.isCollapsing = true;
      
        this.isExpanded = false;
        this.isCollapsed = true;
        this.ren.setElementStyle(this.el.nativeElement,'display', 'none');
           
        setTimeout(() => {
            this.height = '0';
             
            this.isCollapse = true;
            this.isCollapsing = false;
        }, 4);
    }

    show() {
        this.isCollapse = false;
        this.isCollapsing = true;

        this.isExpanded = true;
        this.isCollapsed = false;
        this.ren.setElementStyle(this.el.nativeElement,'display', 'block');
            
        setTimeout(() => {
            this.height = 'auto';

            this.isCollapse = true;
            this.isCollapsing = false;
        }, 4);
    }
}
