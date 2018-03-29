// export const environment = {
//   production: true,
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