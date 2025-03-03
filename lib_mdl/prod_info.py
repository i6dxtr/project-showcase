import pyttsx3


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
    Given a product name, returns a natural language string
    describing the product with its total calories and price.
    
    Args:
        product_name (str): The name of the product.
        
    Returns:
        str: A descriptive string about the product information.
    """
    # Normalize input to lower-case to match keys in our dictionary.
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
    Uses pyttsx3 to convert text to speech.
    
    Args:
        text (str): The text to be spoken.
    """
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def announce_product(product_name: str):
    """
    Retrieves product information and announces it using TTS.
    
    Args:
        product_name (str): The name of the product.
    """
    info_text = get_product_info(product_name)
    print(info_text)
    speak_text(info_text)