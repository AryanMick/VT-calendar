#!/usr/bin/env node

// VT Calendar Setup Verification Script

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying VT Calendar setup...\n');

let issues = 0;

// Check required files
const requiredFiles = [
    'server.js',
    'package.json',
    'public/index.html',
    'public/app.js',
    'public/style.css',
    'extension/manifest.json',
    'extension/popup.html',
    'extension/popup.js',
    'README.md'
];

console.log('📁 Checking required files...');
requiredFiles.forEach(file => {
    if (fs.existsSync(file)) {
        console.log(`   ✓ ${file}`);
    } else {
        console.log(`   ✗ ${file} - MISSING`);
        issues++;
    }
});

// Check env file
console.log('\n⚙️  Checking configuration...');
if (fs.existsSync('.env')) {
    console.log('   ✓ .env file exists');
} else {
    console.log('   ⚠  .env file not found');
    console.log('   → Run: cp env.template .env');
    issues++;
}

// Check node_modules
if (fs.existsSync('node_modules')) {
    console.log('   ✓ node_modules exists');
} else {
    console.log('   ✗ node_modules not found');
    console.log('   → Run: npm install');
    issues++;
}

// Check extension icons
console.log('\n🎨 Checking extension icons...');
const iconFiles = [
    'extension/icons/icon16.png',
    'extension/icons/icon32.png',
    'extension/icons/icon48.png',
    'extension/icons/icon128.png'
];

let missingIcons = 0;
iconFiles.forEach(icon => {
    if (fs.existsSync(icon)) {
        console.log(`   ✓ ${icon}`);
    } else {
        console.log(`   ⚠  ${icon} - placeholder (can add PNG icons later)`);
        missingIcons++;
    }
});

console.log(`\n${'='.repeat(50)}`);

if (issues === 0) {
    console.log('\n✅ Setup verification complete!');
    console.log('\n📝 Next steps:');
    console.log('   1. Copy env.template to .env if not done');
    console.log('   2. Update .env with your API credentials');
    console.log('   3. Run: npm start');
    console.log('   4. Open: http://localhost:3000');
    console.log('   5. Load the Chrome extension from the extension/ folder');
    console.log('\n🎉 Ready to use!');
    process.exit(0);
} else {
    console.log(`\n⚠️  Found ${issues} issue(s). Please resolve before starting.`);
    process.exit(1);
}


