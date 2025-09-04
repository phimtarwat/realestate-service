from flask import Flask, request, jsonify
import requests, re

app = Flask(__name__)

GOOGLE_API_KEY = "AIzaSyB8nmRbjRFkkUj6TzSktFsjlrW9mYBqdTY"  # << ใส่ API Key ของคุณ

# Dictionary สำหรับ mapping เขต/แขวง → Zone
ZONE_MAPPING = {
    "Huai Khwang": "พระราม 9 – รัชดา – ดินแดง",
    "ห้วยขวาง": "พระราม 9 – รัชดา – ดินแดง",
    "Din Daeng": "พระราม 9 – รัชดา – ดินแดง",
    "ดินแดง": "พระราม 9 – รัชดา – ดินแดง",
    "Pathum Wan": "CBD (อโศก, สีลม, สาทร, เพลินจิต)",
    "ปทุมวัน": "CBD (อโศก, สีลม, สาทร, เพลินจิต)",
    "Bang Na": "สุขุมวิทตอนปลาย (อุดมสุข, บางนา, แบริ่ง)",
    "บางนา": "สุขุมวิทตอนปลาย (อุดมสุข, บางนา, แบริ่ง)",
    "Nonthaburi": "บางใหญ่ – นนทบุรี",
    "บางใหญ่": "บางใหญ่ – นนทบุรี",
    "Mueang Chiang Mai": "เชียงใหม่ (Lifestyle / Investor)",
    "Pattaya": "พัทยา (Luxury / Investor)",
    "Bang Lamung": "พัทยา (Luxury / Investor)"
}

def expand_short_url(short_url):
    """ขยาย short link ของ Google Maps"""
    try:
        res = requests.get(short_url, allow_redirects=True, timeout=5)
        return res.url
    except:
        return short_url

def extract_latlng_from_url(url):
    """ดึง lat,lng จาก Google Maps URL"""
    # แบบ q=lat,lng
    m = re.search(r"q=(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)

    # แบบ !3dLAT!4dLNG
    m = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)

    # แบบ /place/lat,lng
    m = re.search(r"/(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if m:
        return m.group(1), m.group(2)

    return None, None

@app.route("/reverse-geocode", methods=["GET"])
def reverse_geocode():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    maps_url = request.args.get("maps_url")

    # ถ้ามี Google Maps URL → แปลง short link → extract lat,lng
    if maps_url and not lat and not lng:
        maps_url = expand_short_url(maps_url)
        lat, lng = extract_latlng_from_url(maps_url)
        if not lat or not lng:
            return jsonify({"error": "ไม่สามารถดึง lat,lng จาก Google Maps URL"}), 400

    if not lat or not lng:
        return jsonify({"error": "ต้องส่ง lat,lng หรือ maps_url"}), 400

    # เรียก Google Reverse Geocoding API
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_API_KEY}"
    res = requests.get(url).json()

    if res.get("status") != "OK":
        return jsonify({"error": res.get("status")}), 500

    components = res["results"][0]["address_components"]
    area = None
    for comp in components:
        if "sublocality_level_1" in comp["types"] or "administrative_area_level_2" in comp["types"]:
            area = comp["long_name"]
            break

    if not area:
        return jsonify({
            "lat": lat,
            "lng": lng,
            "area": None,
            "zone": "Investor / Practical (default)"
        }), 200

    zone = ZONE_MAPPING.get(area, "Investor / Practical (default)")

    return jsonify({
        "lat": lat,
        "lng": lng,
        "area": area,
        "zone": zone
    }), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
