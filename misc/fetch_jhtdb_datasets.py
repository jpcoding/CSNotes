"""
Fetch all JHTDB dataset metadata and dump to JSON.
Scrapes the JHTDB website pages + parses the WSDL for available API operations.
"""

import json
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree import ElementTree as ET

BASE = "https://turbulence.pha.jhu.edu"
WSDL_URL = f"{BASE}/service/turbulence.asmx?WSDL"

# Token for API probing — copied from download.py (or set your own)
TOKEN = "edu.jhu.pha.turbulence.testing-201406"

# All field codes the API might support — probed live against each dataset
ALL_FIELD_CODES = ["u", "p", "b", "a", "d", "t"]

# The dataset page URLs are discovered automatically from /datasets.aspx.
# The API dataset name strings (e.g. "isotropic1024coarse") are internal API codes
# not written anywhere in the HTML — this is the only thing that must be specified manually.
# A single HTML page can cover multiple API dataset variants (e.g. coarse vs fine).
PAGE_TO_API_NAMES = {
    "Forced_isotropic_turbulence.aspx": ["isotropic1024coarse", "isotropic1024fine"],
    "Forced_MHD_turbulence.aspx":       ["mhd1024"],
    "Channel_Flow.aspx":                ["channel"],
    "Homogeneous_buoyancy_driven_turbulence.aspx": ["mixing"],
    "Isotropic4096.aspx":               ["isotropic4096"],
    "Rotstrat4096.aspx":                ["rotstrat4096"],
    "Transition_bl.aspx":               ["transition_bl"],
    "Channel5200.aspx":                 ["channel5200"],
    "Isotropic8192.aspx":               ["isotropic8192"],
}

FIELD_DESCRIPTIONS = {
    "u": "velocity (3-component: ux, uy, uz)",
    "p": "pressure (scalar)",
    "b": "magnetic field (3-component: bx, by, bz)",
    "a": "vector potential (3-component: ax, ay, az)",
    "d": "density (scalar)",
    "t": "temperature (scalar)",
}


def _soap_cutout(dataset: str, field: str, token: str) -> str:
    """Build a minimal 1×1×1 GetAnyCutoutWeb SOAP body."""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <GetAnyCutoutWeb xmlns="http://turbulence.pha.jhu.edu/">
      <authToken>{token}</authToken>
      <dataset>{dataset}</dataset>
      <field>{field}</field>
      <T>1</T>
      <x_start>1</x_start><y_start>1</y_start><z_start>1</z_start>
      <x_end>1</x_end><y_end>1</y_end><z_end>1</z_end>
      <x_step>1</x_step><y_step>1</y_step><z_step>1</z_step>
      <filter_width>1</filter_width>
      <addr>none</addr>
    </GetAnyCutoutWeb>
  </soap12:Body>
