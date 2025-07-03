# Flask Astroloji API

Swiss Ephemeris kullanarak doğum haritası hesaplayan Flask API. React frontend ile entegre edilmek üzere tasarlanmıştır.

## Özellikler

- Gezegen pozisyonları (Güneş, Ay, Merkür, Venüs, Mars, Jüpiter, Satürn)
- Ev cusps (Placidus sistemi)
- Önemli noktalar (ASC, MC, DSC, IC)
- Gezegen evleri
- Retrograde durumu
- Tropikal zodyak
- Otomatik timezone hesaplaması

## Kurulum

1. Gereksinimleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Swiss Ephemeris dosyalarını indirin:
```bash
# Swiss Ephemeris dosyaları gerekli (.se1 dosyaları)
# https://www.astro.com/ftp/swisseph/ephe/ adresinden indirin
```

3. API'yi çalıştırın:
```bash
python app.py
```

## API Kullanımı

### Doğum Haritası Hesaplama

**POST** `/natal`

**Request Body:**
```json
{
  "date": "YYYY-MM-DD",
  "time": "HH:MM", 
  "place": "Şehir, Ülke"
}
```

**Response:**
```json
{
  "planets": {
    "Sun": {
      "sign": "Burç Adı",
      "degree": "Derece dakika",
      "house": 1,
      "retrograde": false
    }
  },
  "houses": {
    "House 1": {
      "sign": "Burç Adı", 
      "degree": "Derece dakika"
    }
  },
  "points": {
    "Asc": {
      "sign": "Burç Adı",
      "degree": "Derece dakika"
    }
  }
}
```

## React Entegrasyonu

React uygulamasından API'ye istek gönderme örneği:

```javascript
const calculateNatalChart = async (birthData) => {
  try {
    const response = await fetch('http://localhost:5000/natal', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        date: birthData.date,
        time: birthData.time,
        place: birthData.place
      })
    });
    
    const chartData = await response.json();
    return chartData;
  } catch (error) {
    console.error('API Error:', error);
  }
};
```

## Production Deployment

Gunicorn ile:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

## Teknik Detaylar

- **Ev Sistemi**: Placidus
- **Zodyak**: Tropikal
- **Timezone**: Otomatik hesaplama (DST kuralları dahil)
- **Ephemeris**: Swiss Ephemeris (DE431)
- **Koordinatlar**: OpenCage Geocoding API

## CORS Ayarları

React frontend ile entegrasyon için CORS ayarları gerekebilir:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
```

## Hata Yönetimi

API aşağıdaki hata durumlarını döndürür:
- `400`: Eksik veya yanlış format
- `500`: Sunucu hatası

## Güvenlik

- API key'ler environment variable olarak saklanmalı
- Production'da HTTPS kullanılmalı
- Rate limiting uygulanmalı 