import urllib.request, re, json, os
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.read().decode("utf-8", "ignore")
out = []
SAM = [("Samsung SA", "https://www.samsung.com/sa/smartphones/galaxy-a/galaxy-a56-5g-awesome-graphite-128gb-sm-a566bzkvmea/buy/"),
       ("Samsung AE", "https://www.samsung.com/ae/smartphones/galaxy-a/galaxy-a56-5g-awesome-olive-256gb-sm-a566bzgwmea/buy/")]
for n, u in SAM:
    try:
        st, b = get(u)
        for m in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', b, re.S):
            try:
                j = json.loads(m)
            except Exception:
                continue
            for it in (j if isinstance(j, list) else [j]):
                if isinstance(it, dict) and it.get("@type") in ("Product", "ProductGroup"):
                    o = it.get("offers") or {}
                    if isinstance(o, list): o = o[0] if o else {}
                    out.append(f"{n} | {str(it.get('name'))[:50]} | sku={it.get('sku')} | {o.get('price') or o.get('lowPrice')} {o.get('priceCurrency')}")
    except Exception as e:
        out.append(f"{n} ERR {str(e)[:50]}")
LIST = [("Jarir", "https://www.jarir.com/sa-en/catalogsearch/result/?q=galaxy+a56"),
        ("Extra", "https://www.extra.com/en-sa/search/?text=galaxy+a56"),
        ("Amazon SA", "https://www.amazon.sa/s?k=Samsung+Galaxy+A56")]
for n, u in LIST:
    try:
        st, b = get(u)
        t = re.search(r'<title>(.*?)</title>', b, re.S)
        out.append(f"{n} | {st} | {len(b)//1024}KB | title={(t.group(1).strip()[:60] if t else '-')}")
        hits = [m.start() for m in re.finditer(r'(SAR|SR|ر\.س)\s?[0-9][0-9,]+|[0-9][0-9,]+\s?(SAR|SR|ر\.س)|"price"\s*:\s*"?[0-9]', b)][:3]
        for h in hits:
            out.append("   > " + re.sub(r'\s+', ' ', b[max(0, h-70):h+50]))
        a56 = len(re.findall(r'A56', b))
        out.append(f"   A56 mentions: {a56}")
    except Exception as e:
        out.append(f"{n} ERR {str(e)[:50]}")
BR = ["https://www.mi.com/sa/", "https://www.oppo.com/sa/", "https://www.realme.com/sa/", "https://www.hihonor.com/sa/", "https://www.vivo.com/sa", "https://www.mi.com/ae/", "https://www.oppo.com/ae/", "https://www.hihonor.com/ae/"]
for u in BR:
    try:
        st, b = get(u)
        out.append(f"{u} | {st} | {len(b)//1024}KB | ld={len(re.findall('application/ld.json', b))}")
    except Exception as e:
        out.append(f"{u} ERR {str(e)[:40]}")
text = "\n".join(out)
print(text)
open(os.environ["GITHUB_STEP_SUMMARY"], "a").write("```\n" + text + "\n```\n")
