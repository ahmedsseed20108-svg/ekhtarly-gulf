import urllib.request, re, json, os
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}
def get(url, data=None, hdr=None, to=40):
    h = dict(UA)
    if hdr: h.update(hdr)
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=to) as r:
        return r.status, r.read().decode("utf-8", "ignore")
out = {}
URL = "https://btech.com/ar/c/mobiles-tablets/mobile-phones"
try:
    st, b = get(URL)
    t = b.replace('\\"', '"')
    out["status"] = st; out["len"] = len(b)
    out["hasNextData"] = "__NEXT_DATA__" in b
    m = re.search(r'/_next/static/([A-Za-z0-9_-]{8,})/_buildManifest', b)
    out["buildId"] = m.group(1) if m else None
    urls = set(re.findall(r'https?://[^"\'\s<>\\)]+', t))
    keep = [u for u in urls if re.search(r'graphql|algolia|typesense|elastic|search|/api/|catalog|product', u, re.I) and not re.search(r'\.(jpg|jpeg|png|webp|svg|gif|css|woff2?|ico)(\?|$)|media\.btech|fonts\.g', u, re.I)]
    out["api_urls"] = sorted(keep)[:40]
    out["scripts"] = sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', b)))[:20]
    ctx = {}
    for k in ["currentPage", "page_size", "pageSize", "endCursor", "hasNextPage", "nextPage", "total_count", "totalCount", "numFound", "nbHits", "x-algolia", "applicationId", "searchKey"]:
        i = t.find(k)
        if i >= 0: ctx[k] = re.sub(r"\s+", " ", t[max(0, i - 80):i + 160])
    out["ctx"] = ctx
except Exception as e:
    out["page_err"] = str(e)[:100]
out["graphql"] = {}
Q = '{"query":"{products(search:\\"samsung\\",pageSize:5,currentPage:1){total_count items{name sku}}}"}'.encode()
for ep in ["https://btech.com/graphql", "https://btech.com/api/graphql", "https://btech.com/ar/graphql", "https://api.btech.com/graphql", "https://btech.com/en/graphql"]:
    try:
        st, b = get(ep, data=Q, hdr={"Content-Type": "application/json", "Store": "ar"})
        out["graphql"][ep] = f"{st} {b[:250]}"
    except Exception as e:
        out["graphql"][ep] = "ERR " + str(e)[:60]
if out.get("buildId"):
    for p in ["/ar/c/mobiles-tablets/mobile-phones.json?page=2", ]:
        try:
            st, b = get(f"https://btech.com/_next/data/{out['buildId']}{p}")
            out["nextdata"] = f"{st} {len(b)} {b[:200]}"
        except Exception as e:
            out["nextdata"] = "ERR " + str(e)[:60]
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3500]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
