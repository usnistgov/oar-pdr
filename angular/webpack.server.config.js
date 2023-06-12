const path = require('path');
const webpack = require('webpack');

// const uglifyJsPlugin = require('uglifyjs-webpack-plugin');
// var mangle = true;

module.exports = {
  entry: { server: './server.ts', prerender: './prerender.ts' },
  resolve: {
    extensions: ['.js', '.ts'],
    modules: [path.join(__dirname, "node_modules")],
    fallback: { "url": require.resolve("url/") }
  },
  target: 'node',
  mode: 'none',
  // this makes sure we include node_modules and other 3rd party libraries
  externals: [/node_modules/],
  output: {
    path: path.join(__dirname, 'dist'),
    filename: '[name].js'
  },
 
  module: {
    rules: [
        { test: /\.(ts|js)$/, loader: 'regexp-replace-loader', options: { match: { pattern: '\\[(Mouse|Keyboard)?Event\\]', flags: 'g' }, replaceWith: '[]', } },
        { test: /\.ts$/, loader: 'ts-loader' },
        {
          // Mark files inside `@angular/core` as using SystemJS style dynamic imports.
          // Removing this will cause deprecation warnings to appear.
          test: /(\\|\/)@angular(\\|\/)core(\\|\/).+\.js$/,
          parser: { system: true },
        }
      ]
  },
  plugins: [
    // Temporary Fix for issue: https://github.com/angular/angular/issues/11580
    // for 'WARNING Critical dependency: the request of a dependency is an expression'
    new webpack.ContextReplacementPlugin(
      /(.+)?angular(\\|\/)core(.+)?/,
      path.join(__dirname, 'src'), // location of your src
      {} // a map of your routes
    ),
    new webpack.ContextReplacementPlugin(
      /(.+)?express(\\|\/)(.+)?/,
      path.join(__dirname, 'src'),
      {}
    )
  ]
};
