"""
Fetch all JHTDB dataset metadata and dump to JSON.
Scrapes the JHTDB website pages + parses the WSDL for available API operations.
"""

import json
import re
import requests
from xml.etree import ElementTree as ET

BASE = "https://turbulence.pha.jhu.edu"
WSDL_URL = f"{BASE}/service/turbulence.asmx?WSDL"

DATASET_PAGES = {
    "isotropic1024coarse": f"{BASE}/Forced_isotropic_turbulence.aspx",
    "isotropic1024fine":   f"{BASE}/Forced_isotropic_turbulence.aspx",
    "mhd1024":             f"{BASE}/Forced_MHD_turbulence.aspx",
    "channel":             f"{BASE}/Channel_Flow.aspx",
    "mixing":              f"{BASE}/Homogeneous_buoyancy_driven_turbulence.aspx",
    "isotropic4096":       f"{BASE}/Isotropic4096.aspx",
    "rotstrat4096":        f"{BASE}/Rotstrat4096.aspx",
    "transition_bl":       f"{BASE}/Transition_bl.aspx",
    "channel5200":         f"{BASE}/Channel5200.aspx",
    "isotropic8192":       f"{BASE}/Isotropic8192.aspx",
}

# Known fields per dataset (from documentation)
DATASET_FIELDS = {
    "isotropic1024coarse": ["u", "p"],
    "isotropic1024fine":   ["u", "p"],
    "mhd1024":             ["u", "p", "b", "a"],
    "channel":             ["u", "p"],
    "mixing":              ["u", "p", "d", "t"],
    "isotropic4096":       ["u"],
    "rotstrat4096":        ["u", "t"],
    "transition_bl":       ["u", "p"],
    "channel5200":         ["u", "p"],
    "isotropic8192":       ["u", "p"],
}

FIELD_DESCRIPTIONS = {
    "u": "velocity (3-component: ux, uy, uz)",
    "p": "pressure (scalar)",
    "b": "magnetic field (3-component: bx, by, bz)",
    "a": "vector potential (3-component: ax, ay, az)",
    "d": "density (scalar)",
    "t": "temperature (scalar)",
}


def fetch_page_text(url: str) -> str:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return f"ERROR: {e}"


def extract_bullets(html: str) -> list[str]:
    """Pull out <li> bullet text from the HTML page."""
    items = re.findall(r"<li>(.*?)</li>", html, re.DOTALL | re.IGNORECASE)
    results = []
    for item in items:
        # strip inner tags, decode common entities
        text = re.sub(r"<[^>]+>", "", item)
        text = text.replace("&times;", "×").replace("&pi;", "π")
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            results.append(text)
    return results


def extract_key_params(bullets: list[str]) -> dict:
    """Parse key numeric parameters from bullet text."""
    params = {}
    joined = " ".join(bullets)

    def find(pattern, key, cast=str):
        m = re.search(pattern, joined, re.IGNORECASE)
        if m:
            try:
                params[key] = cast(m.group(1).replace(",", "").replace(" ", ""))
            except Exception:
                params[key] = m.group(1).strip()

    find(r"Grid[:\s]+(\d[\d,×x\s]+\d)", "grid")
    find(r"Domain[:\s]+([^\n•]+)", "domain")
    find(r"Number of snapshots available[:\s]*(\d+)", "num_snapshots", int)
    find(r"Viscosity[,\s\w]*ν\s*=\s*([^\s•]+)", "viscosity")
    find(r"Reynolds number\s*Re[^\s=]*\s*[~=]\s*([\d,.]+)", "Re_lambda")
    find(r"(\d[\d,]+)\s*nodes", "nodes")

    return params


