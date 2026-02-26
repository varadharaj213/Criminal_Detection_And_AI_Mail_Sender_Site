from django.shortcuts import render, HttpResponse, redirect
from .models import *
from .forms import *
import face_recognition
import cv2
import numpy as np
from django.db.models import Q
import os
import json
import time
from datetime import datetime
import threading

from .mail import send_criminal_alert_email, send_audio_alert_email
from .location import get_location_details
from .audio_detection import AudioDetector

# Global variables
last_face = 'no_face'
current_path = os.path.dirname(__file__)
face_list_file = os.path.join(current_path, 'face_list.txt')

# Audio detection variables
audio_detector = AudioDetector()
audio_detection_active = False
audio_stop_event = None
audio_detection_thread = None

def home(request):
    scanned = LastFace.objects.all().order_by('date').reverse()
    context = {'scanned': scanned}
    return render(request, 'core/home.html', context)

def ajax(request):
    last_face = LastFace.objects.last()
    context = {'last_face': last_face}
    return render(request, 'core/ajax.html', context)

def scan(request):
    global last_face
    found_face_encodings = []
    found_face_names = []

    profiles = Profile.objects.all()
    for profile in profiles:
        person = profile.image
        image_of_person = face_recognition.load_image_file(f'media/{person}')
        person_face_encoding = face_recognition.face_encodings(image_of_person)[0]
        found_face_encodings.append(person_face_encoding)
        found_face_names.append(f'{person}'[:-4])

    video_capture = cv2.VideoCapture(0)

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(found_face_encodings, face_encoding)
                name = "Criminal not found in records"

                face_distances = face_recognition.face_distance(found_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = found_face_names[best_match_index]
                    profile = Profile.objects.get(Q(image__icontains=name))

                    location_data = None
                    if 'detection_location' in request.session:
                        loc = request.session.get('detection_location')
                        if loc and 'latitude' in loc and 'longitude' in loc:
                            location_data = get_location_details(loc['latitude'], loc['longitude'])

                    # Get current timestamp for both email and database
                    current_time = datetime.now()
                    
                    # Send email with the same timestamp
                    send_criminal_alert_email("varadharaj1410@gmail.com", profile, location_data, current_time)

                    if profile.present == True:
                        pass
                    else:
                        profile.present = True
                        profile.save()

                    if last_face != name:
                        # Create LastFace object with explicit timestamp
                        last_face_obj = LastFace(
                            last_face=name,
                            date=current_time  # Use the same timestamp as email
                        )
                        
                        if location_data:
                            try:
                                last_face_obj.latitude = float(location_data.get('latitude', 0))
                                last_face_obj.longitude = float(location_data.get('longitude', 0))
                            except:
                                pass
                            last_face_obj.city = location_data.get('city', 'Unknown')[:200]
                            last_face_obj.pincode = str(location_data.get('pincode', 'Unknown'))[:20]
                            last_face_obj.address = location_data.get('address', '')[:500]
                        
                        last_face_obj.save()
                        last_face = name

                face_names.append(name)

        process_this_frame = not process_this_frame

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

        cv2.imshow('Face detection - Press q to shut camera', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return HttpResponse('scanner closed', last_face)

def save_location(request):
    """Save current location to session"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lon = data.get('longitude')
            
            if lat and lon:
                request.session['detection_location'] = {
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'timestamp': time.time()
                }
                return HttpResponse('Location saved successfully')
        except Exception as e:
            print(f"Error saving location: {e}")
    
    return HttpResponse('Invalid location data', status=400)

def profiles(request):
    profiles = Profile.objects.all()
    context = {'profiles': profiles}
    return render(request, 'core/profiles.html', context)

def details(request):
    try:
        last_face = LastFace.objects.last()
        profile = Profile.objects.get(Q(image__icontains=last_face))
    except:
        last_face = None
        profile = None

    context = {
        'profile': profile,
        'last_face': last_face
    }
    return render(request, 'core/details.html', context)

def add_profile(request):
    form = ProfileForm
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('profiles')
    context = {'form': form}
    return render(request, 'core/add_profile.html', context)

def edit_profile(request, id):
    profile = Profile.objects.get(id=id)
    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profiles')
    context = {'form': form}
    return render(request, 'core/add_profile.html', context)

def delete_profile(request, id):
    profile = Profile.objects.get(id=id)
    profile.delete()
    return redirect('profiles')

def clear_history(request):
    history = LastFace.objects.all()
    history.delete()
    return redirect('home')

# ============================================
# AUDIO DETECTION FUNCTIONS
# ============================================

def audio_detection(request):
    """Start audio detection system"""
    global audio_detection_active, audio_stop_event, audio_detection_thread
    
    if not audio_detection_active:
        audio_detection_active = True
        audio_stop_event = threading.Event()
        
        # Start audio detection in separate thread
        audio_detection_thread = threading.Thread(
            target=run_audio_detection,
            args=(request, audio_stop_event)
        )
        audio_detection_thread.daemon = True
        audio_detection_thread.start()
        
        return HttpResponse('Audio detection started successfully')
    else:
        return HttpResponse('Audio detection is already active')

def run_audio_detection(request, stop_event):
    """Run audio detection in a separate thread"""
    print("🔊 Starting audio detection system...")
    
    def audio_callback(detected_text, alert_info):
        """Callback function to handle detected audio alerts"""
        try:
            # Get location from session
            location_data = None
            if 'detection_location' in request.session:
                loc = request.session.get('detection_location')
                if loc and 'latitude' in loc and 'longitude' in loc:
                    location_data = get_location_details(loc['latitude'], loc['longitude'])
            
            # Create AudioAlert record
            audio_alert = AudioAlert(
                detected_text=detected_text,
                alert_type=alert_info['type'],
                confidence=alert_info['confidence'],
                date=datetime.now()
            )
            
            # Add location data if available
            if location_data:
                try:
                    audio_alert.latitude = float(location_data.get('latitude', 0))
                    audio_alert.longitude = float(location_data.get('longitude', 0))
                except:
                    pass
                audio_alert.city = location_data.get('city', 'Unknown')[:200]
                audio_alert.pincode = str(location_data.get('pincode', 'Unknown'))[:20]
                audio_alert.address = location_data.get('address', '')[:500]
            
            audio_alert.save()
            
            # Send email alert
            send_audio_alert_email(
                "varadharaj1410@gmail.com",
                detected_text,
                alert_info['type'],
                location_data,
                datetime.now()
            )
            
            print(f"✅ Audio alert saved and email sent: {detected_text}")
            
        except Exception as e:
            print(f"❌ Error handling audio alert: {e}")
    
    # Run continuous audio detection
    audio_detector.continuous_detection(callback=audio_callback, stop_event=stop_event)
    
    print("🔊 Audio detection stopped")

def stop_audio_detection(request):
    """Stop audio detection system"""
    global audio_detection_active, audio_stop_event
    
    if audio_detection_active and audio_stop_event:
        audio_stop_event.set()
        audio_detection_active = False
        
        # Wait for thread to finish
        if audio_detection_thread and audio_detection_thread.is_alive():
            audio_detection_thread.join(timeout=2)
        
        return HttpResponse('Audio detection stopped successfully')
    else:
        return HttpResponse('Audio detection is not active')

def audio_alerts(request):
    """View all audio alerts"""
    alerts = AudioAlert.objects.all().order_by('-date')
    
    # Get stats
    total_alerts = alerts.count()
    help_alerts = alerts.filter(alert_type='help').count()
    save_alerts = alerts.filter(alert_type='save').count()
    emergency_alerts = alerts.filter(alert_type='emergency').count()
    
    # Check if audio detection is active
    global audio_detection_active
    
    context = {
        'alerts': alerts,
        'total_alerts': total_alerts,
        'help_alerts': help_alerts,
        'save_alerts': save_alerts,
        'emergency_alerts': emergency_alerts,
        'audio_detection_active': audio_detection_active
    }
    return render(request, 'core/audio_alerts.html', context)

def clear_audio_alerts(request):
    """Clear all audio alerts"""
    AudioAlert.objects.all().delete()
    return redirect('audio_alerts')

def mark_alert_verified(request, id):
    """Mark an audio alert as verified"""
    try:
        alert = AudioAlert.objects.get(id=id)
        alert.is_verified = True
        alert.save()
        return redirect('audio_alerts')
    except AudioAlert.DoesNotExist:
        return redirect('audio_alerts')

def mark_alert_action_taken(request, id):
    """Mark an audio alert as action taken"""
    try:
        alert = AudioAlert.objects.get(id=id)
        alert.action_taken = True
        alert.save()
        return redirect('audio_alerts')
    except AudioAlert.DoesNotExist:
        return redirect('audio_alerts')

def delete_audio_alert(request, id):
    """Delete a specific audio alert"""
    try:
        alert = AudioAlert.objects.get(id=id)
        alert.delete()
        return redirect('audio_alerts')
    except AudioAlert.DoesNotExist:
        return redirect('audio_alerts')

def get_audio_detection_status(request):
    """Get current audio detection status (for AJAX)"""
    global audio_detection_active
    return JsonResponse({
        'active': audio_detection_active,
        'status': 'listening' if audio_detection_active else 'stopped'
    })

def quick_audio_test(request):
    """Quick test function for audio detection"""
    try:
        # Record 5 seconds of audio
        print("🎤 Recording test audio...")
        audio = audio_detector.record_audio(duration=5)
        
        # Try to recognize
        try:
            text = audio_detector.recognizer.recognize_google(audio)
            print(f"📝 Test detected: {text}")
            
            # Check for alerts
            alerts = audio_detector.detect_alert_phrases(text)
            
            if alerts:
                return HttpResponse(f"✅ Test successful! Detected alert: '{text}' - Type: {alerts[0]['type']}")
            else:
                return HttpResponse(f"✅ Test successful! Detected: '{text}' (No alert keywords)")
                
        except sr.UnknownValueError:
            return HttpResponse("❌ Test failed: Could not understand audio")
        except sr.RequestError as e:
            return HttpResponse(f"❌ Test failed: Speech recognition service error - {e}")
            
    except Exception as e:
        return HttpResponse(f"❌ Test failed: {str(e)}")

def audio_stats(request):
    """Get audio detection statistics"""
    # Daily stats
    today = datetime.now().date()
    today_alerts = AudioAlert.objects.filter(date__date=today).count()
    
    # Weekly stats
    week_ago = datetime.now().date() - timedelta(days=7)
    weekly_alerts = AudioAlert.objects.filter(date__date__gte=week_ago).count()
    
    # Alert type distribution
    alert_types = AudioAlert.objects.values('alert_type').annotate(count=Count('alert_type'))
    
    # Location stats
    alerts_with_location = AudioAlert.objects.exclude(city='Unknown').exclude(city__isnull=True).count()
    
    return JsonResponse({
        'today_alerts': today_alerts,
        'weekly_alerts': weekly_alerts,
        'alert_types': list(alert_types),
        'alerts_with_location': alerts_with_location,
        'total_alerts': AudioAlert.objects.count()
    })

# Add to imports if not already present
from django.http import JsonResponse
import speech_recognition as sr
from django.db.models import Count
from datetime import timedelta