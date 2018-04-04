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
  RMMAPI: "http://data.nist.gov/rmm/",
  SDPAPI:  'http://testdata.nist.gov/sdp/',
  PDRAPI:  'http://localhost:5555/#/id/',
  DISTAPI: 'http://localhost/disturl/',
  METAPI:  'http://localhost/metaurl/',
  LANDING: 'http://data.nist.gov/rmm/'
};