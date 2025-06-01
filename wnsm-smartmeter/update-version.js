const fs = require('fs');
const path = require('path');

// Read command line arguments
const args = process.argv.slice(2);
const versionType = args[0] || 'patch'; // Default to patch if not specified

// Read the config.json file
const configPath = path.join(__dirname, 'config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

// Parse the current version
const currentVersion = config.version;
const [major, minor, patch] = currentVersion.split('.').map(Number);

// Calculate the new version based on the version type
let newVersion;
switch (versionType.toLowerCase()) {
  case 'major':
    newVersion = `${major + 1}.0.0`;
    break;
  case 'minor':
    newVersion = `${major}.${minor + 1}.0`;
    break;
  case 'patch':
  default:
    newVersion = `${major}.${minor}.${patch + 1}`;
    break;
}

// Update the version in config.json
config.version = newVersion;
fs.writeFileSync(configPath, JSON.stringify(config, null, 4), 'utf8');

console.log(`Version updated from ${currentVersion} to ${newVersion}`);

// Also update the CHANGELOG.md
const changelogPath = path.join(__dirname, 'CHANGELOG.md');
let changelog = '';

try {
  changelog = fs.readFileSync(changelogPath, 'utf8');
} catch (error) {
  // If the file doesn't exist, create it
  changelog = '# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n';
}

// Add the new version entry at the top of the changelog
const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
const newEntry = `## [${newVersion}] - ${date}\n\n### Changes\n\n- Update version to ${newVersion}\n\n`;

// Insert the new entry after the header
const lines = changelog.split('\n');
let insertIndex = 0;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].startsWith('# Changelog')) {
    // Find the next empty line after the header
    while (i < lines.length && lines[i].trim() !== '') {
      i++;
    }
    insertIndex = i + 1;
    break;
  }
}

// If we didn't find a header, just prepend the new entry
if (insertIndex === 0) {
  changelog = newEntry + changelog;
} else {
  lines.splice(insertIndex, 0, newEntry);
  changelog = lines.join('\n');
}

fs.writeFileSync(changelogPath, changelog, 'utf8');
console.log(`Updated CHANGELOG.md with version ${newVersion}`);

// Copy the CHANGELOG.md to the parent directory
const parentChangelogPath = path.join(__dirname, '..', 'CHANGELOG.md');
fs.copyFileSync(changelogPath, parentChangelogPath);
console.log(`Copied CHANGELOG.md to parent directory`);

console.log('\nDon\'t forget to commit these changes and create a git tag:');
console.log(`git add config.json CHANGELOG.md ../CHANGELOG.md`);
console.log(`git commit -m "chore(release): ${newVersion}"`);
console.log(`git tag -a v${newVersion} -m "Version ${newVersion}"`);