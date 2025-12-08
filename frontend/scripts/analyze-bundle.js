/**
 * Bundle Size Analysis Script
 * Analyzes bundle sizes and provides optimization recommendations
 */

import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

const distDir = join(process.cwd(), 'dist');
const jsDir = join(distDir, 'js');

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function analyzeBundle() {
  console.log('📦 Bundle Size Analysis\n');
  console.log('='.repeat(60));

  try {
    const files = readdirSync(jsDir);
    const fileStats = files
      .map((file) => {
        const filePath = join(jsDir, file);
        const stats = statSync(filePath);
        return {
          name: file,
          size: stats.size,
          path: filePath,
        };
      })
      .sort((a, b) => b.size - a.size);

    let totalSize = 0;
    console.log('\n📊 File Sizes:\n');
    fileStats.forEach((file) => {
      totalSize += file.size;
      const sizeStr = formatBytes(file.size);
      const barLength = Math.floor((file.size / fileStats[0].size) * 30);
      const bar = '█'.repeat(barLength);
      console.log(`${sizeStr.padEnd(12)} ${bar} ${file.name}`);
    });

    console.log('\n' + '='.repeat(60));
    console.log(`\n📈 Total Bundle Size: ${formatBytes(totalSize)}`);
    console.log(`📁 Number of Chunks: ${fileStats.length}\n`);

    // Recommendations
    console.log('💡 Optimization Recommendations:\n');
    
    const largeFiles = fileStats.filter((f) => f.size > 500 * 1024); // > 500KB
    if (largeFiles.length > 0) {
      console.log('⚠️  Large files detected (>500KB):');
      largeFiles.forEach((file) => {
        console.log(`   - ${file.name}: ${formatBytes(file.size)}`);
        console.log(`     Consider code splitting or lazy loading`);
      });
      console.log('');
    }

    if (totalSize > 2 * 1024 * 1024) {
      console.log('⚠️  Total bundle size exceeds 2MB');
      console.log('   Consider:');
      console.log('   - More aggressive code splitting');
      console.log('   - Tree shaking unused code');
      console.log('   - Removing unused dependencies');
      console.log('');
    }

    const vendorFiles = fileStats.filter((f) => f.name.includes('vendor'));
    if (vendorFiles.length > 10) {
      console.log('⚠️  Too many vendor chunks detected');
      console.log('   Consider consolidating vendor chunks');
      console.log('');
    }

    console.log('✅ Analysis complete!\n');
  } catch (error) {
    console.error('❌ Error analyzing bundle:', error.message);
    console.log('\n💡 Make sure to build the project first: npm run build\n');
  }
}

analyzeBundle();

