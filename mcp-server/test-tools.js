import { extractDependencies } from './tools/extract-dependencies.js';
import { checkCVE } from './tools/check-cve.js';
import { classifyLicense } from './tools/classify-license.js';
import { scoreFreshness } from './tools/score-freshness.js';

console.log('=== Testing ChainSight Tools ===\n');

const code = `
import fastapi
from jose import jwt
import requests

---DEPENDENCIES---
fastapi==0.111.0 (ecosystem: PyPI)
python-jose==3.3.0 (ecosystem: PyPI)
requests==2.31.0 (ecosystem: PyPI)
---END---
`;

const deps = await extractDependencies({ code });
console.log('TEST 1 - Extract:', deps.count, 'dependencies found');

const cves = await checkCVE({ packages: deps.dependencies });
console.log('TEST 2 - CVEs:', cves.summary?.total_cves, 'total CVEs found');

const lic = await classifyLicense({ name: 'requests', version: '2.31.0', ecosystem: 'PyPI' });
console.log('TEST 3 - License:', lic.spdx_id);

const allCves = cves.results.flatMap(r => r.cves.map(c => ({ id: c.id, published: c.published })));
const fresh = await scoreFreshness({ cves: allCves });
console.log('TEST 4 - Blind spots:', fresh.summary.post_cutoff_count);
console.log('Message:', fresh.summary.message);
console.log('\n=== All tests complete ===');
