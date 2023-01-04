export interface UserInfo {
    fullName: string;
    email: string
    phone?: string;
    organization: string;
    purposeOfUse: string;
    address1: string;
    address2?: string;
    address3?: string;
    stateOrProvince?: string;
    zipCode?: number;
    country: string;
    receiveEmails: boolean;
}