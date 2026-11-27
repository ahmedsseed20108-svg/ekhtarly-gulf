import urllib.request, urllib.error, re, json, os
from concurrent.futures import ThreadPoolExecutor
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}
def req(url, to=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=to) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""
B = "https://btech.com"
URL = B + "/ar/c/mobiles-tablets/mobile-phones"
def meta(h):
    t = h.replace('\\"', '"')
    m = re.search(r'"total_items":(\d+),"page":(\d+),"page_size":(\d+),"total_pages":(\d+)', t)
    sk = re.findall(r'"sku":"([^"]+)"', t)[:3]
    return {"meta": list(m.groups()) if m else None, "skus": sk}
out = {}
st, h = req(URL)
t = h.replace('\\"', '"')
i = t.find('"key":"brands"')
seg = t[i:i + 6000]
out["brand_ids"] = re.findall(r'"id":"([^"]+)","value":"([^"]+)","count":(\d+)', seg)[:12]
bid = next((x[0] for x in out["brand_ids"] if "samsung" in x[0].lower() or "samsung" in x[1].lower()), (out["brand_ids"][0][0] if out["brand_ids"] else "samsung"))
out["bid"] = bid
base_sk = meta(h)["skus"]
out["tests"] = {}
qs = [f"?brands={bid}", f"?brands[]={bid}", f"?brands%5B%5D={bid}", f"?filters=brands:{bid}", f"?filters[brands]={bid}", f"?filter=brands:{bid}", f"?f=brands:{bid}", f"?brands={bid}&page=1",
      "?sort_by=price_asc", "?sort_by=price_desc", "?sort_by=newest", "?sort=price_asc", "?sort=price_desc", "?sortBy=price_asc", "?order_by=price_asc", "?sort_by=price-asc", "?sort_by=price_low_to_high"]
def run(q):
    s2, hh = req(URL + q)
    m = meta(hh)
    m["st"] = s2; m["diff"] = m["skus"] != base_sk
    return q, m
with ThreadPoolExecutor(6) as ex:
    for q, m in ex.map(run, qs):
        out["tests"][q] = m
s, root = req(B + "/ar")
scripts = sorted(set(re.findall(r'src="(/_next/static/[^"]+\.js)"', h)))
def dl(s):
    s_, j = req(B + s, 30); return s, j
snips = {}
with ThreadPoolExecutor(8) as ex:
    for s, js in ex.map(dl, scripts):
        for m in re.finditer(r'searchParams|URLSearchParams|useSearchParams', js):
            ctx = re.sub(r"\s+", " ", js[max(0, m.start() - 100):m.start() + 220])
            if "sort" in ctx or "filter" in ctx or "brands" in ctx:
                snips.setdefault(s[-12:] + str(m.start()), ctx)
out["code_snips"] = dict(list(snips.items())[:8])
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3800]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
