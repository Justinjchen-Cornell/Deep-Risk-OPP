#!/usr/bin/env python3
"""
OpenFIGI Mapper — Bloomberg Global Identifier Resolution
==========================================================
Map any security identifier (ticker, ISIN, CUSIP, SEDOL) to FIGI
and cross-reference A-shares vs H-shares for Deep-Risk-OPP.

API: OpenFIGI v3 (https://www.openfigi.com/api)
Key:  Stored in .env as OPENFIGI_API_KEY
Docs: https://www.openfigi.com/api/v3

Usage:
    from scripts.figi_mapper import map_ticker, cross_ref_ah
    result = map_ticker("0700", "HK")          # Tencent Hong Kong
    pairs  = cross_ref_ah("600036", "03968")    # CMB A vs H
"""

import os
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── API Config ───────────────────────────────────────────────
OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"

def _get_api_key():
    """Load OpenFIGI key from .env"""
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / '.env')
        return os.getenv('OPENFIGI_API_KEY')
    except ImportError:
        return None


# ─── Core Functions ────────────────────────────────────────────

def map_to_figi(ids, id_type="TICKER", exch_code=None, mic_code=None):
    """
    Resolve any identifier(s) to FIGI.

    Args:
        ids:       Single string or list of identifier strings
        id_type:   "TICKER" | "ISIN" | "CUSIP" | "SEDOL" | "ID_BB_GLOBAL"
        exch_code: Exchange code (e.g. "HK", "US", "CN")
        mic_code:  ISO MIC code (e.g. "XHKG", "XNYS", "XSHG")

    Returns:
        List of dicts: [{figi, ticker, name, exchCode, mic, ...}]
    """
    if isinstance(ids, str):
        ids = [ids]

    results = []
    for identifier in ids:
        body = [{"idType": id_type, "idValue": identifier}]
        if exch_code:
            body[0]["exchCode"] = exch_code
        if mic_code:
            body[0]["micCode"] = mic_code

        try:
            api_key = _get_api_key()
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["X-OPENFIGI-APIKEY"] = api_key

            req = urllib.request.Request(
                OPENFIGI_URL,
                data=json.dumps(body).encode('utf-8'),
                headers=headers,
            )
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())

            if data and len(data) > 0 and 'data' in data[0]:
                for item in data[0]['data']:
                    results.append({
                        "figi": item.get("figi"),
                        "name": item.get("name"),
                        "ticker": item.get("ticker"),
                        "exchCode": item.get("exchCode"),
                        "mic": item.get("micCode"),
                        "marketSector": item.get("marketSector"),
                        "securityType": item.get("securityType"),
                        "shareClassFIGI": item.get("shareClassFIGI"),
                        "uniqueID": item.get("uniqueID"),
                    })
        except Exception as e:
            results.append({"error": str(e), "identifier": identifier})

    return results


def map_ticker(ticker, exchange="HK"):
    """Quick ticker → FIGI map.
    HK: uses exchCode=HK (0883→883)
    CN: uses micCode=XSHG/XSHE based on ticker prefix (600xxx→XSHG, 000xxx/002xxx→XSHE)"""
    if exchange in ("HK",) and ticker.startswith("0"):
        ticker = ticker.lstrip("0") or "0"

    if exchange == "CN":
        # Shanghai (600xxx, 601xxx) vs Shenzhen (000xxx, 002xxx, 300xxx)
        if ticker.startswith(("6",)):
            return map_to_figi(ticker, "TICKER", mic_code="XSHG")
        elif ticker.startswith(("0", "3")):
            return map_to_figi(ticker, "TICKER", mic_code="XSHE")

    return map_to_figi(ticker, "TICKER", exch_code=exchange)


def cross_ref_ah(a_ticker, h_ticker):
    """
    Cross-reference A-share vs H-share of the same company.
    Returns both FIGIs with comparison data.

    Args:
        a_ticker: A-share ticker (e.g. "600036" for 招商银行)
        h_ticker: H-share ticker (e.g. "03968" for CMB HK)
    """
    a_result = map_ticker(a_ticker, "CN")
    h_result = map_ticker(h_ticker, "HK")

    return {
        "a_share": a_result[0] if a_result else None,
        "h_share": h_result[0] if h_result else None,
        "is_same_company": (
            a_result[0].get("shareClassFIGI") == h_result[0].get("shareClassFIGI")
            if a_result and h_result and a_result[0].get("shareClassFIGI")
            else None
        ),
    }