</soap12:Envelope>"""


def _probe_one(dataset: str, field: str, token: str) -> tuple[str, str, bool, str]:
    """
    Send a 1×1×1 cutout request for (dataset, field).
    Returns (dataset, field, supported: bool, reason: str).
    """
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}
    soap = _soap_cutout(dataset, field, token)
    try:
        r = requests.post(
            f"{BASE}/service/turbulence.asmx",
            data=soap, headers=headers, timeout=30
        )
        body = r.text
        if r.status_code == 200 and "GetAnyCutoutWebResult" in body:
            # Parse and confirm there is actual base64 payload
            root = ET.fromstring(r.content)
            ns = {"jhtdb": "http://turbulence.pha.jhu.edu/"}
            result = root.find(".//jhtdb:GetAnyCutoutWebResult", ns)
            if result is not None and result.text:
                return dataset, field, True, "ok"
        # SOAP fault or empty result
        fault = re.search(r"<[^>]*[Tt]ext[^>]*>([^<]{5,})<", body)
        reason = fault.group(1).strip() if fault else f"HTTP {r.status_code}"
        return dataset, field, False, reason
    except Exception as e:
        return dataset, field, False, str(e)


def probe_all_fields(
    dataset_names: list[str],
    token: str,
    max_workers: int = 1,
) -> dict[str, list[str]]:
    """
    Probe every (dataset, field) combination in parallel.
    Returns {dataset_name: [supported_field, ...]}.
    """
    jobs = [
        (ds, field)
        for ds in dataset_names
        for field in ALL_FIELD_CODES
    ]
    total = len(jobs)
    print(f"Probing {total} (dataset, field) combinations with {max_workers} workers...")

    results: dict[str, list[str]] = {ds: [] for ds in dataset_names}
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_probe_one, ds, field, token): (ds, field)
            for ds, field in jobs
        }
        for future in as_completed(futures):
            ds, field, supported, reason = future.result()
            done += 1
            status = "✓" if supported else "✗"
            print(f"  [{done:2d}/{total}] {status} {ds!r:30s} field={field!r}  {'' if supported else reason}")
            if supported:
                results[ds].append(field)

    # Sort fields consistently
    for ds in results:
        results[ds] = [f for f in ALL_FIELD_CODES if f in results[ds]]
    return results


def discover_dataset_pages() -> dict[str, str]:
    """
    Scrape /datasets.aspx and return {page_filename: full_url} for every
    dataset detail page linked from it. No hardcoding of URLs needed.
    """
    url = f"{BASE}/datasets.aspx"
    print(f"Discovering dataset pages from {url} ...")
    html = fetch_page_text(url)

    # Find all relative .aspx hrefs that do NOT start with / (those are nav links)
    raw = re.findall(r'href=["\']([A-Za-z][^"\']*\.aspx)["\']', html)
    # Deduplicate and filter out non-dataset pages (nav links start with /)
    skip = {"datasets.aspx"}
    pages = {}
    for filename in dict.fromkeys(raw):  # preserves order, deduplicates
        if filename not in skip:
            pages[filename] = f"{BASE}/{filename}"

    print(f"  Found {len(pages)} dataset pages: {list(pages.keys())}")
    return pages


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


def build_dataset_info(probed_fields: dict[str, list[str]]) -> list[dict]:
    datasets = []

    # Step 1: auto-discover dataset pages from /datasets.aspx
    discovered_pages = discover_dataset_pages()

    # Step 2: build flat {api_dataset_name -> url} by expanding PAGE_TO_API_NAMES,
    # only for pages that were actually discovered on the site
    dataset_pages: dict[str, str] = {}
    for filename, url in discovered_pages.items():
        api_names = PAGE_TO_API_NAMES.get(filename)
        if api_names:
            for name in api_names:
                dataset_pages[name] = url
        else:
            # Newly added page with no known API name — record it as-is so it
            # still appears in output (under the filename as a placeholder name)
            dataset_pages[filename] = url

    # Step 3: fetch each page (cache to avoid re-fetching shared pages)
    html_cache: dict[str, str] = {}
    for dataset_name, url in dataset_pages.items():
        print(f"Fetching page for dataset '{dataset_name}': {url}")

        if url not in html_cache:
            html_cache[url] = fetch_page_text(url)
        html = html_cache[url]

        bullets = extract_bullets(html)
        params = extract_key_params(bullets)

        # Use API-probed fields instead of hardcoded list
        fields = probed_fields.get(dataset_name, [])

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

    # 1. Probe field availability against live API
    print("\n=== Probing field availability via API ===")
    all_dataset_names = [
        name
        for names in PAGE_TO_API_NAMES.values()
        for name in names
    ]
    probed_fields = probe_all_fields(all_dataset_names, TOKEN, max_workers=1)

    # 2. Dataset metadata (uses probed fields)
    print("\n=== Fetching dataset pages ===")
    result["datasets"] = build_dataset_info(probed_fields)

    # 3. WSDL operations
    print("\n=== Fetching WSDL operations ===")
    result["api_operations"] = fetch_wsdl_operations(WSDL_URL)

    # 4. Field legend
    result["field_legend"] = FIELD_DESCRIPTIONS

    # 5. GetAnyCutoutWeb parameters (what your download.py uses)
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
