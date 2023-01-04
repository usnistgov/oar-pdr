export interface Dataset {
    name: string;
    description: string;
    url: string;
    approvers: any[];
    terms: string[];
    requiresApproval: boolean;
    formTemplate: string;
  }