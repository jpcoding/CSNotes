import os
import base64
import requests
import xml.etree.ElementTree as ET
from multiprocessing import Pool, Lock, Manager
import time
import random 

# Constants
BLOCK_SIZE = 256
NUM_BLOCKS = 32
DATASET = "isotropic8192"
FIELD = "u"
TOKEN = "USER_TOKEN_HERE" # Replace with your actual token
TSTEP = 1
FILTER_WIDTH = 1
ADDR = "none"
X_STEP = Y_STEP = Z_STEP = 1
OUTDIR = "iso8192_f32"
PREFIX = "iso8192"
URL = "https://turbulence.pha.jhu.edu/service/turbulence.asmx"
HEADERS = {"Content-Type": "application/soap+xml; charset=utf-8"}
LOG_FILE = "downloaded.txt"

os.makedirs(OUTDIR, exist_ok=True)

def build_soap_body(x_start, x_end, y_start, y_end, z_start, z_end):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <GetAnyCutoutWeb xmlns="http://turbulence.pha.jhu.edu/">
      <authToken>{TOKEN}</authToken>
      <dataset>{DATASET}</dataset>
      <field>{FIELD}</field>
      <T>{TSTEP}</T>
      <x_start>{x_start}</x_start>
      <y_start>{y_start}</y_start>
      <z_start>{z_start}</z_start>
      <x_end>{x_end}</x_end>
      <y_end>{y_end}</y_end>
      <z_end>{z_end}</z_end>
      <x_step>{X_STEP}</x_step>
      <y_step>{Y_STEP}</y_step>
      <z_step>{Z_STEP}</z_step>
      <filter_width>{FILTER_WIDTH}</filter_width>
      <addr>{ADDR}</addr>
    </GetAnyCutoutWeb>
  </soap12:Body>
</soap12:Envelope>"""


def download_block(args):
    indices, downloaded_set, lock = args
    i, j, k = indices
    tag = f"{PREFIX}_{i}_{j}_{k}"

    if tag in downloaded_set:
        print(f"[SKIP] {tag} already logged.")
        return

    filepath = os.path.join(OUTDIR, tag + ".f32")
    if os.path.exists(filepath):
        print(f"[SKIP] {tag} already exists on disk.")
        with lock:
            with open(LOG_FILE, "a") as log:
                log.write(tag + "\n")
        return

    x_start = i * BLOCK_SIZE + 1
    y_start = j * BLOCK_SIZE + 1
    z_start = k * BLOCK_SIZE + 1
    x_end = x_start + BLOCK_SIZE - 1
    y_end = y_start + BLOCK_SIZE - 1
    z_end = z_start + BLOCK_SIZE - 1

    soap_body = build_soap_body(x_start, x_end, y_start, y_end, z_start, z_end)

    max_retries = 5
    delay = 2  # start with 2 seconds on first failure

    for attempt in range(max_retries):
        try:
            with requests.Session() as session:
                response = session.post(URL, data=soap_body, headers=HEADERS)

                if response.status_code == 200:
                    tree = ET.fromstring(response.content)
                    ns = {'soap': 'http://www.w3.org/2003/05/soap-envelope',
                          'jhtdb': 'http://turbulence.pha.jhu.edu/'}
                    result = tree.find('.//jhtdb:GetAnyCutoutWebResult', ns)
                    if result is not None:
                        binary_data = base64.b64decode(result.text)
                        with open(filepath, "wb") as f:
                            f.write(binary_data)
                        print(f"[DONE] {tag}")
                        with lock:
                            with open(LOG_FILE, "a") as log:
                                log.write(tag + "\n")
                        return
                    else:
                        raise Exception("No data in SOAP response")
                else:
                    raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            print(f"[RETRY {attempt+1}] Block {tag} failed: {e}")
            sleep_time = delay + random.uniform(0, 1)  # jitter helps avoid synchronized retries
            print(f"Sleeping {sleep_time:.1f}s before retrying...")
            time.sleep(sleep_time)
            delay = min(delay * 2, 64)  # cap delay at 64 seconds

    print(f"[FAIL] Block {tag} permanently failed after {max_retries} retries.")

# Build job list
job_list = [(i, j, k) for i in range(NUM_BLOCKS) for j in range(NUM_BLOCKS) for k in range(NUM_BLOCKS)]
# partial_job_list = job_list[:128]  # Optional limit
partial_job_list = job_list

# Load downloaded tags
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        downloaded = set(line.strip() for line in f)
else:
    downloaded = set()

if __name__ == "__main__":
    with Manager() as manager:
        lock = manager.Lock()
        downloaded_set = manager.dict({tag: True for tag in downloaded})
        tasks = [(indices, downloaded_set, lock) for indices in partial_job_list]

        with Pool(processes=16) as pool:
            pool.map(download_block, tasks)
