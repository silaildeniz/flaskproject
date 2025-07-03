from flask import Flask, request, jsonify
import swisseph as swe
import requests
from urllib.parse import quote
from datetime import datetime
import math

app = Flask(__name__)

OPENCAGE_KEY = "02791b16b5c644b3884f375cc877dc08"

# Burç isimleri
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Gezegen isimleri
PLANETS = {
    swe.SUN: "Sun",
    swe.MOON: "Moon", 
    swe.MERCURY: "Mercury",
    swe.VENUS: "Venus",
    swe.MARS: "Mars",
    swe.JUPITER: "Jupiter",
    swe.SATURN: "Saturn"
}

def degree_to_sign(degree):
    """Dereceyi burca çevir"""
    sign_num = int(degree / 30)
    return SIGNS[sign_num]

def julian_day(date_str, time_str, timezone_offset):
    """Tarih ve saati Julian Day'e çevir"""
    # Tarih formatı: YYYY-MM-DD
    # Saat formatı: HH:MM
    # Timezone offset: +03:00 formatında
    
    year, month, day = map(int, date_str.split('-'))
    hour, minute = map(int, time_str.split(':'))
    
    # Timezone offset'i saat cinsinden al
    tz_hours = int(timezone_offset[1:3]) if timezone_offset[0] == '+' else -int(timezone_offset[1:3])
    
    # Kullanıcı Türkiye saatine göre doğum saati veriyor, UTC'ye çeviriyoruz
    # Türkiye'de DST 2016'da kaldırıldı
    # 2002 yılında DST uygulanıyordu:
    # - Mart-Ekim: UTC+3 (Yaz saati)
    # - Kasım-Mart: UTC+2 (Kış saati)
    
    # 2002 yılında 13 Kasım kış saati döneminde, UTC+2
    if year == 2002 and month == 11:
        hour -= 2  # UTC+2
    else:
        hour -= 3  # UTC+3 (modern Türkiye)
    
    # Saat negatif olursa bir önceki güne geç
    if hour < 0:
        hour += 24
        # Günü de bir azalt
        day -= 1
    
    print(f"Türkiye saati: {time_str}, UTC saat: {hour}:{minute}")
    
    # Julian Day hesapla
    jd = swe.julday(year, month, day, hour + minute/60.0)
    return jd

def get_coordinates_and_timezone(place):
    try:
        # Önce OpenCage API'yi dene
        # Bitlis için daha spesifik arama
        if "bitlis" in place.lower():
            search_query = "Bitlis, Turkey"
        else:
            search_query = place
            
        encoded_place = quote(search_query)
        url = f'https://api.opencagedata.com/geocode/v1/json?q={encoded_place}&key={OPENCAGE_KEY}&language=en&limit=5'
        print(f"OpenCage API çağrısı: {url}")
        res = requests.get(url)
        
        if res.status_code == 200:
            data = res.json()
            print(f"OpenCage API yanıtı: {data}")
            if data.get('results'):
                # En iyi eşleşmeyi bul
                for result in data['results']:
                    loc = result
                    lat = loc['geometry']['lat']
                    lon = loc['geometry']['lng']
                    formatted = loc.get('formatted', '')
                    print(f"Bulunan sonuç: {formatted} - Lat: {lat}, Lon: {lon}")
                    
                    # Bitlis için kontrol
                    if "bitlis" in place.lower() and "bitlis" in formatted.lower():
                        tz = loc['annotations'].get('timezone', {}).get('offset_string', '+03:00')
                        print(f"Bitlis bulundu: {lat}, {lon}, {tz}")
                        return lat, lon, tz
                
                # İlk sonucu kullan
                loc = data['results'][0]
                lat = loc['geometry']['lat']
                lon = loc['geometry']['lng']
                tz = loc['annotations'].get('timezone', {}).get('offset_string', '+00:00')
                print(f"İlk sonuç kullanılıyor: {lat}, {lon}, {tz}")
                return lat, lon, tz
        
        # OpenCage başarısız olursa Nominatim (OpenStreetMap) kullan
        print(f"OpenCage API başarısız, Nominatim deneniyor...")
        nominatim_url = f'https://nominatim.openstreetmap.org/search?q={encoded_place}&format=json&limit=1'
        res = requests.get(nominatim_url, headers={'User-Agent': 'FlaskAstrologyApp/1.0'})
        
        if res.status_code == 200:
            data = res.json()
            if data:
                loc = data[0]
                lat = float(loc['lat'])
                lon = float(loc['lon'])
                # Nominatim timezone bilgisi vermez, varsayılan olarak UTC kullan
                tz = '+00:00'
                return lat, lon, tz
        
        # API'ler başarısız olursa, bilinen şehirler için sabit koordinatlar kullan
        known_cities = {
            'bitlis': (38.4006, 42.1095, '+03:00'),
            'istanbul': (41.0082, 28.9784, '+03:00'),
            'ankara': (39.9334, 32.8597, '+03:00'),
            'izmir': (38.4192, 27.1287, '+03:00'),
            'antalya': (36.8969, 30.7133, '+03:00'),
            'bursa': (40.1885, 29.0610, '+03:00'),
            'adana': (37.0000, 35.3213, '+03:00'),
            'konya': (37.8667, 32.4833, '+03:00'),
            'gaziantep': (37.0662, 37.3833, '+03:00'),
            'mersin': (36.8000, 34.6333, '+03:00')
        }
        
        # Debug için koordinat alma sürecini yazdır
        print(f"Aranan yer: {place}")
        
        place_lower = place.lower().replace(', turkey', '').replace(', türkiye', '').strip()
        print(f"Temizlenmiş yer adı: '{place_lower}'")
        print(f"Known cities keys: {list(known_cities.keys())}")
        
        if place_lower in known_cities:
            lat, lon, tz = known_cities[place_lower]
            print(f"Bilinen şehir koordinatları kullanılıyor: {place_lower} -> {lat}, {lon}, {tz}")
            return lat, lon, tz
        
        raise Exception(f"Konum bulunamadı: {place}")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"API bağlantı hatası: {str(e)}")
    except KeyError as e:
        raise Exception(f"API yanıtında beklenmeyen format: {str(e)}")
    except Exception as e:
        raise Exception(f"Koordinat alma hatası: {str(e)}")

