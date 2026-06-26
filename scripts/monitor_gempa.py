#!/usr/bin/env python3
"""
Monitor gempa bumi di sekitar Yogyakarta dari BMKG.
Jika ada gempa baru ≥ M2.5 dalam radius 150km, print alert.
Jika tidak ada gempa baru, diam (no output = no notification).
"""
import urllib.request
import xml.etree.ElementTree as ET
import json
import os
from math import radians, sin, cos, sqrt, atan2

SEEN_FILE = os.path.expanduser("~/sembako/gempa_seen.json")
JOJ_LAT, JOJ_LON = -7.7956, 110.3695
RADIUS_KM = 150
MIN_MAG = 2.5

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return json.load(f)
    return {"seen": []}

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)

def check_earthquake():
    url = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/xml, text/xml, */*",
    }
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read().decode("utf-8")
        
        root = ET.fromstring(xml_data)
        gempa = root.find(".//gempa")
        
        if gempa is None:
            return
        
        tanggal = gempa.findtext("Tanggal", "")
        jam = gempa.findtext("Jam", "")
        mag = float(gempa.findtext("Magnitude", "0"))
        kedalaman = gempa.findtext("Kedalaman", "")
        wilayah = gempa.findtext("Wilayah", "")
        potensi = gempa.findtext("Potensi", "")
        dirasakan = gempa.findtext("Dirasakan", "")
        shakemap = gempa.findtext("Shakemap", "")
        
        lintang_str = gempa.findtext("Lintang", "0")
        bujur_str = gempa.findtext("Bujur", "0")
        lat = float(lintang_str.replace(" LS", "").replace(" LU", "").strip())
        lon = float(bujur_str.replace(" BT", "").replace(" BB", "").strip())
        if "LS" in lintang_str: lat = -lat
        if "BB" in bujur_str: lon = -lon
        
        event_id = f"{tanggal}_{jam}_{mag}_{lat}_{lon}"
        seen = load_seen()
        
        if event_id in seen["seen"]:
            return  # sudah diproses
        
        dist = haversine(JOJ_LAT, JOJ_LON, lat, lon)
        
        if dist <= RADIUS_KM and mag >= MIN_MAG:
            seen["seen"].append(event_id)
            seen["seen"] = seen["seen"][-100:]
            save_seen(seen)
            
            msg = (
                f"🚨 *PERINGATAN GEMPA* 🚨\n\n"
                f"📅 {tanggal} ⏰ {jam}\n"
                f"📍 {wilayah}\n"
                f"💥 Magnitudo: *M{mag}*\n"
                f"📏 Kedalaman: {kedalaman}\n"
                f"📐 Jarak dari Jogja: *{dist:.0f} km*\n"
                f"⚠️ {potensi}\n"
            )
            if dirasakan:
                msg += f"🔔 Dirasakan: {dirasakan}\n"
            if shakemap:
                msg += f"\n🗺️ Shakemap: https://data.bmkg.go.id/DataMKG/TEWS/{shakemap}"
            print(msg)
            return
        
        if mag >= 5.0 and dist <= 500:
            seen["seen"].append(event_id)
            seen["seen"] = seen["seen"][-100:]
            save_seen(seen)
            
            msg = (
                f"⚠️ *GEMPA BESAR TERDEKAT* ⚠️\n\n"
                f"📅 {tanggal} ⏰ {jam}\n"
                f"📍 {wilayah}\n"
                f"💥 Magnitudo: *M{mag}*\n"
                f"📏 Kedalaman: {kedalaman}\n"
                f"📐 Jarak dari Jogja: *{dist:.0f} km*\n"
                f"⚠️ {potensi}\n"
            )
            if dirasakan:
                msg += f"🔔 Dirasakan: {dirasakan}\n"
            print(msg)
            return
        
        # Gempa di luar radius atau terlalu kecil — simpan ID saja, diam
        seen["seen"].append(event_id)
        seen["seen"] = seen["seen"][-100:]
        save_seen(seen)
        
    except Exception as e:
        print(f"⚠️ Monitor gempa error: {e}")

if __name__ == "__main__":
    check_earthquake()
