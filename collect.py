import urllib.request, urllib.error, urllib.parse, re, json, os
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
def info(h):
    t = h.replace('\\"', '"')
    m = re.search(r'"total_items":(\d+),"page":(\d+),"page_size":(\d+),"total_pages":(\d+)', t)
    names = re.findall(r'"sku":"[^"]+","name":"([^"]{5,70})"', t)
    prices = re.findall(r'"final_price":(\d+)', t)
    return {"meta": list(m.groups()) if m else None, "n_names": len(names), "names": names[:4], "prices": prices[:6]}
def q(filters=None, sort=None, page=None):
    p = []
    if filters is not None: p.append("filters=" + urllib.parse.quote(json.dumps(filters, separators=(",", ":"))))
    if sort: p.append("sort=" + sort)
    if page: p.append("page=" + str(page))
    return "?" + "&".join(p)
tests = {
 "brands_arr": q({"brands": ["samsung"]}),
 "brands_str": q({"brands": "samsung"}),
 "brands_arr_page2": q({"brands": ["samsung"]}, None, 2),
 "samsung_asc": q({"brands": ["samsung"]}, "price_asc"),
 "samsung_desc": q({"brands": ["samsung"]}, "price_desc"),
 "xiaomi": q({"brands": ["xiaomi"]}),
 "pr_arr": q({"brands": ["samsung"], "price_range": [10000, 20000]}),
 "pr_obj": q({"brands": ["samsung"], "price_range": {"min": 10000, "max": 20000}}),
 "pr_str": q({"brands": ["samsung"], "price_range": "10000-20000"}),
 "sort_newest": q(None, "newest"),
 "sort_latest": q(None, "latest"),
}
out = {"tests": {}}
def run(kv):
    k, qq = kv
    s, h = req(URL + qq)
    r = info(h); r["st"] = s; r["q"] = qq[:90]
    return k, r
with ThreadPoolExecutor(6) as ex:
    for k, r in ex.map(run, tests.items()):
        out["tests"][k] = r
st, h = req(URL)
scripts = sorted(set(re.findall(r'src="(/_next/static/[^"]+\.js)"', h)))
def dl(s): return s, req(B + s, 30)[1]
sn = {}
with ThreadPoolExecutor(8) as ex:
    for s, js in ex.map(dl, scripts):
        for m in re.finditer(r'price_asc|price_desc|"newest"|relevance', js):
            sn.setdefault(s[-12:] + str(m.start() // 400), re.sub(r"\s+", " ", js[max(0, m.start() - 160):m.start() + 260]))
out["sort_snips"] = dict(list(sn.items())[:4])
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3800]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
