from gtts import gTTS
import os
from pygame import mixer
import time

# Product information dictionary
products = {
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

def speak_text(text: str):
    """
    Convert text to speech using Google TTS and play immediately
    """
    try:
        # Initialize pygame mixer
        mixer.init()
        
        # Generate and save the speech
        tts = gTTS(text=text, lang='en')
        tts.save("temp.mp3")
        
        # Load and play the audio
        mixer.music.load("temp.mp3")
        mixer.music.play()
        
        # Wait for the audio to finish
        while mixer.music.get_busy():
            time.sleep(0.1)
            
        # Clean up
        mixer.music.unload()
        mixer.quit()
        os.remove("temp.mp3")
        
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        # Fallback to pyttsx3 if gTTS fails
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