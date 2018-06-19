#!/usr/bin/env node

var path = require('path');
var prepend = require('prepend-file');
var findUp = require('find-up')

var FIXED_FILE = ['ng2-sticky', 'app', 'build', 'app.js'];
var FIXED_CODE = '// < HACK >\n'
  +'if (!process.env.BROWSER) {\n'
  +'  global.window = {};\n'
  +'}\n// </ HACK >\n\n'
  +'if (typeof window === \'undefined\') { \n' 
  +' global.window = {} \n'+
  +'} \n\n' ;

function hackChartJs() {
  findUp('node_modules')
    .then(nodeModules => prepend(
      path.resolve.apply(path, [nodeModules].concat(FIXED_FILE)),
      FIXED_CODE,
      console.log
    ));
}

hackChartJs();