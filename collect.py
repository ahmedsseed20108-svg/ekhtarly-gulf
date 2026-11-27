import urllib.request, urllib.error, urllib.parse, re, json, os
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}
def req(url, to=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=to) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, ""
URL = "https://btech.com/ar/c/mobiles-tablets/mobile-phones"
def meta(h):
    t = h.replace('\\"', '"')
    m = re.search(r'"total_items":(\d+),"page":(\d+),"page_size":(\d+),"total_pages":(\d+)', t)
    names = re.findall(r'"sku":"[^"]+","name":"([^"]{5,60})"', t)[:3]
    return {"meta": list(m.groups()) if m else None, "names": names}
out = {}
st, h = req(URL)
t = h.replace('\\"', '"')
i = t.find('"key":"categories"')
out["filters_head"] = re.sub(r"\s+", " ", t[max(0, i - 200):i + 1800])
keys = re.findall(r'\{"key":"([a-z_0-9]+)","name":"([^"]+)","type":"([a-z_]+)"', t)
out["filter_keys"] = keys[:20]
j = t.find('"key":"brand"')
out["brand_head"] = re.sub(r"\s+", " ", t[j:j + 900]) if j >= 0 else None
out["base"] = meta(h)
tests = ["?brand=samsung", "?brands=samsung", "?filters=brand:samsung", "?filter[brand]=samsung", "?brand%5B%5D=samsung", "?brand=Samsung", "?manufacturer=samsung", "?brand_name=samsung"]
out["tests"] = {}
for q in tests:
    s2, hh = req(URL + q)
    out["tests"][q] = {"st": s2, **meta(hh)}
for sub in ["https://btech.com/ar/c/mobiles-tablets/smartphones", "https://btech.com/ar/c/samsung-mobile-phones", "https://btech.com/ar/brand/samsung"]:
    s2, hh = req(sub)
    out["tests"][sub[-40:]] = {"st": s2, **meta(hh)}
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3800]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
