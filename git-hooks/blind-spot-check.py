#!/usr/bin/env python3
import json
import sys
import urllib.request
from datetime import date

CUTOFF = "2024-11-01"
CUTOFF_DATE = date.fromisoformat(CUTOFF)

def fetch_url(url, data=None, timeout=15):
    try:
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

def get_vuln_published(vuln_id):
    """Fetch full vuln details to get published date."""
    data = fetch_url(f'https://api.osv.dev/v1/vulns/{vuln_id}')
    if data:
        return data.get('published', '')
    return ''

def main():
    pkgs = json.load(sys.stdin)
    if not pkgs:
        print(json.dumps({'all_cves':[],'blind_spots':[],'total':0,'blind_count':0}))
        return

    # Build batch query
    queries = []
    for p in pkgs:
        q = {'package': {'name': p['name'], 'ecosystem': p['ecosystem']}}
        if p.get('version') and p['version'] != 'unknown':
            q['version'] = p['version']
        queries.append(q)

    osv = fetch_url('https://api.osv.dev/v1/querybatch',
                    data=json.dumps({'queries': queries}).encode())
    if not osv:
        print(json.dumps({'all_cves':[],'blind_spots':[],'total':0,'blind_count':0,'error':'OSV unreachable'}))
        return

    results = osv.get('results', [])
    all_cves = []
    blind_spots = []
    seen = set()

    for i, pkg in enumerate(pkgs):
        vulns = results[i].get('vulns', []) if i < len(results) else []
        for v in vulns:
            vid = v.get('id', '')
            if not vid or vid in seen:
                continue
            seen.add(vid)

            # Get published date from vuln object first, then fetch full record
            published = v.get('published', '')
            if not published:
                published = get_vuln_published(vid)

            pub_str = published[:10] if published else ''
            is_blind = False
            days_after = 0

            if pub_str:
                try:
                    pub_date = date.fromisoformat(pub_str)
                    is_blind = pub_date > CUTOFF_DATE
                    if is_blind:
                        days_after = (pub_date - CUTOFF_DATE).days
                except:
                    pass

            entry = {
                'id': vid,
                'package': pkg['name'],
                'version': pkg.get('version', 'unknown'),
                'published': published,
                'pub_date': pub_str,
                'is_blind': is_blind,
                'days_after': days_after
            }
            all_cves.append(entry)
            if is_blind:
                blind_spots.append(entry)

    print(json.dumps({
        'all_cves': all_cves,
        'blind_spots': blind_spots,
        'total': len(all_cves),
        'blind_count': len(blind_spots)
    }))

if __name__ == '__main__':
    main()
