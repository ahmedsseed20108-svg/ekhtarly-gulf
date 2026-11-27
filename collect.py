import urllib.request, urllib.error, re, json, os
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}
def req(url, data=None, hdr=None, to=40):
    h = dict(UA)
    if hdr: h.update(hdr)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=to) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, "ERR " + str(e)[:60]
BASE = "https://btech.com"
URL = BASE + "/ar/c/mobiles-tablets/mobile-phones"
D = "https://retail-online-prod.btech.com/api/v1/green/discovery/api/v1"
SELLER = "f233878d-c4df-4b14-8816-5c9b6a3d2f84"
out = {"slugs": [], "post": {}}
st, html = req(URL)
t = html.replace('\\"', '"')
sl = []
for m in re.findall(r'"slug":"([^"]+)"', t):
    if m not in sl: sl.append(m)
out["slugs"] = [s for s in sl if "mobile" in s or "phone" in s][:12]
out["slug_sample"] = sl[:12]
cands = list(dict.fromkeys(out["slugs"] + ["mobile-phones", "mobiles-tablets", "mobiles-tablets/mobile-phones"]))[:6]
H = [
 ("plain", {"Content-Type": "application/json", "Accept": "application/json"}),
 ("origin", {"Content-Type": "application/json", "Accept": "application/json", "Origin": BASE, "Referer": URL}),
 ("seller", {"Content-Type": "application/json", "Accept": "application/json", "Origin": BASE, "Referer": URL, "x-seller-id": SELLER, "seller-id": SELLER, "localization_code": "2", "Accept-Language": "ar"}),
]
done = False
for s in cands:
    for hn, hh in H:
        body = json.dumps({"slug": s, "page": 2, "page_size": 20}).encode()
        code, r = req(D + "/collections/products", data=body, hdr=hh)
        out["post"][f"{s}|{hn}"] = f"{code} {r[:220]}"
        if code == 200 and '"page"' in r:
            out["WIN"] = {"slug": s, "hdr": hn}
            m = re.search(r'"total_items":(\d+)', r)
            out["WIN"]["meta"] = re.findall(r'"(?:total_items|page|page_size|total_pages)":\d+', r)[:6]
            out["WIN"]["sample"] = r[:900]
            done = True; break
    if done: break
code, r = req(D + "/products/search?query=samsung&page=1&page_size=5", hdr={"Accept": "application/json", "Origin": BASE})
out["search_get"] = f"{code} {r[:200]}"
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3800]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
