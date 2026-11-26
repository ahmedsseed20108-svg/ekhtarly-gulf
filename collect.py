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
CAP = 900
SLUGS = ["galaxy-a05", "galaxy-a05s", "galaxy-a06", "galaxy-a06-4g", "galaxy-a06-5g", "galaxy-a07", "galaxy-a07-4g", "galaxy-a07-5g", "galaxy-a07s", "galaxy-a07s-4g", "galaxy-a08", "galaxy-a08-4g", "galaxy-a14", "galaxy-a14-4g", "galaxy-a14-5g", "galaxy-a15", "galaxy-a15-4g", "galaxy-a15-5g", "galaxy-a16", "galaxy-a16-4g", "galaxy-a16-5g", "galaxy-a17", "galaxy-a17-4g", "galaxy-a17-5g", "galaxy-a18", "galaxy-a18-4g", "galaxy-a24", "galaxy-a24-4g", "galaxy-a25", "galaxy-a25-5g", "galaxy-a26", "galaxy-a26-5g", "galaxy-a27", "galaxy-a27-5g", "galaxy-a34", "galaxy-a34-5g", "galaxy-a35", "galaxy-a35-5g", "galaxy-a36", "galaxy-a36-5g", "galaxy-a37", "galaxy-a37-5g", "galaxy-a54", "galaxy-a54-5g", "galaxy-a55", "galaxy-a55-5g", "galaxy-a56", "galaxy-a56-5g", "galaxy-a57", "galaxy-a57-5g", "galaxy-c55", "galaxy-c55-5g", "galaxy-f14", "galaxy-f14-5g", "galaxy-f15", "galaxy-f15-5g", "galaxy-f34", "galaxy-f34-5g", "galaxy-f54", "galaxy-f54-5g", "galaxy-f55", "galaxy-f55-5g", "galaxy-f56", "galaxy-f56-5g", "galaxy-m04", "galaxy-m05", "galaxy-m14", "galaxy-m14-5g", "galaxy-m15", "galaxy-m15-5g", "galaxy-m16", "galaxy-m16-5g", "galaxy-m34", "galaxy-m34-5g", "galaxy-m35", "galaxy-m35-5g", "galaxy-m36", "galaxy-m36-5g", "galaxy-m54", "galaxy-m54-5g", "galaxy-m55", "galaxy-m55-5g", "galaxy-m55s", "galaxy-m55s-5g", "galaxy-m56", "galaxy-m56-5g", "galaxy-quantum-5", "galaxy-s23", "galaxy-s23-fe", "galaxy-s23-plus", "galaxy-s23-ultra", "galaxy-s24", "galaxy-s24-fe", "galaxy-s24-plus", "galaxy-s24-ultra", "galaxy-s24-ultra-5g", "galaxy-s25", "galaxy-s25-edge", "galaxy-s25-fe", "galaxy-s25-plus", "galaxy-s25-slim", "galaxy-s25-slim-5g", "galaxy-s25-ultra", "galaxy-s25-ultra-5g", "galaxy-s26", "galaxy-s26-fe", "galaxy-s26-fe-5g", "galaxy-s26-plus", "galaxy-s26-ultra", "galaxy-s26-ultra-5g", "galaxy-tab-active-5-phone-edition", "galaxy-xcover-7", "galaxy-z-flip-5", "galaxy-z-flip-6", "galaxy-z-flip-7", "galaxy-z-flip-7-fe", "galaxy-z-flip-7-fe-5g", "galaxy-z-flip-8", "galaxy-z-flip-8-5g", "galaxy-z-fold-5", "galaxy-z-fold-6", "galaxy-z-fold-6-slim", "galaxy-z-fold-7", "galaxy-z-fold-8", "galaxy-z-fold-8-5g", "galaxy-z-fold-8-ultra", "galaxy-z-fold-8-ultra-5g", "galaxy-z-fold-special-edition"]
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
    if key.startswith("samsung"):
        pick = []
        for u in acc:
            if "/business/" in u or "/smartphones/" not in u: continue
            seg = u.rstrip("/").split("/")
            seg = seg[-2] if seg[-1] == "buy" else seg[-1]
            if any(seg.startswith(sg + "-") for sg in SLUGS): pick.append(u)
    else:
        pick = [u for u in acc if all(k in u for k in keys)]
    pick = pick[:CAP]
    with ThreadPoolExecutor(8) as ex:
        out = list(ex.map(parse, pick))
    got = [i for lst in out for i in lst]
    for g in got: g["site"] = key
    items += got
    summ.append(f"{key}: urls_in_sitemap={len(acc)} fetched={len(pick)} with_price={len(got)}")
for dom in ["https://www.mi.com", "https://www.hihonor.com"]:
    try:
        rb = get(dom + "/robots.txt", 20)
        diag.append(dom + " robots: " + re.sub(r"\s+", " ", rb)[:260])
    except Exception as e:
        diag.append(dom + " robots ERR " + str(e)[:40])
    for p in ["/sa/sitemap.xml", "/ae/sitemap.xml", "/sitemap.xml", "/sitemap_index.xml"]:
        try:
            x = get(dom + p, 20); diag.append(dom + p + " OK " + str(len(x)) + " loc=" + str(len(re.findall("<loc>", x))))
        except Exception as e:
            diag.append(dom + p + " ERR " + str(e)[:30])
json.dump(items, open("gulf-raw.json", "w"), ensure_ascii=False)
text = "\n".join(summ + diag[:14] + [f"{i['site']} | {i['name']} | {i['price']} {i['cur']}" for i in items[:6]])
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
