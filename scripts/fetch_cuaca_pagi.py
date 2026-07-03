#!/usr/bin/env python3
"""
Fetch cuaca Yogyakarta setiap pagi dan catat ke Excel.
Data dari Open-Meteo API (free, no key needed).
"""
import urllib.request
import json
import openpyxl
from datetime import datetime
import os
import sys

# Telegram config via env
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram(message):
    """Kirim notifikasi ke Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured, output to stdout:", file=sys.stderr)
        print(message)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'),
                                      headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram error: {e}", file=sys.stderr)
        return False

API_URL = "https://api.open-meteo.com/v1/forecast?latitude=-7.7956&longitude=110.3695&current=temperature_2m,relative_humidity_2m,rain,weather_code,wind_speed_10m,apparent_temperature&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=Asia/Jakarta"

EXCEL_PATH = os.path.expanduser("~/sembako/data/cuaca_yogyakarta.xlsx")

# Weather code descriptions (WMO codes)
WEATHER_CODES = {
    0: "Cerah", 1: "Cerah", 2: "Cerah Sebagian", 3: "Mendung",
    45: "Kabut", 48: "Kabut Dingin",
    51: "Gerimis Ringan", 53: "Gerimis Sedang", 55: "Gerimis Lebat",
    61: "Hujan Ringan", 63: "Hujan Sedang", 65: "Hujan Lebat",
    71: "Salju Ringan", 73: "Salju Sedang", 75: "Salju Lebat",
    80: "Hujan Lebat", 81: "Hujan Sangat Lebat", 82: "Hujan Ekstrem",
    85: "Salju Lebat", 86: "Salju Ekstrem",
    95: "Badai Guntur", 96: "Badai Guntur Ringan", 99: "Badai Guntur Lebat"
}

def fetch_weather():
    """Fetch cuaca dari Open-Meteo."""
    try:
        with urllib.request.urlopen(API_URL, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

def get_weather_description(code):
    """Get weather description dari WMO code."""
    return WEATHER_CODES.get(code, f"Code {code}")

def add_to_excel(weather_data):
    """Add weather data to Excel."""
    if not weather_data:
        return False
    
    try:
        # Load existing workbook
        if os.path.exists(EXCEL_PATH):
            wb = openpyxl.load_workbook(EXCEL_PATH)
            ws = wb.active
        else:
            # Create new workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Cuaca"
            headers = ["Tanggal", "Jam", "Suhu Sekarang", "Terasa", "Kelembapan", 
                      "Hujan", "Kecepatan Angin", "Kondisi", "Suhu Max", "Suhu Min", 
                      "Hujan Harian", "Kondisi Harian"]
            ws.append(headers)
        
        current = weather_data.get('current', {})
        daily = weather_data.get('daily', {})
        
        now = datetime.now()
        tanggal = now.strftime('%Y-%m-%d')
        jam = now.strftime('%H:%M')
        
        # Get today's daily forecast
        today_idx = 0 if daily.get('time') and daily['time'][0] == tanggal else -1
        
        row = [
            tanggal,
            jam,
            current.get('temperature_2m', '-'),
            current.get('apparent_temperature', '-'),
            current.get('relative_humidity_2m', '-'),
            current.get('rain', 0),
            current.get('wind_speed_10m', '-'),
            get_weather_description(current.get('weather_code', 0)),
            daily['temperature_2m_max'][today_idx] if daily.get('temperature_2m_max') else '-',
            daily['temperature_2m_min'][today_idx] if daily.get('temperature_2m_min') else '-',
            daily['precipitation_sum'][today_idx] if daily.get('precipitation_sum') else '-',
            get_weather_description(daily['weather_code'][today_idx]) if daily.get('weather_code') else '-'
        ]
        
        ws.append(row)
        wb.save(EXCEL_PATH)
        return True
    except Exception as e:
        print(f"Error writing to Excel: {e}")
        return False

def format_report(weather_data):
    """Format weather report untuk kirim."""
    if not weather_data:
        return "❌ Gagal fetch cuaca"
    
    current = weather_data.get('current', {})
    daily = weather_data.get('daily', {})
    
    now = datetime.now()
    tanggal = now.strftime('%A, %d %B %Y')
    
    # Get today's daily forecast
    today_idx = 0
    
    msg = f"🌤️ **CUACA YOGYAKARTA**\n"
    msg += f"📅 {tanggal}\n\n"
    
    msg += f"**📍 Kondisi Sekarang:**\n"
    msg += f"🌡️ Suhu: {current.get('temperature_2m', '-')}°C (terasa {current.get('apparent_temperature', '-')}°C)\n"
    msg += f"💧 Kelembapan: {current.get('relative_humidity_2m', '-')}%\n"
    msg += f"🌧️ Hujan: {current.get('rain', 0)} mm\n"
    msg += f"💨 Angin: {current.get('wind_speed_10m', '-')} km/h\n"
    msg += f"☁️ Kondisi: {get_weather_description(current.get('weather_code', 0))}\n\n"
    
    msg += f"**📊 Prakiraan Hari Ini:**\n"
    msg += f"🔺 Tertinggi: {daily['temperature_2m_max'][today_idx]}°C\n"
    msg += f"🔻 Terendah: {daily['temperature_2m_min'][today_idx]}°C\n"
    msg += f"🌧️ Hujan: {daily['precipitation_sum'][today_idx]} mm\n"
    msg += f"☁️ Kondisi: {get_weather_description(daily['weather_code'][today_idx])}\n\n"
    
    msg += f"✅ Data dicatat di Excel: `cuaca_yogyakarta.xlsx`"
    
    return msg

def main():
    print("=" * 50)
    print("🌤️ FETCH CUACA YOGYAKARTA")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M WIB')}")
    print("=" * 50)
    
    weather = fetch_weather()
    if not weather:
        print("❌ Gagal fetch data cuaca")
        return
    
    if add_to_excel(weather):
        print("✅ Data cuaca disimpan ke Excel")
    else:
        print("❌ Gagal menyimpan ke Excel")
    
    report = format_report(weather)
    print(f"\n{report}")
    
    # Send to Telegram
    send_telegram(report)

if __name__ == "__main__":
    main()
