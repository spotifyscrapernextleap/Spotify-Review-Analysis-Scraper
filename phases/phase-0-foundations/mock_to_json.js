// Phase 0 test helper: evaluate the prototype data.js and dump window.REVIEW_DATA
// as JSON, so the Python contract models can validate the real contract shape.
const path = require("path");
global.window = {};
const dataPath = path.join(__dirname, "..", "..", "build and design docs", "source", "data.js");
require(dataPath);
process.stdout.write(JSON.stringify(global.window.REVIEW_DATA, null, 2));
