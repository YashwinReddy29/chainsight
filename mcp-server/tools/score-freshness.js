const BOB_TRAINING_CUTOFF = new Date('2024-11-01T00:00:00Z');

export async function scoreFreshness({ cves }) {
  if (!cves || cves.length === 0) {
    return { success: true, results: [], summary: { total_checked: 0, post_cutoff_count: 0, freshness_risk: 'NONE' } };
  }

  const cutoffMs = BOB_TRAINING_CUTOFF.getTime();
  const now = new Date();

  const results = cves.map(cve => {
    let published;
    try { published = cve.published ? new Date(cve.published) : null; }
    catch { published = null; }

    if (!published || isNaN(published.getTime())) {
      return { id: cve.id, published: cve.published || 'unknown', bob_aware: 'UNKNOWN',
        is_bob_blind_spot: false, freshness_risk: 'UNKNOWN', message: 'Could not parse date' };
    }

    const daysAfter = Math.floor((published.getTime() - cutoffMs) / 86400000);
    const isBlind = daysAfter > 0;
    const daysSince = Math.floor((now.getTime() - published.getTime()) / 86400000);

    let risk = 'NONE';
    let message = '';

    if (isBlind) {
      risk = daysAfter > 180 ? 'CRITICAL' : 'HIGH';
      message = `BOB BLIND SPOT: published ${daysAfter} days after training cutoff. Bob could not warn about this. Exploitable for ${daysSince} days.`;
    } else {
      const daysBefore = Math.abs(daysAfter);
      risk = daysBefore < 30 ? 'LOW' : 'NONE';
      message = daysBefore < 30
        ? `Published ${daysBefore} days before cutoff — Bob may have partial knowledge.`
        : `Bob was trained with knowledge of this CVE (${daysBefore} days before cutoff).`;
    }

    return { id: cve.id, published: cve.published, days_after_cutoff: isBlind ? daysAfter : 0,
      days_since_publish: daysSince, freshness_risk: risk, bob_aware: !isBlind,
      is_bob_blind_spot: isBlind, message };
  });

  const blind = results.filter(r => r.is_bob_blind_spot);
  return {
    success: true,
    training_cutoff: BOB_TRAINING_CUTOFF.toISOString(),
    results,
    summary: {
      total_checked: cves.length,
      post_cutoff_count: blind.length,
      freshness_risk: blind.some(r => r.freshness_risk === 'CRITICAL') ? 'CRITICAL' : blind.length > 0 ? 'HIGH' : 'NONE',
      message: blind.length > 0
        ? `BOB BLIND SPOT: ${blind.length} CVE(s) unknown to Bob at generation time`
        : 'All CVEs within Bob training window',
      blind_spot_ids: blind.map(r => r.id)
    }
  };
}
