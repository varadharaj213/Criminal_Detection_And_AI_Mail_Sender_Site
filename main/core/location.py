import requests
import json

def get_location_details(latitude, longitude):
    """Get accurate location details using multiple APIs"""
    if not latitude or not longitude:
        return {
            'latitude': None,
            'longitude': None,
            'city': 'Unknown',
            'pincode': 'Unknown',
            'address': 'Location not available'
        }
    
    # Try multiple APIs for better accuracy
    location_data = try_all_location_apis(latitude, longitude)
    
    if location_data:
        return location_data
    
    # Fallback
    return {
        'latitude': latitude,
        'longitude': longitude,
        'city': 'Unknown',
        'pincode': 'Unknown',
        'address': f'Coordinates: {latitude:.6f}, {longitude:.6f}'
    }

def try_all_location_apis(lat, lon):
    """Try multiple location APIs for accurate results"""
    results = []
    
    # 1. Try BigDataCloud API (very accurate)
    try:
        result = get_location_from_bigdatacloud(lat, lon)
        if result and result.get('city') != 'Unknown':
            return result
        results.append(result)
    except:
        pass
    
    # 2. Try PositionStack API
    try:
        result = get_location_from_positionstack(lat, lon)
        if result and result.get('city') != 'Unknown':
            return result
        results.append(result)
    except:
        pass
    
    # 3. Try OpenStreetMap (fallback)
    try:
        result = get_location_from_osm(lat, lon)
        if result and result.get('city') != 'Unknown':
            return result
        results.append(result)
    except:
        pass
    
    # Return the first valid result
    for result in results:
        if result and result.get('city') != 'Unknown':
            return result
    
    return None

def get_location_from_bigdatacloud(lat, lon):
    """Get location from BigDataCloud API (free tier, accurate)"""
    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client"
        params = {
            'latitude': lat,
            'longitude': lon,
            'localityLanguage': 'en'
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            city = data.get('city', 'Unknown')
            locality = data.get('locality', '')
            
            # Use locality if city is not available
            if city == 'Unknown' and locality:
                city = locality
            
            return {
                'latitude': lat,
                'longitude': lon,
                'city': city,
                'pincode': data.get('postcode', 'Unknown'),
                'address': data.get('localityInfo', {}).get('informative', [{}])[0].get('name', ''),
                'source': 'BigDataCloud'
            }
    except:
        pass
    
    return None

def get_location_from_positionstack(lat, lon):
    """Get location from PositionStack API (requires free API key)"""
    try:
        # Get free API key from https://positionstack.com/
        api_key = "YOUR_FREE_API_KEY_HERE"  # Register for free at positionstack.com
        
        url = f"http://api.positionstack.com/v1/reverse"
        params = {
            'access_key': api_key,
            'query': f"{lat},{lon}",
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                location = data['data'][0]
                
                return {
                    'latitude': lat,
                    'longitude': lon,
                    'city': location.get('locality') or location.get('county') or 'Unknown',
                    'pincode': location.get('postal_code', 'Unknown'),
                    'address': location.get('label', ''),
                    'source': 'PositionStack'
                }
    except:
        pass
    
    return None

def get_location_from_osm(lat, lon):
    """Get location from OpenStreetMap"""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'zoom': 18,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'CriminalDetectionSystem/1.0 (contact@example.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            # Try multiple city fields
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('municipality') or 
                   address.get('county') or 
                   address.get('state_district') or 
                   'Unknown')
            
            return {
                'latitude': lat,
                'longitude': lon,
                'city': city,
                'pincode': address.get('postcode', 'Unknown'),
                'address': data.get('display_name', f'Lat: {lat}, Lon: {lon}'),
                'raw_address': address,
                'source': 'OpenStreetMap'
            }
    except Exception as e:
        print(f"OSM API error: {e}")
    
    return None

def get_ip_based_location():
    """Get approximate location from IP address"""
    try:
        # Try ipapi first
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'city': data.get('city'),
                'pincode': data.get('postal'),
                'address': f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country_name', '')}",
                'source': 'ipapi'
            }
    except:
        pass
    
    # Fallback to ipinfo
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            loc = data.get('loc', '').split(',')
            if len(loc) == 2:
                return {
                    'latitude': float(loc[0]),
                    'longitude': float(loc[1]),
                    'city': data.get('city', 'Unknown'),
                    'pincode': data.get('postal', 'Unknown'),
                    'address': data.get('city', ''),
                    'source': 'ipinfo'
                }
    except:
        pass
    
    return None

# Quick test function
def test_location():
    """Test function to verify location accuracy"""
    # Vellore coordinates (approximate)
    vellore_coords = (12.9165, 79.1325)
    result = get_location_details(vellore_coords[0], vellore_coords[1])
    print("Location test for Vellore:")
    print(f"City: {result.get('city')}")
    print(f"Pincode: {result.get('pincode')}")
    print(f"Address: {result.get('address')}")
    print(f"Source: {result.get('source', 'Unknown')}")
    return result