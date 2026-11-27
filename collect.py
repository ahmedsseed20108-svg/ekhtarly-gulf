import urllib.request, urllib.error, json, os
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "ar,en;q=0.8"}
def req(url, data=None, hdr=None, to=8):
    h = dict(UA)
    if hdr: h.update(hdr)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=to) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, "ERR " + str(e)[:50]
J = {"Content-Type": "application/json", "Accept": "application/json", "Origin": "https://btech.com", "Referer": "https://btech.com/ar/c/mobiles-tablets/mobile-phones", "Accept-Language": "ar"}
body = json.dumps({"slug": "mobile-phones", "page": 2, "page_size": 20}).encode()
P = "/api/v1/green/discovery/api/v1"
out = {}
for h in ["https://retail.btech.com", "https://btech.com", "https://www.btech.com", "https://retail-online-prod.btech.com"]:
    for pre in [P, "/api/v1/green/discovery", "/discovery/api/v1", "/api/v1"]:
        k = h + pre + "/collections/products"
        code, r = req(k, data=body, hdr=J)
        out[k] = f"{code} {r[:170]}"
        if code == 200:
            out["WIN"] = k
code, r = req("https://retail-online-prod.btech.com/", hdr=J, to=8)
out["retail-online-prod root"] = f"{code} {r[:100]}"
code, r = req("https://retail.btech.com/", hdr=J, to=8)
out["retail root"] = f"{code} {r[:100]}"
json.dump(out, open("gulf-raw.json", "w"), ensure_ascii=False, indent=1)
text = json.dumps(out, ensure_ascii=False, indent=1)[:3800]
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
