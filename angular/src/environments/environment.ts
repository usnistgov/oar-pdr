// The file contents for the current environment will overwrite these during build.
// The build system defaults to the dev environment which uses `environment.ts`, but if you do
// `ng build --env=prod` then `environment.prod.ts` will be used instead.
// The list of which env maps to which file can be found in `.angular-cli.json`.

// export const environment = {
//   production: false,
//   rmmapi: "http://oardev.nist.gov/rmm/",
//   landingbackend: "http://oardev.nist.gov/rmm/",
//   sdpurl: "http://oardev.nist.gov/sdp/",
//   metdataservice: "http://oardev.nist.gov/rmm/"
// };


declare var OAR_APP_ENV: any;

export const environment = {
  production: false,
  RMMAPI: OAR_APP_ENV.RMMAPI,
  SDPAPI: OAR_APP_ENV.SDPAPI,
  PDRAPI: OAR_APP_ENV.PDRAPI,
  DISTAPI: OAR_APP_ENV.DISTAPI,
  METAPI: OAR_APP_ENV.METAPI,
  LANDING: OAR_APP_ENV.LANDING
};