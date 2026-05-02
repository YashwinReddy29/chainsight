export async function classifyLicense({ name, version, ecosystem }) {
  try {
    if (ecosystem === 'PyPI' || ecosystem === 'pypi') return await getPyPI(name, version);
    if (ecosystem === 'npm') return await getNpm(name, version);
    return { name, version, ecosystem, license: 'UNKNOWN', spdx_id: 'NOASSERTION' };
  } catch (error) {
    return { name, version, ecosystem, license: 'LOOKUP_FAILED', spdx_id: 'NOASSERTION', error: error.message };
  }
}

async function getPyPI(name, version) {
  const url = (version && version !== 'unknown')
    ? `https://pypi.org/pypi/${encodeURIComponent(name)}/${version}/json`
    : `https://pypi.org/pypi/${encodeURIComponent(name)}/json`;
  const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`PyPI ${res.status}`);
  const data = await res.json();
  const info = data.info || {};
  let license = info.license || '';
  if (!license || license.length > 100) {
    const lc = (info.classifiers || []).find(c => c.startsWith('License ::'));
    if (lc) license = lc.split(' :: ').pop();
  }
  return { name, version: info.version || version, ecosystem: 'PyPI', license: license || 'UNKNOWN', spdx_id: toSpdx(license) };
}

async function getNpm(name, version) {
  const enc = encodeURIComponent(name).replace('%40','@').replace('%2F','/');
  const url = (version && version !== 'unknown')
    ? `https://registry.npmjs.org/${enc}/${version}`
    : `https://registry.npmjs.org/${enc}/latest`;
  const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`npm ${res.status}`);
  const data = await res.json();
  const license = data.license || data.licenses?.[0]?.type || 'UNKNOWN';
  return { name, version: data.version || version, ecosystem: 'npm', license: typeof license === 'string' ? license : JSON.stringify(license), spdx_id: toSpdx(typeof license === 'string' ? license : license?.type) };
}

function toSpdx(license) {
  if (!license) return 'NOASSERTION';
  const n = license.trim().toLowerCase();
  const map = [
    [['mit'], 'MIT'],
    [['apache-2.0','apache 2.0','apache2','apache software'], 'Apache-2.0'],
    [['bsd-3-clause','bsd 3','new bsd','revised bsd'], 'BSD-3-Clause'],
    [['bsd-2-clause','bsd 2','simplified bsd'], 'BSD-2-Clause'],
    [['gpl-3.0','gpl-3','gpl v3'], 'GPL-3.0-only'],
    [['gpl-2.0','gpl-2','gpl v2'], 'GPL-2.0-only'],
    [['lgpl-3.0','lgpl-3'], 'LGPL-3.0-only'],
    [['lgpl-2.1','lgpl-2'], 'LGPL-2.1-only'],
    [['mpl-2.0','mozilla'], 'MPL-2.0'],
    [['isc'], 'ISC'],
    [['cc0','public domain','unlicense'], 'CC0-1.0'],
    [['agpl'], 'AGPL-3.0-only'],
  ];
  for (const [patterns, id] of map) {
    if (patterns.some(p => n.includes(p))) return id;
  }
  return license.trim();
}
