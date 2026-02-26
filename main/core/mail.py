import os
from datetime import datetime
from langchain_community.agent_toolkits import GmailToolkit
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)

credentials = get_gmail_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/"],
    client_secrets_file="D:/Holmes_Criminal_Detection_Platform-main/core/cred.json",
)

api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)
tools = toolkit.get_tools()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key="YOURGROQAPIKEY"
)

agent_executor = create_react_agent(llm, tools)

def send_criminal_alert_email(officer_email, profile, location_data=None, timestamp=None):
    # Use provided timestamp or current time
    if timestamp:
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build location information for table
    if location_data:
        location_rows = f"""
        <tr><td><strong>📍 Detection Location</strong></td><td>{location_data.get('address', 'Unknown')}</td></tr>
        <tr><td><strong>🏙️ City</strong></td><td>{location_data.get('city', 'Unknown')}</td></tr>
        <tr><td><strong>🌐 Coordinates</strong></td><td>{location_data.get('latitude', 'N/A')}, {location_data.get('longitude', 'N/A')}</td></tr>
        """
        # Add Google Maps link if coordinates are available
        if location_data.get('latitude') and location_data.get('longitude'):
            location_rows += f"""
        <tr><td><strong>🗺️ Google Maps</strong></td><td><a href="https://www.google.com/maps/search/?api=1&query={location_data.get('latitude')},{location_data.get('longitude')}">View on Google Maps</a></td></tr>
        """
    else:
        location_rows = """
        <tr><td><strong>📍 Location</strong></td><td>Not available (GPS access required)</td></tr>
        """

    query = f"""
    Compose and send an urgent HTML email to {officer_email} notifying that a criminal has been identified 
    by the facial recognition system. The email should use HTML formatting with tables for better readability.

    IMPORTANT: Use HTML table formatting with proper <table>, <tr>, and <td> tags.

    Email Subject: 🚨 CRIMINAL ALERT - IMMEDIATE ACTION REQUIRED

    Email Body HTML Content:
    <h2>🚨 CRIMINAL ALERT - IMMEDIATE ACTION REQUIRED 🚨</h2>
    
    <h3>🔍 Criminal Details:</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        <tr><td><strong>Full Name</strong></td><td>{profile.first_name} {profile.last_name}</td></tr>
        <tr><td><strong>Profile ID</strong></td><td>{profile.id}</td></tr>
        <tr><td><strong>Gender</strong></td><td>{profile.gender}</td></tr>
        <tr><td><strong>Age</strong></td><td>{profile.age}</td></tr>
        <tr><td><strong>Identification Mark</strong></td><td>{profile.identi}</td></tr>
        <tr><td><strong>Crimes</strong></td><td>{profile.crime}</td></tr>
        <tr><td><strong>Nationality</strong></td><td>{profile.nationality}</td></tr>
    </table>

    <h3>📍 Detection Information:</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        {location_rows}
        <tr><td><strong>⏰ Time of Detection</strong></td><td>{timestamp_str}</td></tr>
    </table>

    <h3>🛡️ Action Required:</h3>
    <ul>
        <li>Verify the criminal details in the database immediately</li>
        <li>Dispatch units to the detection location</li>
        <li>Coordinate with local law enforcement</li>
        <li>Maintain surveillance in the area</li>
    </ul>

    <p><strong>Note:</strong> This alert was generated automatically by the Holmes Criminal Detection Platform.</p>

    Use a professional, urgent, and concise tone. Set the email priority to HIGH.
    Ensure the email is sent automatically with high priority.
    """

    try:
        events = agent_executor.stream(
            {"messages": [("user", query)]},
            stream_mode="values",
        )
        for event in events:
            print(event["messages"][-1])
    except Exception as e:
        print("❌ Email sending failed:", e)

def send_audio_alert_email(officer_email, detected_text, alert_type, location_data=None, timestamp=None):
    """Send email for audio-based alerts"""
    if timestamp:
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Alert type mapping
    alert_titles = {
        'help': '🆘 HELP REQUEST DETECTED',
        'save': '🆘 RESCUE REQUEST DETECTED',
        'emergency': '🚨 EMERGENCY SITUATION',
        'danger': '⚠️ DANGER ALERT',
        'other': '🔊 AUDIO ALERT DETECTED'
    }
    
    title = alert_titles.get(alert_type, '🔊 AUDIO ALERT DETECTED')
    
    # Build location information
    if location_data:
        location_rows = f"""
        <tr><td><strong>📍 Location</strong></td><td>{location_data.get('address', 'Unknown')}</td></tr>
        <tr><td><strong>🏙️ City</strong></td><td>{location_data.get('city', 'Unknown')}</td></tr>
        <tr><td><strong>🌐 Coordinates</strong></td><td>{location_data.get('latitude', 'N/A')}, {location_data.get('longitude', 'N/A')}</td></tr>
        """
        if location_data.get('latitude') and location_data.get('longitude'):
            location_rows += f"""
        <tr><td><strong>🗺️ Google Maps</strong></td><td><a href="https://www.google.com/maps/search/?api=1&query={location_data.get('latitude')},{location_data.get('longitude')}">View on Google Maps</a></td></tr>
        """
    else:
        location_rows = """
        <tr><td><strong>📍 Location</strong></td><td>Not available (GPS access required)</td></tr>
        """
    
    query = f"""
    Compose and send an urgent HTML email to {officer_email} notifying that an audio alert has been detected.
    
    Email Subject: {title} - IMMEDIATE RESPONSE REQUIRED
    
    Email Body HTML Content:
    <h2>{title}</h2>
    
    <h3>🔊 Detected Audio Content:</h3>
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p style="font-size: 18px; font-weight: bold;">"{detected_text}"</p>
    </div>
    
    <h3>📊 Alert Details:</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        <tr><td><strong>Alert Type</strong></td><td>{alert_type.upper()}</td></tr>
        <tr><td><strong>⏰ Time of Detection</strong></td><td>{timestamp_str}</td></tr>
    </table>
    
    <h3>📍 Location Information:</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        {location_rows}
    </table>
    
    <h3>🛡️ Immediate Action Required:</h3>
    <ul>
        <li>Verify the location immediately</li>
        <li>Dispatch patrol units to the location</li>
        <li>Check for any ongoing incidents in the area</li>
        <li>Contact local authorities if needed</li>
        <li>Maintain audio surveillance in the area</li>
    </ul>
    
    <p><strong>Note:</strong> This alert was automatically generated by audio analysis system.</p>
    <p><strong>⚠️ IMPORTANT:</strong> This could indicate someone in distress requiring immediate assistance.</p>
    
    Use an urgent and professional tone. Set email priority to HIGHEST.
    """
    
    try:
        events = agent_executor.stream(
            {"messages": [("user", query)]},
            stream_mode="values",
        )
        for event in events:
            print(event["messages"][-1])
        return True
    except Exception as e:
        print("❌ Audio alert email sending failed:", e)
        return False