def fetch_wsdl_operations(wsdl_url: str) -> list[dict]:
    """Parse the WSDL and return all operations with their doc strings."""
    print(f"Fetching WSDL from {wsdl_url} ...")
    r = requests.get(wsdl_url, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    ns = {
        "wsdl": "http://schemas.xmlsoap.org/wsdl/",
    }

    operations = []
    for port_type in root.findall(".//wsdl:portType", ns):
        for op in port_type.findall("wsdl:operation", ns):
            name = op.attrib.get("name", "")
            doc_el = op.find("wsdl:documentation", ns)
            doc = doc_el.text.strip() if doc_el is not None and doc_el.text else ""
            operations.append({"name": name, "description": doc})

    return sorted(operations, key=lambda x: x["name"])


def build_dataset_info() -> list[dict]:
    datasets = []
    seen_urls = {}

    for dataset_name, url in DATASET_PAGES.items():
        print(f"Fetching page for dataset '{dataset_name}': {url}")

        if url not in seen_urls:
            html = fetch_page_text(url)
            seen_urls[url] = html
        else:
            html = seen_urls[url]

        bullets = extract_bullets(html)
        params = extract_key_params(bullets)

        fields = DATASET_FIELDS.get(dataset_name, [])

        entry = {
            "dataset": dataset_name,
            "info_url": url,
            "available_fields": {f: FIELD_DESCRIPTIONS.get(f, f) for f in fields},
            "extracted_params": params,
            "bullet_points": bullets,
            "notes": [],
        }

        # Dataset-specific notes
        if dataset_name == "isotropic8192":
            entry["notes"].append("TSTEP range: 1–6")
            entry["notes"].append("Re_lambda ~1200-1300 for TSTEP 1-5, ~610 for TSTEP 6")
            entry["notes"].append("GetPosition NOT supported")
        elif dataset_name == "isotropic4096":
            entry["notes"].append("TSTEP range: 1 only (single snapshot)")
            entry["notes"].append("No pressure field available")
            entry["notes"].append("GetPosition NOT supported")
        elif dataset_name == "channel5200":
            entry["notes"].append("TSTEP range: 1–11")
            entry["notes"].append("GetPosition NOT supported; Filtering NOT supported")
        elif dataset_name == "isotropic1024coarse":
            entry["notes"].append("TSTEP range: 1–5028")
        elif dataset_name == "isotropic1024fine":
            entry["notes"].append("TSTEP range: 1–99 (fine time-step DNS frames)")
        elif dataset_name == "mhd1024":
            entry["notes"].append("TSTEP range: 1–1024")
        elif dataset_name == "channel":
            entry["notes"].append("TSTEP range: 1–4000")
        elif dataset_name == "rotstrat4096":
            entry["notes"].append("TSTEP range: 1–5")
            entry["notes"].append("GetPosition NOT supported")

        datasets.append(entry)

    return datasets


def main():
    result = {}

    # 1. Dataset metadata
    print("\n=== Fetching dataset pages ===")
    result["datasets"] = build_dataset_info()

    # 2. WSDL operations
    print("\n=== Fetching WSDL operations ===")
    result["api_operations"] = fetch_wsdl_operations(WSDL_URL)

    # 3. Field legend
    result["field_legend"] = FIELD_DESCRIPTIONS

    # 4. GetAnyCutoutWeb parameters (what your download.py uses)
    result["GetAnyCutoutWeb_parameters"] = {
        "authToken": "Your API token string",
        "dataset":   "Dataset name string (see datasets list)",
        "field":     "Field code: u, p, b, a, d, t",
        "T":         "Timestep integer (TSTEP, range depends on dataset)",
        "x_start":   "Start X coordinate (1-based)",
        "y_start":   "Start Y coordinate (1-based)",
        "z_start":   "Start Z coordinate (1-based)",
        "x_end":     "End X coordinate (inclusive)",
        "y_end":     "End Y coordinate (inclusive)",
        "z_end":     "End Z coordinate (inclusive)",
        "x_step":    "Step size in X (1 = full resolution)",
        "y_step":    "Step size in Y",
        "z_step":    "Step size in Z",
        "filter_width": "Filter width (1 = no filter)",
        "addr":      "Return address hint, use 'none'",
    }

    out_file = "jhtdb_datasets.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Written to {out_file}")
    print(f"  {len(result['datasets'])} datasets")
    print(f"  {len(result['api_operations'])} API operations")


if __name__ == "__main__":
    main()
