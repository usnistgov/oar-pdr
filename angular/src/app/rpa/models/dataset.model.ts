export interface Dataset {
    name: string;
    ediid: string;
    description: string;
    url: string;
    terms: string[];
    requiresApproval: boolean;
    formTemplate: string;
}