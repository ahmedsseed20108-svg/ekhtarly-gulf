import urllib.request, re, json, os, time, gzip
from concurrent.futures import ThreadPoolExecutor
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9,ar;q=0.8", "Accept-Encoding": "gzip"}
T0 = time.time()
def get(url, to=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=to) as r:
        raw = r.read()
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8", "ignore")
SITES = [
 ("samsung-ae", "https://www.samsung.com", "/ae/", ["/smartphones/", "sm-"]),
 ("samsung-sa", "https://www.samsung.com", "/sa/", ["/smartphones/", "sm-"]),
 ("mi-ae", "https://www.mi.com", "/ae/", ["/product/"]),
 ("mi-sa", "https://www.mi.com", "/sa/", ["/product/"]),
 ("honor-ae", "https://www.hihonor.com", "/ae/", ["/phones/"]),
 ("honor-sa", "https://www.hihonor.com", "/sa/", ["/phones/"]),
]
CAP = 150
diag = []
def sitemaps_for(root):
    found = []
    try:
        rb = get(root + "/robots.txt", 20)
        found = re.findall(r'(?im)^sitemap:\s*(\S+)', rb)
    except Exception as e:
        diag.append(f"robots ERR {root} {str(e)[:40]}")
    if not found:
        found = [root + "/sitemap.xml"]
    return found
def locs(sm, depth, prefix, keys, acc, seen):
    if sm in seen or depth > 2 or time.time() - T0 > 420 or len(acc) > 4000:
        return
    seen.add(sm)
    try:
        x = get(sm, 40)
    except Exception as e:
        diag.append(f"sitemap ERR {sm[-60:]} {str(e)[:30]}")
        return
    ls = re.findall(r'<loc>\s*(.*?)\s*</loc>', x)
    for l in ls:
        if l.endswith(".xml") or l.endswith(".xml.gz") or "sitemap" in l.lower() and l.endswith("xml"):
            if prefix.strip("/") in l.lower() or depth == 0:
                locs(l, depth + 1, prefix, keys, acc, seen)
        elif prefix in l and all(k in l for k in keys[:1]) and (len(keys) < 2 or keys[1] in l or True):
            acc.append(l)
def parse(url):
    try:
        b = get(url, 30)
    except Exception as e:
        return []
    res = []
    for m in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', b, re.S):
        try:
            j = json.loads(m)
        except Exception:
            continue
        stack = j if isinstance(j, list) else [j]
        for it in stack:
            if isinstance(it, dict) and "@graph" in it:
                stack = stack + it["@graph"]
        for it in stack:
            if isinstance(it, dict) and it.get("@type") in ("Product", "ProductGroup"):
                o = it.get("offers") or {}
                if isinstance(o, list): o = o[0] if o else {}
                pr = o.get("price") or o.get("lowPrice")
                if pr:
                    res.append({"url": url, "name": str(it.get("name"))[:90], "sku": it.get("sku"), "price": pr, "cur": o.get("priceCurrency"), "avail": str(o.get("availability", ""))[-12:]})
    return res
items = []
summ = []
for key, root, prefix, keys in SITES:
    if time.time() - T0 > 480:
        summ.append(f"{key}: skipped (time)"); continue
    acc = []; seen = set()
    for sm in sitemaps_for(root):
        locs(sm, 0, prefix, keys, acc, seen)
    acc = list(dict.fromkeys(acc))
    pick = [u for u in acc if all(k in u for k in keys)] or acc
    pick = pick[:CAP]
    with ThreadPoolExecutor(8) as ex:
        out = list(ex.map(parse, pick))
    got = [i for lst in out for i in lst]
    for g in got: g["site"] = key
    items += got
    summ.append(f"{key}: urls_in_sitemap={len(acc)} fetched={len(pick)} with_price={len(got)}")
json.dump(items, open("gulf-raw.json", "w"), ensure_ascii=False)
text = "\n".join(summ + diag[:10] + [f"{i['site']} | {i['name']} | {i['price']} {i['cur']}" for i in items[:12]])
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
