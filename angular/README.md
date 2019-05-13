# PDR Landing Page Service

This directory provides the `pdr-lps` software product, an
[Angular](https://angular.io) application providing HTML landing page
views of datasets in the PDR. 

This software is built on the Angular framework using Angular CLI and
Angular Universal (the latter providing server-side rendering) and
implemented primarily in Typescript.  It is currently built on Angular
6.  

## Prerequisites

 - [node](https://nodejs.org/en/download/) version 8.9.4 or higher.
   (10.9 is recommended).  This provides the `npm` build tool.

All other required modules can be installed automatically via the
`npm` tool (by typing `npm install` in this directory.

You may be interested these related links:
 - [Get VS Code](https://code.visualstudio.com/download) (an IDE)
 - [Angular CLI](https://github.com/angular/angular-cli) version 1.6.8.

## Building the app from scratch

### Downloading this repository

```bash
# clone the repo
git clone https://github.com/usnistgove/oar-pdr

# change directory to repo
cd angular

```

(Note that the [oar-metadata](https://github.com/usnistgove/oar-metadata) 
submodule is not needed for building and running the Angular code.)

### Building the application

The `npm` tool is used to build, test, and run the Angular application.  
To install the Typescript compiler and all required Javascript modules, type: 

```bash
npm install
```

This only needs to be done once, unless dependencies (recorded in the
`package.json` file) change.

To build the application, type

```bash
npm run build:ssr
```

### Running the tests

To run the unit tests and the integration tests (also refered to as _e2e
tests_), type, respectively:

```bash
npm test
npm e2e
```

_Note: e2e tests are currently disabled._

_Editor's Note:  add info about running/debugging tests interactively._

### Running the service

_Editor's note:  Need some instruction on configuring the service._

This application can run with browser-only operation (i.e. _without_
server-side rendering), via the following command:

```bash
npm serve
```

This will serve the application via a local web server; one can use a browser
to interact with it by accessing URLs based at `http://localhost:4000`.

To run the application with server-side rendering type:

```bash
npm run serve:universal
```

This will run `node` as a web server, serving the application via URLs based
at http://localhost:4200/.

## Further information

### Libraries 
 - [bootstrap](https://github.com/twbs/bootstrap) - The most popular HTML, CSS, and JavaScript framework for developing responsive, mobile first projects on the web.
 - [ng-bootstrap](https://ng-bootstrap.github.io) - Angular powered Bootstrap
 - [font-awesome 5.x](https://github.com/FortAwesome/Font-Awesome) - Get vector icons and social logos on your website with Font Awesome, the web’s most popular icon set and toolkit.

## Developing

### Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive/pipe/service/class/module`.

