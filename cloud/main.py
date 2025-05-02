import time, os, json
import google.auth

from flask import Request, make_response, jsonify
from google.cloud import dlp_v2

# ─── Fetch project ID ────────────────────────────────
# 1) First look for PROJECT_ID (from set-env-vars)
# 2) Then fallback to GOOGLE_CLOUD_PROJECT / GCP_PROJECT
# 3) Finally fallback to ADC via google.auth.default()
PROJECT_ID = (
    os.getenv("PROJECT_ID")            # what you set in Gen2
    or os.getenv("GOOGLE_CLOUD_PROJECT")
    or os.getenv("GCP_PROJECT")
)
if not PROJECT_ID:
    # last-ditch: read from ADC (metadata server)
    _, PROJECT_ID = google.auth.default()

PARENT = f"projects/{PROJECT_ID}/locations/global"

# ─── Init DLP client & info-types ─────────────────────
dlp        = dlp_v2.DlpServiceClient()
INFO_TYPES = [{"name": n} for n in (
    "PERSON_NAME",
    "DATE",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "LOCATION",      # ID_NUMBER removed
)]

def _cors(resp):
    resp.headers['Access-Control-Allow-Origin']  = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

def deid(request: Request):
    # 1) Pre-flight
    if request.method == 'OPTIONS':
        return _cors(make_response('', 204))

    # 2) Parse & validate
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text:
        return _cors(make_response(jsonify({"error": "no text"}), 400))

    t0    = time.time()
    item  = {"value": text}

    # 3) Inspect for PHI spans
    try:
        inspect_resp = dlp.inspect_content(
            request={
                "parent":         PARENT,
                "item":           item,
                "inspect_config": {"info_types": INFO_TYPES, "include_quote": True}
            }
        )
    except Exception as e:
        return _cors(make_response(jsonify({
            "error": f"Inspect failed: {e}"
        }), 500))

    phi_spans = []
    for finding in inspect_resp.result.findings or []:
        loc = finding.location.byte_range
        phi_spans.append({
            "start": int(loc.start),
            "end":   int(loc.end),
            "type":  finding.info_type.name
        })

    # 4) De-identify (replace PHI with “★”)
    try:
        deid_resp = dlp.deidentify_content(
            request={
                "parent":             PARENT,
                "item":               item,
                "deidentify_config": {
                    "info_type_transformations": {
                        "transformations": [{
                            "info_types": INFO_TYPES,
                            "primitive_transformation": {
                                "replace_config": {
                                    "new_value": { "string_value": "★" }
                                }
                            }
                        }]
                    }
                }
            }
        )
    except Exception as e:
        return _cors(make_response(jsonify({
            "error": f"De-identify failed: {e}"
        }), 500))

    elapsed = round((time.time() - t0) * 1000, 1)

    # 5) Return JSON + CORS
    resp = make_response(jsonify({
        "clean_text": deid_resp.item.value,
        "phi_spans":  phi_spans,
        "elapsed_ms": elapsed
    }), 200)
    return _cors(resp)