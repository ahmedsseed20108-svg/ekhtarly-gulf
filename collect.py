import urllib.request, re, json, os
from concurrent.futures import ThreadPoolExecutor
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}
def req(url, data=None, hdr=None, to=40):
    h = dict(UA)
    if hdr: h.update(hdr)
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=to) as r:
        return r.status, r.read().decode("utf-8", "ignore")
BASE = "https://btech.com"
URL = BASE + "/ar/c/mobiles-tablets/mobile-phones"
out = {"snips": {}, "hosts": [], "post": {}}
st, html = req(URL)
scripts = sorted(set(re.findall(r'src="(/_next/static/[^"]+\.js)"', html)))
def dl(s):
    try: return s, req(BASE + s)[1]
    except Exception: return s, ""
allhosts = set(); paths = {}
with ThreadPoolExecutor(8) as ex:
    for s, js in ex.map(dl, scripts):
        for k in ["collectionProducts", "baseURL", "NEXT_PUBLIC_API", "API_URL", "API_BASE"]:
            for mm in list(re.finditer(k, js))[:2]:
                out["snips"][k + "@" + s[-14:] + str(mm.start())] = re.sub(r"\s+", " ", js[max(0, mm.start() - 120):mm.start() + 260])
        for h in re.findall(r'https://[a-z0-9.\-]*btech[a-z0-9.\-]*[^"\'`\s\\)]{0,60}', js):
            allhosts.add(h)
        for m in re.findall(r'collectionProducts:"([^"]+)"', js):
            paths[m] = 1
out["hosts"] = sorted(allhosts)[:40]
out["paths"] = list(paths)
out["snips"] = dict(list(out["snips"].items())[:12])
slugs = ["mobile-phones", "mobiles-tablets/mobile-phones", "mobiles-tablets", "mobile-phones-tablets"]
bases = [BASE, BASE + "/api", "https://api.btech.com"] + [h.split("/", 3)[0] + "//" + h.split("/")[2] for h in list(allhosts)[:6]]
for b in dict.fromkeys(bases):
    for p in (list(paths) or ["/api/collections/products"]):
        for sl in slugs[:2]:
            body = json.dumps({"slug": sl, "page": 2, "page_size": 20}).encode()
            key = b + p + " slug=" + sl
            try:
                st, r = req(b + p, data=body, hdr={"Content-Type": "application/json", "Accept": "application/json", "Origin": BASE, "Referer": URL})
                out["post"][key] = f"{st} {r[:160]}"
                if st == 200: break
            except Exception as e:
                out["post"][key] = "ERR " + str(e)[:50]
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3800]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
