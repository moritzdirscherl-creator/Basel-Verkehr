#!/usr/bin/env python3
"""Holt die Linienverläufe (Tram/Bus) für die Region Basel aus OpenStreetMap
und schreibt sie kompakt nach shapes.json. Nur Standardbibliothek."""
import json, math, time, urllib.parse, urllib.request, datetime, sys

BBOX = (47.40, 7.45, 47.66, 7.82)  # S, W, N, E
QUERY = f"""[out:json][timeout:300];
relation["type"="route"]["route"~"^(tram|bus|trolleybus)$"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
out geom;"""
SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

def fetch():
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    for attempt in range(3):
        for url in SERVERS:
            try:
                req = urllib.request.Request(url, data=body, headers={"User-Agent": "laengts-basel-shapes/1.0"})
                with urllib.request.urlopen(req, timeout=360) as r:
                    data = json.load(r)
                if data.get("elements"):
                    print(f"ok: {url} ({len(data['elements'])} Relationen)")
                    return data
                print(f"leer: {url}")
            except Exception as e:
                print(f"fehler {url}: {e}")
        time.sleep(30 * (attempt + 1))
    sys.exit("Kein Overpass-Server erreichbar")

def d2(a, b):
    return (a[0] - b[0]) ** 2 + ((a[1] - b[1]) * math.cos(math.radians(a[0]))) ** 2

def chain(ways):
    out = []
    for w in ways:
        if not out:
            out = list(w)
            continue
        if len(out) == len(ways[0]) and out == list(ways[0]):
            # Richtung des ersten Wegs an den zweiten anpassen
            best = min([(d2(out[-1], w[0]), 0), (d2(out[-1], w[-1]), 1), (d2(out[0], w[0]), 2), (d2(out[0], w[-1]), 3)])[1]
            if best in (2, 3):
                out.reverse()
        if d2(out[-1], w[-1]) < d2(out[-1], w[0]):
            w = list(reversed(w))
        out.extend(w[1:] if d2(out[-1], w[0]) < 1e-12 else w)
    return out

def rdp(pts, eps_m=3.0):
    if len(pts) < 3:
        return pts
    lat0 = math.radians(pts[0][0])
    xy = [((p[1]) * 111320 * math.cos(lat0), p[0] * 110540) for p in pts]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = xy[a]; bx, by = xy[b]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, py = xy[i]
            if L == 0:
                dist = (px - ax) ** 2 + (py - ay) ** 2
            else:
                t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
                dist = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
            if dist > best:
                best, bi = dist, i
        if best > eps_m * eps_m:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]

def main():
    data = fetch()
    routes = []
    for el in data["elements"]:
        if el.get("type") != "relation":
            continue
        tags = el.get("tags", {})
        ref = (tags.get("ref") or "").strip()
        if not ref:
            continue
        ways = [[(g["lat"], g["lon"]) for g in m["geometry"]]
                for m in el.get("members", [])
                if m.get("type") == "way" and m.get("geometry")
                and not str(m.get("role", "")).startswith(("platform", "stop"))]
        ways = [w for w in ways if len(w) > 1]
        if not ways:
            continue
        line = rdp(chain(ways))
        routes.append({
            "t": "bus" if tags.get("route") in ("bus", "trolleybus") else "tram",
            "r": ref,
            "n": tags.get("name", ""),
            "l": [[round(a, 5), round(b, 5)] for a, b in line],
        })
    routes.sort(key=lambda r: (r["t"], r["r"], r["n"]))
    out = {"generated": datetime.datetime.utcnow().isoformat() + "Z",
           "source": "© OpenStreetMap-Mitwirkende (ODbL)", "routes": routes}
    with open("shapes.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(routes)} Linienverläufe geschrieben")

if __name__ == "__main__":
    main()