def figi_to_ticker(figi):
    """Reverse lookup: FIGI → ticker details."""
    return map_to_figi(figi, "ID_BB_GLOBAL")


# ─── Pre-built Resource LUTs ────────────────────────────────────

# Common HK / China energy & resource tickers for Deep-Risk-OPP
DEEP_RISK_UNIVERSE = {
    # Oil & Gas (HK)
    "中海油":     {"ticker": "0883", "exch": "HK", "name": "CNOOC Ltd"},
    "中石油":     {"ticker": "0857", "exch": "HK", "name": "PetroChina"},
    "中石化":     {"ticker": "0386", "exch": "HK", "name": "Sinopec"},
    # Coal & Energy (HK)
    "中国神华":   {"ticker": "1088", "exch": "HK", "name": "China Shenhua"},
    "中煤能源":   {"ticker": "1898", "exch": "HK", "name": "China Coal Energy"},
    # Metals & Mining (HK)
    "紫金矿业":   {"ticker": "2899", "exch": "HK", "name": "Zijin Mining"},
    "洛阳钼业":   {"ticker": "3993", "exch": "HK", "name": "CMOC Group"},
    "江西铜业":   {"ticker": "0358", "exch": "HK", "name": "Jiangxi Copper"},
    # Power / Grid (HK)
    "中广核电力": {"ticker": "1816", "exch": "HK", "name": "CGN Power"},
    # A-share counterparts
    "紫金矿业A":  {"ticker": "601899", "exch": "CN", "name": "Zijin Mining A"},
    "中国神华A":  {"ticker": "601088", "exch": "CN", "name": "China Shenhua A"},
    "长江电力":   {"ticker": "600900", "exch": "CN", "name": "Yangtze Power"},
    "宝丰能源":   {"ticker": "600989", "exch": "CN", "name": "Baofeng Energy"},
    # Shipping
    "中远海能":   {"ticker": "1138",  "exch": "HK", "name": "COSCO Shipping Energy"},
    "招商轮船":   {"ticker": "601872","exch": "CN", "name": "CMES"},
}


def resolve_universe():
    """Resolve all Deep-Risk-OPP universe tickers to FIGI.
    Returns a dict keyed by Chinese name with FIGI details."""
    resolved = {}
    for name, info in DEEP_RISK_UNIVERSE.items():
        result = map_ticker(info["ticker"], info["exch"])
        resolved[name] = {
            "input": info,
            "figi": result,
        }
    return resolved


# ─── CLI ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python figi_mapper.py map 0700 HK")
        print("  python figi_mapper.py cross 600036 03968")
        print("  python figi_mapper.py universe")
        print("  python figi_mapper.py figi BBG000B9XRY4")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "map":
        ticker = sys.argv[2] if len(sys.argv) > 2 else "0700"
        exch = sys.argv[3] if len(sys.argv) > 3 else "HK"
        results = map_ticker(ticker, exch)
        for r in results:
            print(json.dumps(r, indent=2, ensure_ascii=False))

    elif cmd == "cross":
        a = sys.argv[2] if len(sys.argv) > 2 else "600036"
        h = sys.argv[3] if len(sys.argv) > 3 else "03968"
        result = cross_ref_ah(a, h)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "universe":
        resolved = resolve_universe()
        for name, data in resolved.items():
            figi_info = data["figi"][0] if data["figi"] and "error" not in data["figi"][0] else {}
            status = figi_info.get("figi", "NOT FOUND")[:20]
            print(f"  {name:<10s} {data['input']['ticker']:<8s} → {status}")

    elif cmd == "figi":
        figi = sys.argv[2]
        results = figi_to_ticker(figi)
        for r in results:
            print(json.dumps(r, indent=2, ensure_ascii=False))