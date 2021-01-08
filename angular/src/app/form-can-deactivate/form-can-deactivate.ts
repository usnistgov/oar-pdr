import {ComponentCanDeactivate} from '../can-deactivate/component-can-deactivate';
import {NgForm} from "@angular/forms";

export abstract class FormCanDeactivate extends ComponentCanDeactivate{

 abstract get overallStatus():string;
 
 canDeactivate():boolean{
     console.log('this.overallStatus', this.overallStatus);
     return (this.overallStatus != "downloading");
  }
}