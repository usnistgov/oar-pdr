
export interface UserInfo {
    fullName: string;
    organization: string;
    email: string;
    receiveEmails: string;
    country: string;
    approvalStatus: string;
    productTitle?: string;
    subject: string;
    description: string;
}

export interface Record {
    is: string;
    caseNum: string
    userInfo: UserInfo
}

  export interface RecordWrapper {
    record: Record;
  }