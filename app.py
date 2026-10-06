import base64, json, math, os, re
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")
BASE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(BASE, "photos")
DB = os.path.join(BASE, "people.json")
os.makedirs(PHOTOS, exist_ok=True)


def load():
    try:
        with open(DB) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(data):
    with open(DB, "w") as f:
        json.dump(data, f)


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/photos/<path:fn>")
def photo(fn):
    return send_from_directory(PHOTOS, fn)


@app.route("/api/people")
def people():
    return jsonify(load())


@app.route("/api/register", methods=["POST"])
def register():
    d = request.get_json()
    name = (d.get("name") or "").strip()
    if not name or not d.get("descriptor"):
        return jsonify(error="Name and face are required"), 400

    # block the same face being registered under a different name
    for p in load():
        if p["name"].lower() != name.lower() and dist(p["descriptor"], d["descriptor"]) < 0.5:
            return jsonify(error=f"This face is already registered as {p['name']}"), 409

    safe = re.sub(r"[^A-Za-z0-9_-]", "_", name)
    fname = f"{safe}.jpg"
    with open(os.path.join(PHOTOS, fname), "wb") as f:
        f.write(base64.b64decode(d["photo"].split(",", 1)[1]))

    data = [p for p in load() if p["name"].lower() != name.lower()]
    data.append({"name": name, "photo": fname, "descriptor": d["descriptor"]})
    save(data)
    return jsonify(ok=True)


@app.route("/api/people/<name>", methods=["DELETE"])
def delete(name):
    data = load()
    for p in data:
        if p["name"] == name:
            try:
                os.remove(os.path.join(PHOTOS, p["photo"]))
            except OSError:
                pass
    save([p for p in data if p["name"] != name])
    return jsonify(ok=True)



@app.route("/favicon.ico")
def favicon():
      return "", 204
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)