const OSV_BATCH_URL = 'https://api.osv.dev/v1/querybatch';

export async function checkCVE({ packages }) {
  if (!packages || packages.length === 0) return { success: false, error: 'No packages provided', results: [] };

  const ecoMap = { 'PyPI':'PyPI','pypi':'PyPI','npm':'npm','node':'npm','Go':'Go','go':'Go',
    'Maven':'Maven','maven':'Maven','Cargo':'crates.io','cargo':'crates.io' };

  const queries = packages.map(pkg => {
    const q = { package: { name: pkg.name, ecosystem: ecoMap[pkg.ecosystem] || pkg.ecosystem } };
    if (pkg.version && pkg.version !== 'unknown') q.version = pkg.version;
    return q;
  });

  try {
    const response = await fetch(OSV_BATCH_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ queries }),
      signal: AbortSignal.timeout(15000)
    });

    if (!response.ok) throw new Error(`OSV API returned ${response.status}`);
    const data = await response.json();
    const results = [];

    for (let i = 0; i < packages.length; i++) {
      const pkg = packages[i];
      const vulns = data.results?.[i]?.vulns || [];
      const cveDetails = vulns.map(v => ({
        id: v.id,
        summary: v.summary || 'No summary',
        published: v.published || 'unknown',
        aliases: v.aliases || [],
        severity: extractSeverity(v),
        severity_score: extractScore(v),
        fixed_in: extractFixed(v)
      }));
      results.push({
        package: pkg.name,
        version: pkg.version || 'unknown',
        ecosystem: pkg.ecosystem,
        cve_count: vulns.length,
        severity: overallSeverity(cveDetails),
        max_score: Math.max(0, ...cveDetails.map(c => c.severity_score)),
        cves: cveDetails
      });
    }

    return {
      success: true,
      results,
      summary: {
        total_packages: packages.length,
        total_cves: results.reduce((s,r) => s + r.cve_count, 0),
        critical: results.filter(r => r.severity === 'CRITICAL').length,
        high: results.filter(r => r.severity === 'HIGH').length,
        clean: results.filter(r => r.cve_count === 0).length
      }
    };
  } catch (error) {
    return { success: false, error: error.message, results: [] };
  }
}

function extractSeverity(vuln) {
  for (const s of vuln.severity || []) {
    const score = parseFloat(s.score);
    if (!isNaN(score)) {
      if (score >= 9.0) return 'CRITICAL';
      if (score >= 7.0) return 'HIGH';
      if (score >= 4.0) return 'MEDIUM';
      return 'LOW';
    }
    if (typeof s.score === 'string' && s.score.startsWith('CVSS:')) {
      return parseCVSSVector(s.score);
    }
  }
  return vuln.id ? 'MEDIUM' : 'UNKNOWN';
}

function parseCVSSVector(vector) {
  const ci = vector.includes('C:H') ? 1 : vector.includes('C:L') ? 0.5 : 0;
  const ii = vector.includes('I:H') ? 1 : vector.includes('I:L') ? 0.5 : 0;
  const ai = vector.includes('A:H') ? 1 : vector.includes('A:L') ? 0.5 : 0;
  const avg = (ci + ii + ai) / 3;
  if (avg >= 0.9) return 'CRITICAL';
  if (avg >= 0.6) return 'HIGH';
  if (avg >= 0.3) return 'MEDIUM';
  return 'LOW';
}

function extractScore(vuln) {
  for (const s of vuln.severity || []) {
    const score = parseFloat(s.score);
    if (!isNaN(score)) return score;
  }
  return 0;
}

function extractFixed(vuln) {
  for (const a of vuln.affected || []) {
    for (const r of a.ranges || []) {
      for (const e of r.events || []) {
        if (e.fixed) return e.fixed;
      }
    }
  }
  return null;
}

function overallSeverity(cves) {
  if (!cves.length) return 'NONE';
  if (cves.some(c => c.severity === 'CRITICAL')) return 'CRITICAL';
  if (cves.some(c => c.severity === 'HIGH')) return 'HIGH';
  if (cves.some(c => c.severity === 'MEDIUM')) return 'MEDIUM';
  if (cves.length > 0) return 'LOW';
  return 'NONE';
}
