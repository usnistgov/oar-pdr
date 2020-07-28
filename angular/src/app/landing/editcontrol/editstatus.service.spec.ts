import { EditStatusService } from './editstatus.service';
import { AngularEnvironmentConfigService } from '../../config/config.service';
import { AppConfig } from '../../config/config'
import { config } from '../../../environments/environment'
import { UpdateDetails, UserDetails } from './interfaces';

describe('EditStatusService', () => {

    let svc : EditStatusService = null;
    let cfgdata = null;
    let cfg = null;
    let userDetails: UserDetails = {
        'userId': 'dsn1',
        'userName': 'test01',
        'userLastName': 'NIST',
        'userEmail': 'test01@nist.gov'
    }
    let updateDetails: UpdateDetails = {
        'userDetails': userDetails,
        '_updateDate': 'today'
    }

    beforeEach(() => {
        cfgdata = JSON.parse(JSON.stringify(config));
        cfgdata['editEnabled'] = true;
        svc = new EditStatusService(new AppConfig(cfgdata));
    });

    it('initialize', () => {
        expect(svc.lastUpdated).toEqual(null);
        expect(svc.editMode).toEqual(false);
        expect(svc.userID).toBeNull();
        expect(svc.authenticated).toBe(false);
        expect(svc.authorized).toBe(false);
        expect(svc.editingEnabled()).toBe(true);
    });

    it('setable', () => {
        svc._setLastUpdated(updateDetails);
        svc._setEditMode(true);
        svc._setUserID("Hank");
        svc._setAuthorized(false);

        expect(svc.lastUpdated._updateDate).toEqual("today");
        expect(svc.lastUpdated.userDetails).toEqual(userDetails);
        expect(svc.editMode).toEqual(true);
        expect(svc.userID).toEqual("Hank");
        expect(svc.authenticated).toBe(true);
        expect(svc.authorized).toBe(false);
    });

    it('watchable remote start', () => {
        let resID = "";
        svc._watchRemoteStart((ev) => {
            resID = ev;
        });
        expect(resID).toEqual("");
        svc.startEditing("testid");
        expect(resID).toEqual("testid");
    });
});


               
                                 
        
        
