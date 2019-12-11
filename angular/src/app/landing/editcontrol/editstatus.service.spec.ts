// import { EditStatusService } from './editstatus.service';
// import { AngularEnvironmentConfigService } from '../../config/config.service';
// import { AppConfig } from '../../config/config'
// import { config } from '../../../environments/environment'

// describe('EditStatusService', () => {

//     let svc : EditStatusService = null;
//     let cfgdata = null;
//     let cfg = null;

//     beforeEach(() => {
//         cfgdata = JSON.parse(JSON.stringify(config));
//         cfgdata['enableEdit'] = true;
//         svc = new EditStatusService(new AppConfig(cfgdata));
//     });

//     it('initialize', () => {
//         expect(svc.lastUpdated).toEqual("");
//         expect(svc.editMode).toEqual(false);
//         expect(svc.userID).toBeNull();
//         expect(svc.authenticated).toBe(false);
//         expect(svc.authorized).toBe(false);
//         expect(svc.editingEnabled()).toBe(true);
//     });

//     it('setable', () => {
//         svc._setLastUpdated('today');
//         svc._setEditMode(true);
//         svc._setUserID("Hank");
//         svc._setAuthorized(false);

//         expect(svc.lastUpdated).toEqual("today");
//         expect(svc.editMode).toEqual(true);
//         expect(svc.userID).toEqual("Hank");
//         expect(svc.authenticated).toBe(true);
//         expect(svc.authorized).toBe(false);
//     });

//     it('watchable remote start', () => {
//         let started = false;
//         svc._watchRemoteStart((ev) => {
//             started = ev;
//         });
//         expect(started).toBeFalsy();
//         svc.startEditing();
//         expect(started).toBeTruthy();
//     });
// });


               
                                 
        
        
