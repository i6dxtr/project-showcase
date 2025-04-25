from gtts import gTTS
import os
from pygame import mixer
import time
from typing import Dict, Any

# Product information dictionary
products: Dict[str, Dict[str, Any]] = {
    "morton coarse kosher salt": {
        "calories": 0,
        "price": "$2.99"
    },
    "kroger creamy peanut butter": {
        "calories": 190,
        "price": "$3.49"
    },
    "great value twist and shout cookies": {
        "calories": 250,
        "price": "$1.99"
    },
    "great value cheddar cheese cracklers": {
        "calories": 210,
        "price": "$2.49"
    }
}

def get_product_info(product_name: str) -> str:
    """
    Retrieve product information based on the product name.
    """
    key = product_name.lower()
    
    if key in products:
        info = products[key]
        message = (f"Here is the information for {product_name.title()}: "
                   f"it contains {info['calories']} calories and is priced at {info['price']}.")
    else:
        message = (f"Sorry, we do not have information for the product '{product_name}'. "
                   "Please try another product name.")
    return message

def speak_text(text: str) -> None:
    """
    Convert text to speech using Google TTS and play immediately
    """
    temp_file = "temp_speech.mp3"
    try:
        # Generate speech file
        tts = gTTS(text=text, lang='en')
        
        # Remove existing file if it exists
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        # Save new speech file
        tts.save(temp_file)
        
        # Initialize and play audio
        mixer.init()
        mixer.music.load(temp_file)
        mixer.music.play()
        
        # Wait for audio to finish
        while mixer.music.get_busy():
            time.sleep(0.1)
            
        # Cleanup
        mixer.music.unload()
        mixer.quit()
        
        # Remove temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        # Fallback to pyttsx3
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

def announce_product(product_name: str):
    """
    Announce product information using text-to-speech.
    """
    info_text = get_product_info(product_name)
    print(info_text)
    speak_text(info_text)