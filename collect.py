import urllib.request, re, json, os
from concurrent.futures import ThreadPoolExecutor
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}
def get(url, hdr=None, to=40):
    h = dict(UA)
    if hdr: h.update(hdr)
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=to) as r:
        return r.status, r.read().decode("utf-8", "ignore")
BASE = "https://btech.com"
URL = BASE + "/ar/c/mobiles-tablets/mobile-phones"
out = {"pages": {}, "api": {}, "snips": {}}
def info(b):
    t = b.replace('\\"', '"')
    m = re.search(r'"total_items":(\d+),"page":(\d+),"page_size":(\d+),"total_pages":(\d+)', t)
    skus = re.findall(r'"sku":"([^"]+)"', t)[:3]
    return {"meta": m.groups() if m else None, "first_skus": skus}
for q in ["", "?page=2", "?page=2&page_size=100", "?page_size=100", "?p=2", "?page=3"]:
    try:
        st, b = get(URL + q)
        out["pages"][q or "base"] = {"st": st, **info(b)}
    except Exception as e:
        out["pages"][q or "base"] = "ERR " + str(e)[:60]
try:
    st, b = get(URL + "?page=2", hdr={"RSC": "1"})
    out["pages"]["rsc_page2"] = {"st": st, "len": len(b), **info(b)}
except Exception as e:
    out["pages"]["rsc_page2"] = "ERR " + str(e)[:60]
st, html = get(URL)
scripts = sorted(set(re.findall(r'src="(/_next/static/[^"]+\.js)"', html)))
out["n_scripts"] = len(scripts)
def dl(s):
    try: return s, get(BASE + s, to=40)[1]
    except Exception: return s, ""
paths = {}
with ThreadPoolExecutor(8) as ex:
    for s, js in ex.map(dl, scripts):
        for m in re.findall(r'["`\'](/api/[A-Za-z0-9_\-/{}$.?=&]{2,90})', js):
            paths[m] = paths.get(m, 0) + 1
        for k in ["page_size", "total_pages", "vxstore", "total_items"]:
            for mm in list(re.finditer(k, js))[:1]:
                out["snips"].setdefault(k + "@" + s[-18:], re.sub(r"\s+", " ", js[max(0, mm.start() - 160):mm.start() + 200]))
out["api_paths"] = dict(sorted(paths.items(), key=lambda x: -x[1])[:40])
out["snips"] = dict(list(out["snips"].items())[:8])
for p in list(paths)[:0]: pass
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3800]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
