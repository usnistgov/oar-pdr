import { Directive, HostListener, Input, ElementRef, OnInit, OnChanges, SimpleChanges, EventEmitter, Output } from '@angular/core';

@Directive({
  selector: '[ceModel]'
})
export class ContenteditableModel implements OnInit, OnChanges {
  @Input('ceDefault') ceDefault: string;
  @Input('ceModel') ceModel: string;
  @Output('ceChange') ceChange = new EventEmitter();
  constructor(private elRef: ElementRef) { }

  @HostListener('keyup', ['$event'])
  onChange($event: any) {
    const value = this.elRef.nativeElement.innerText;
    if (value === '') {
      this.setPHolderColr(true, true);
    } else {
      this.setPHolderColr(false, true);
    }
    this.ceModel = value;
    this.ceChange.emit(value);
  }
  @HostListener('click', ['$event'])
  onFocus($event: any) {
    const value = this.elRef.nativeElement.innerText;
    if (value === this.ceDefault) {
      this.elRef.nativeElement.innerText = '';
    }
    this.setPHolderColr(false, true);
  }
  @HostListener('blur', ['$event'])
  onFocusout($event: any) {
    let value = this.elRef.nativeElement.innerText;
    value = value.replace(/(\r\n|\n|\r)/gm, '');
    if (value === '') {
      this.setPHolderColr(true, false);
      this.elRef.nativeElement.innerText = this.ceDefault;
    } else {
      this.setPHolderColr(false, false);
    }
  }
  /*
   * Set the color based on actual or default placeholder color
   */
  setPHolderColr(isDefault: boolean, isFocus: boolean) {
    if (this.elRef.nativeElement.hasAttribute('placeholder')) {
      if (isDefault) {
        if (isFocus) {
          this.elRef.nativeElement.setAttribute('style', 'color: #C2C2C2 !important; border: 0px solid #00ccff !Important;padding: .5em;border-radius: 5px;box-shadow: 0px 0px 3px 3px #0066cc;');
        } else {
          this.elRef.nativeElement.setAttribute('style', 'color: #C2C2C2 !important; border: 0px solid lightgrey !Important;padding: .5em;border-radius: 5px;');
        }
      } else {
        if (isFocus) {
          this.elRef.nativeElement.setAttribute('style', 'color: #000 !important; border: 1px solid #00ccff !Important; padding: .5em;border-radius: 5px;box-shadow: 0px 0px 3px 3px #0066cc;');
        } else {
          this.elRef.nativeElement.setAttribute('style', 'color: #000 !important; border: 1px solid lightgrey !Important; padding: .5em;border-radius: 5px;');
        }
      }
    }
  }

  ngOnInit() {
    // this.elRef.nativeElement.innerText = "Enter description here...";
    this.setPHolderColr(false, true);
    this.elRef.nativeElement.focus()
  }

  /*
   * Below will be triggered if source is modified in aside section
   */
  ngOnChanges(changes: SimpleChanges) {
    const cv = changes['ceModel'].currentValue;
    if (this.elRef.nativeElement.innerText !== cv) {
      this.elRef.nativeElement.innerText = cv;
      if (cv === '') {
        this.elRef.nativeElement.innerText = this.ceDefault;
      }
    }
  }
}