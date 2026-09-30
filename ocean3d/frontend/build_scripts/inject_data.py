"""
inject_data.py — rebuilds dashboard.html from dashboard_template.html by
injecting the model/floats JSON bundles and Cesium token.

Usage:
    python inject_data.py --model model_bundle.json --floats floats_bundle.json \
        --token YOUR_CESIUM_ION_TOKEN --template dashboard_template.html --out dashboard.html
"""
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default="dashboard_template.html")
    ap.add_argument("--model", required=True)
    ap.add_argument("--floats", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--out", default="dashboard.html")
    args = ap.parse_args()

    with open(args.template, encoding="utf-8") as f:
        tpl = f.read()
    with open(args.model, encoding="utf-8") as f:
        model_bundle = f.read()
    with open(args.floats, encoding="utf-8") as f:
        floats_bundle = f.read()

    out = tpl.replace("{{MODEL_BUNDLE_JSON}}", model_bundle)
    out = out.replace("{{FLOATS_BUNDLE_JSON}}", floats_bundle)
    out = out.replace("{{CESIUM_TOKEN}}", args.token)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {args.out} ({len(out)} bytes)")

if __name__ == "__main__":
    main()
