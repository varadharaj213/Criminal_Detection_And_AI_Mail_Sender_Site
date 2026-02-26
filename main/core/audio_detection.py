import speech_recognition as sr
import pyaudio
import numpy as np
import wave
import os
from datetime import datetime
import time
from scipy import signal
from langchain_groq import ChatGroq
import json
from typing import List, Dict, Any

class AudioDetector:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize Groq LLM for intelligent alert analysis
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",  # or use "mixtral-8x7b-32768" for faster response
            api_key="YOURGROQAPIKEY",
            temperature=0.1,  # Lower temperature for more consistent results
            max_tokens=150
        )
        
        # Basic keywords as fallback
        self.alert_keywords = [
            'help', 'save', 'emergency', 'danger', 
            'help me', 'save me', 'someone help', 
            'call police', 'dangerous', 'attack',
            'robbery', 'fire', 'accident', 'injured',
            'bleeding', 'stuck', 'trapped', 'danger'
        ]
        
    def ai_analyze_alert(self, text: str) -> Dict[str, Any]:
        """
        Use AI to intelligently analyze if the audio contains alert/distress signals
        Returns detailed analysis with confidence score
        """
        prompt = f"""
        Analyze the following spoken text for distress signals, emergencies, or dangerous situations.
        Text: "{text}"
        
        Respond in JSON format with these fields:
        {{
            "is_alert": boolean (true if any distress/emergency detected),
            "alert_type": string ("help", "emergency", "danger", "crime", "medical", "fire", "accident", "none"),
            "confidence": float (0.0 to 1.0),
            "keywords_found": list of strings,
            "urgency_level": integer (1-10, 10 being most urgent),
            "context": string (brief explanation of why this is/isn't an alert),
            "suggested_action": string (brief suggestion for response)
        }}
        
        Examples:
        - "help me someone is following me" → is_alert: true, alert_type: "danger", urgency: 9
        - "call the police there's been an accident" → is_alert: true, alert_type: "accident", urgency: 10
        - "I need help with my homework" → is_alert: false, alert_type: "none", urgency: 1
        - "there's a fire in the building" → is_alert: true, alert_type: "fire", urgency: 10
        
        Be conservative: only flag as alert if there's clear indication of distress or emergency.
        """
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract JSON from response
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].strip()
            else:
                json_str = response_text.strip()
            
            analysis = json.loads(json_str)
            return analysis
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            # Fallback to keyword detection
            return self.fallback_keyword_analysis(text)
    
    def fallback_keyword_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis using keyword matching when AI fails"""
        text_lower = text.lower()
        detected_keywords = []
        
        for keyword in self.alert_keywords:
            if keyword in text_lower:
                detected_keywords.append(keyword)
        
        is_alert = len(detected_keywords) > 0
        
        # Determine alert type based on keywords
        alert_type = "none"
        urgency = 1
        
        if is_alert:
            if any(kw in ['help', 'help me', 'someone help'] for kw in detected_keywords):
                alert_type = "help"
                urgency = 7
            elif any(kw in ['emergency', 'call police'] for kw in detected_keywords):
                alert_type = "emergency"
                urgency = 9
            elif any(kw in ['danger', 'dangerous', 'attack'] for kw in detected_keywords):
                alert_type = "danger"
                urgency = 8
            elif any(kw in ['fire'] for kw in detected_keywords):
                alert_type = "fire"
                urgency = 10
            elif any(kw in ['accident', 'injured', 'bleeding'] for kw in detected_keywords):
                alert_type = "medical"
                urgency = 9
            else:
                alert_type = "other"
                urgency = 6
        
        return {
            "is_alert": is_alert,
            "alert_type": alert_type,
            "confidence": 0.7 if is_alert else 0.1,
            "keywords_found": detected_keywords,
            "urgency_level": urgency,
            "context": "Keyword-based detection",
            "suggested_action": "Investigate further" if is_alert else "No action needed"
        }
    
    def detect_alert_phrases(self, text: str) -> List[Dict]:
        """Check if text contains alert keywords (AI-enhanced)"""
        # Use AI for intelligent analysis
        ai_analysis = self.ai_analyze_alert(text)
        
        if not ai_analysis.get("is_alert", False):
            return []
        
        # Convert AI analysis to alert format
        detected_alerts = [{
            'keyword': ', '.join(ai_analysis.get('keywords_found', [])),
            'type': ai_analysis.get('alert_type', 'unknown'),
            'confidence': ai_analysis.get('confidence', 0.5),
            'urgency': ai_analysis.get('urgency_level', 5),
            'context': ai_analysis.get('context', ''),
            'suggested_action': ai_analysis.get('suggested_action', ''),
            'ai_analyzed': True,
            'raw_text': text
        }]
        
        return detected_alerts
    
    def record_audio(self, duration=5):
        """Record audio for specified duration"""
        with self.microphone as source:
            print("🎤 Listening... (Speak now)")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
        return audio
    
    def continuous_detection(self, callback=None, stop_event=None, use_ai=True):
        """Continuously listen for alert phrases with AI enhancement"""
        print("🔊 Starting continuous audio detection...")
        if use_ai:
            print("🤖 AI-powered analysis enabled")
        else:
            print("🔤 Keyword-based analysis enabled")
        
        print("Speak phrases to trigger alerts")
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while not stop_event or not stop_event.is_set():
                try:
                    print("\n🎤 Listening... (Press Ctrl+C to stop)")
                    audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=5)
                    
                    try:
                        # Try Google Speech Recognition
                        text = self.recognizer.recognize_google(audio)
                        print(f"📝 Detected: {text}")
                        
                        # Check for alert phrases
                        alerts = self.detect_alert_phrases(text) if use_ai else self.detect_alert_phrases_fallback(text)
                        
                        if alerts:
                            alert = alerts[0]
                            print(f"\n{'='*50}")
                            print(f"🚨 ALERT DETECTED!")
                            print(f"Type: {alert['type'].upper()}")
                            print(f"Urgency: {alert['urgency']}/10")
                            print(f"Confidence: {alert['confidence']*100:.1f}%")
                            print(f"Text: {text}")
                            print(f"Context: {alert.get('context', 'N/A')}")
                            print(f"Suggested: {alert.get('suggested_action', 'N/A')}")
                            print(f"{'='*50}\n")
                            
                            if callback:
                                callback(text, alert)
                        else:
                            # Show analysis result even for non-alerts when AI is enabled
                            if use_ai:
                                ai_analysis = self.ai_analyze_alert(text)
                                print(f"✅ No alert - Confidence: {ai_analysis.get('confidence', 0)*100:.1f}%")
                        
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"⚠️ Speech recognition error: {e}")
                        # Try alternative recognition service
                        text = self.try_alternate_recognition(audio)
                        if text:
                            alerts = self.detect_alert_phrases(text)
                            if alerts and callback:
                                callback(text, alerts[0])
                        
                except sr.WaitTimeoutError:
                    continue
                except KeyboardInterrupt:
                    print("\n⏹️ Audio detection stopped by user")
                    break
    
    def detect_alert_phrases_fallback(self, text):
        """Fallback to simple keyword detection"""
        text_lower = text.lower()
        detected_alerts = []
        
        for keyword in self.alert_keywords:
            if keyword in text_lower:
                if keyword in ['help', 'help me', 'someone help']:
                    alert_type = 'help'
                elif keyword in ['save', 'save me']:
                    alert_type = 'save'
                elif keyword in ['emergency', 'call police']:
                    alert_type = 'emergency'
                elif keyword in ['danger', 'dangerous', 'attack']:
                    alert_type = 'danger'
                else:
                    alert_type = 'other'
                
                detected_alerts.append({
                    'keyword': keyword,
                    'type': alert_type,
                    'confidence': 0.8,
                    'urgency': 7,
                    'ai_analyzed': False
                })
                break  # Only report first keyword found
        
        return detected_alerts
    
    def try_alternate_recognition(self, audio):
        """Try alternate speech recognition services"""
        try:
            # Try using Sphinx (offline)
            text = self.recognizer.recognize_sphinx(audio)
            return text
        except:
            return None
    
    def save_audio_to_file(self, audio, filename):
        """Save audio data to WAV file"""
        with open(filename, 'wb') as f:
            f.write(audio.get_wav_data())
        return filename
    
    def analyze_audio_intensity(self, audio_data, sample_rate=16000):
        """Analyze audio intensity for stress detection"""
        # Convert audio to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        
        # Calculate RMS (Root Mean Square) for intensity
        rms = np.sqrt(np.mean(audio_np**2))
        
        # Detect high intensity (potential screaming/yelling)
        is_high_intensity = rms > 5000  # Adjust threshold as needed
        
        # Analyze frequency for stress indicators
        frequencies, psd = signal.welch(audio_np, sample_rate, nperseg=1024)
        
        # High frequency energy often indicates stress/screaming
        high_freq_energy = np.sum(psd[frequencies > 1000])
        total_energy = np.sum(psd)
        high_freq_ratio = high_freq_energy / total_energy if total_energy > 0 else 0
        
        is_stressed_voice = high_freq_ratio > 0.3 or is_high_intensity
        
        return {
            'intensity': rms,
            'is_high_intensity': is_high_intensity,
            'max_amplitude': np.max(np.abs(audio_np)),
            'is_stressed_voice': is_stressed_voice,
            'high_freq_ratio': high_freq_ratio,
            'stress_confidence': min(high_freq_ratio * 2, 1.0)  # Scale to 0-1
        }
    
    def combined_analysis(self, audio, text=None):
        """Perform combined audio and text analysis"""
        if text is None:
            try:
                text = self.recognizer.recognize_google(audio)
            except:
                text = ""
        
        # Text analysis
        text_analysis = self.ai_analyze_alert(text) if text else {"is_alert": False}
        
        # Audio intensity analysis
        audio_data = audio.get_wav_data()
        intensity_analysis = self.analyze_audio_intensity(audio_data)
        
        # Combined decision
        text_alert = text_analysis.get("is_alert", False)
        text_confidence = text_analysis.get("confidence", 0)
        text_urgency = text_analysis.get("urgency_level", 1)
        
        audio_alert = intensity_analysis.get("is_stressed_voice", False)
        audio_confidence = intensity_analysis.get("stress_confidence", 0)
        
        # Weighted decision
        combined_confidence = (text_confidence * 0.7 + audio_confidence * 0.3)
        combined_alert = text_alert or (audio_alert and audio_confidence > 0.7)
        
        return {
            "text_analysis": text_analysis,
            "audio_analysis": intensity_analysis,
            "combined_alert": combined_alert,
            "combined_confidence": combined_confidence,
            "recommended_action": "INVESTIGATE" if combined_alert else "MONITOR",
            "timestamp": datetime.now().isoformat()
        }


# Example usage function
def test_audio_detection():
    """Test the enhanced audio detection system"""
    detector = AudioDetector()
    
    def alert_callback(text, alert):
        print(f"\n🚨 ALERT CALLBACK TRIGGERED!")
        print(f"Text: {text}")
        print(f"Alert Type: {alert['type']}")
        print(f"Urgency: {alert.get('urgency', 'N/A')}")
        print(f"AI Analyzed: {alert.get('ai_analyzed', False)}")
        
        # Here you would call your email sending function
        # from mail import send_audio_alert_email
        # send_audio_alert_email("officer@example.com", text, alert['type'])
    
    print("Testing AI-powered audio detection...")
    print("Try saying phrases like:")
    print("  - 'Help me, I'm in trouble'")
    print("  - 'Call the police, there's been an accident'")
    print("  - 'I need help with my homework' (should NOT trigger)")
    print("  - 'There's a fire in the building!'")
    
    # Start continuous detection with AI
    detector.continuous_detection(callback=alert_callback, use_ai=True)


if __name__ == "__main__":
    test_audio_detection()