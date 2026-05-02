export async function extractDependencies({ code, ecosystem }) {
  const results = [];

  const depsBlockMatch = code.match(/---DEPENDENCIES---([\s\S]*?)---END---/);
  if (depsBlockMatch) {
    const lines = depsBlockMatch[1].trim().split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const structured = trimmed.match(/^([\w./@-]+)==([^\s]+)\s+\(ecosystem:\s*(\w+)\)/);
      if (structured) {
        results.push({ name: structured[1], version: structured[2], ecosystem: structured[3], source: 'deps-block' });
        continue;
      }
      const noVersion = trimmed.match(/^([\w./@-]+)\s+\(ecosystem:\s*(\w+)\)/);
      if (noVersion) {
        results.push({ name: noVersion[1], version: 'unknown', ecosystem: noVersion[2], source: 'deps-block' });
      }
    }
  }

  const detectedEco = ecosystem || detectEcosystem(code);

  if (detectedEco === 'PyPI') {
    const importMatches = [...code.matchAll(/^(?:import|from)\s+([\w.-]+)/gm)];
    for (const m of importMatches) {
      const name = m[1].split('.')[0];
      if (!isBuiltin(name, 'PyPI') && !results.find(r => r.name === name)) {
        results.push({ name, version: 'unknown', ecosystem: 'PyPI', source: 'import-parse' });
      }
    }
    const reqMatches = [...code.matchAll(/^([\w.-]+)==([\d.]+)/gm)];
    for (const m of reqMatches) {
      if (!isBuiltin(m[1], 'PyPI')) {
        const existing = results.find(r => r.name === m[1]);
        if (existing) { existing.version = m[2]; }
        else { results.push({ name: m[1], version: m[2], ecosystem: 'PyPI', source: 'requirements' }); }
      }
    }
  }

  if (detectedEco === 'npm') {
    const esMatches = [...code.matchAll(/import\s+.*?from\s+['"]([^'"./][^'"]*)['"]/g)];
    for (const m of esMatches) {
      const name = m[1].startsWith('@') ? m[1].split('/').slice(0,2).join('/') : m[1].split('/')[0];
      if (!isBuiltin(name, 'npm') && !results.find(r => r.name === name)) {
        results.push({ name, version: 'unknown', ecosystem: 'npm', source: 'import-parse' });
      }
    }
    const requireMatches = [...code.matchAll(/require\(['"]([^'"./][^'"]*)['"]\)/g)];
    for (const m of requireMatches) {
      const name = m[1].startsWith('@') ? m[1].split('/').slice(0,2).join('/') : m[1].split('/')[0];
      if (!isBuiltin(name, 'npm') && !results.find(r => r.name === name)) {
        results.push({ name, version: 'unknown', ecosystem: 'npm', source: 'require-parse' });
      }
    }
  }

  const seen = new Map();
  for (const dep of results) {
    if (!seen.has(dep.name)) { seen.set(dep.name, dep); }
    else if (seen.get(dep.name).version === 'unknown' && dep.version !== 'unknown') {
      seen.set(dep.name, dep);
    }
  }

  const unique = [...seen.values()];
  return { success: true, dependencies: unique, count: unique.length, detected_ecosystem: detectedEco, has_deps_block: !!depsBlockMatch };
}

function detectEcosystem(code) {
  const pyScore = (code.match(/import\s+\w+/g)||[]).length + (code.match(/def\s+\w+/g)||[]).length;
  const jsScore = (code.match(/const\s+\w+/g)||[]).length + (code.match(/require\(/g)||[]).length;
  return jsScore > pyScore ? 'npm' : 'PyPI';
}

function isBuiltin(name, ecosystem) {
  const py = new Set(['os','sys','re','json','math','io','abc','ast','copy','collections','datetime',
    'functools','itertools','logging','pathlib','typing','unittest','threading','subprocess',
    'hashlib','hmac','base64','uuid','time','random','socket','ssl','http','urllib','csv',
    'sqlite3','contextlib','dataclasses','enum','warnings','traceback','inspect','argparse',
    'shutil','tempfile','glob','pickle','gzip','zipfile','configparser','getpass','platform']);
  const node = new Set(['fs','path','http','https','os','crypto','util','events','stream',
    'buffer','child_process','cluster','net','dns','url','querystring','assert','readline',
    'zlib','tls','process','console','worker_threads','module','string_decoder']);
  if (ecosystem === 'PyPI') return py.has(name);
  if (ecosystem === 'npm') return node.has(name);
  return false;
}
