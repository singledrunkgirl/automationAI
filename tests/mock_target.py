from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle_val():
    data = request.get_json(force=True, silent=True) or {}
    val = data.get("val", 0)
    try:
        val = int(val)
    except (ValueError, TypeError):
        val = 0

    if val == 10000000:
        return jsonify({"status": "ok"}), 200
    if val > 1000:
        return jsonify({"error": "overflow"}), 400
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4040)