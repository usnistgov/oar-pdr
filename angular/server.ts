// These are important and needed before anything else
import 'zone.js/dist/zone-node';
import 'reflect-metadata';
import { enableProdMode } from '@angular/core';
import * as express from 'express';
import { join } from 'path';
import * as cors from "cors";
// Express Engine
import { ngExpressEngine } from '@nguniversal/express-engine';
// Import module map for lazy loading
import { provideModuleMap } from '@nguniversal/module-map-ngfactory-loader';

// Faster server renders w/ Prod mode (dev mode never needed)
enableProdMode();
// Express server
const app = express();
//var router = express.Router();
const PORT = process.env.PORT || 4200;
const DIST_FOLDER = join(process.cwd(), 'dist');

// * NOTE :: leave this as require() since this file is built Dynamically from webpack
const { AppServerModuleNgFactory, LAZY_MODULE_MAP } = require('./dist/server/main.bundle');
//options for cors midddleware
// const options:cors.CorsOptions = {
//   allowedHeaders: ["Origin", "X-Requested-With", "Content-Type", "Accept", "X-Access-Token"],
//   credentials: false,
//   methods: "GET,HEAD,OPTIONS,PUT,PATCH,POST,DELETE",
//   origin: "*",
  
// };
// //use cors middleware
// router.use(cors(options));
// //add your routes
// //enable pre-flight
// router.options("*", cors(options));


app.engine('html', ngExpressEngine({
  bootstrap: AppServerModuleNgFactory,
  providers: [
    provideModuleMap(LAZY_MODULE_MAP)
  ]
}));
app.set('view engine', 'html');
app.set('views', join(DIST_FOLDER, 'browser'));

app.get('*.*',express.static(join(DIST_FOLDER, 'browser')));
// // All regular routes use the Universal engine
app.get('*', (req, res,next) => {
  res.render(join(DIST_FOLDER, 'browser', 'index.html'), { req });
});
// Start up the Node server
app.listen(PORT, () => {
  console.log(`Node server listening on http://localhost:${PORT}`);
});