// The file contents for the current environment will overwrite these during build.
// The build system defaults to the dev environment which uses `environment.ts`, but if you do
// `ng build --env=prod` then `environment.prod.ts` will be used instead.
// The list of which env maps to which file can be found in `.angular-cli.json`.

declare var OAR_APP_ENV: any;

export const environment = {
  production: false,
  RMMAPI: 'http://data.nist.gov/rmm/',
    SDPAPI:  'http://testdata.nist.gov/sdp/',
    PDRAPI:  'http://localhost:5555/#/id/',
    DISTAPI: 'http://localhost/disturl/',
    METAPI:  'http://localhost/metaurl/',
    LANDING: 'http://data.nist.gov/rmm/'
};