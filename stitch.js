/**
 * stitch.js
 * Script to Stitch Schema Files Together
 */

const gql = require('merge-graphql-schemas');
const path = require('path');
const fs = require('fs');

const files = gql.fileLoader(path.join(__dirname, 'schema'), {
  recursive: true
});
const content = gql.mergeTypes(files, { all: true });
fs.writeFileSync('schema.graphql', content);
console.log('Schema Stitch Complete');