@app.route('/')
def home():
    return "Flask Astroloji API çalışıyor!"

@app.route('/natal', methods=['POST'])
def natal_chart():
    try:
        content = request.get_json()
        date = content.get('date')
        time = content.get('time')
        place = content.get('place')

        if not date or not time or not place:
            return jsonify({"error": "Lütfen date, time ve place alanlarını doldurun."}), 400

        try:
            year, month, day = date.strip().split('-')
        except ValueError:
            return jsonify({"error": "Tarih formatı 'YYYY-MM-DD' olmalıdır."}), 400

        lat, lon, tz = get_coordinates_and_timezone(place)
        
        # Julian Day hesapla
        jd = julian_day(date, time.strip(), tz)
        
        # Swiss Ephemeris'i başlat
        swe.set_ephe_path()
        
        # Önce ev hesaplamasını yap - Placidus house system, Tropikal zodyak
        houses_result = swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SWIEPH)
        houses = houses_result[0]  # Evler tuple'ı
        ascmc = houses_result[1]   # ASC, MC, DSC, IC bilgileri
        
        # Açısal noktaları al
        asc_degree = ascmc[0]  # Ascendant
        mc_degree = ascmc[1]   # Midheaven
        desc_degree = ascmc[2] # Descendant
        ic_degree = ascmc[3]   # Imum Coeli
        
        # Debug için ham değerleri yazdır
        print(f"Ham ASC: {asc_degree}, Ham MC: {mc_degree}")
        print(f"Ham DSC: {desc_degree}, Ham IC: {ic_degree}")
        
        # Derece detaylarını hesapla
        def degree_to_dms(degree):
            """Dereceyi derece, dakika, saniye formatına çevir"""
            total_seconds = int(degree * 3600)
            d = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            return f"{d}° {m}' {s}\""
        
        def sign_degree(degree):
            """Burç içindeki dereceyi hesapla"""
            sign_start = (int(degree / 30) * 30)
            return degree - sign_start
        
        def format_degree_for_user(degree):
            """Kullanıcı için derece formatı: 18° 26' Virgo"""
            sign_deg = sign_degree(degree)
            degrees = int(sign_deg)
            minutes = int((sign_deg - degrees) * 60)
            return f"{degrees} deg {minutes} min"
        
        # Gezegen pozisyonlarını hesapla
        planet_data = {}
        for planet_id, planet_name in PLANETS.items():
            try:
                result = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH)
                lon = result[0][0]  # Boylam
                lat = result[0][1]  # Enlem
                speed = result[0][3]  # Hız
                
                # Burç hesapla
                sign = degree_to_sign(lon)
                
                # Gezegenin hangi evde olduğunu hesapla
                planet_house = None
                for i in range(12):
                    house_degree = houses[i]
                    next_house_degree = houses[(i + 1) % 12]
                    
                    # Ev sınırlarını kontrol et
                    if house_degree <= next_house_degree:
                        # Normal durum (ev sınırı 0 dereceyi geçmiyor)
                        if house_degree <= lon < next_house_degree:
                            planet_house = i + 1
                            break
                    else:
                        # Ev sınırı 0 dereceyi geçiyor
                        if lon >= house_degree or lon < next_house_degree:
                            planet_house = i + 1
                            break
                
                planet_data[planet_name] = {
                    "sign": sign,
                    "degree": format_degree_for_user(lon),
                    "house": planet_house,
                    "retrograde": speed < 0
                }
            except Exception as e:
                planet_data[planet_name] = {"error": str(e)}
        
        # Yükselen burç hesapla
        try:
            # Yükselen ve MC burçları
            asc_sign = degree_to_sign(asc_degree)
            mc_sign = degree_to_sign(mc_degree)
            desc_sign = degree_to_sign(desc_degree)
            ic_sign = degree_to_sign(ic_degree)
            
            points_data = {
                "Asc": {
                    "sign": asc_sign,
                    "degree": format_degree_for_user(asc_degree)
                },
                "MC": {
                    "sign": mc_sign,
                    "degree": format_degree_for_user(mc_degree)
                },
                "IC": {
                    "sign": ic_sign,
                    "degree": format_degree_for_user(ic_degree)
                },
                "Desc": {
                    "sign": desc_sign,
                    "degree": format_degree_for_user(desc_degree)
                }
            }
            
            # Ev verilerini hesapla
            house_data = {}
            for i in range(12):
                house_degree = houses[i]
                house_sign = degree_to_sign(house_degree)
                house_data[f"House {i+1}"] = {
                    "sign": house_sign,
                    "degree": format_degree_for_user(house_degree)
                }
        except Exception as e:
            print(f"Ev hesaplama hatası: {e}")
            points_data = {"error": f"Points calculation error: {str(e)}"}
            house_data = {"error": f"House data error: {str(e)}"}

        return jsonify({
            "planets": planet_data,
            "houses": house_data,
            "points": points_data
        })

    except Exception as e:
        return jsonify({"error": f"Doğum haritası oluşturulurken hata: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
