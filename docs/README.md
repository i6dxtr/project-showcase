# project-showcase
implementation of a pre-trained image labelling machine learning model using tensorflow/pytorch frameworks (ResNet50, EfficientNet, VGG16) for use in the ~~project showcase thing~~ mucat competition
# general description
## Use Case:
- If a customer has no phone, the desk can provide a cheap loaner phone for this purpose. Customer walks into store and goes to customer service desk.
   - Case 1: Customer is far-sighted and may struggled to read the labels for a product
   - Case 2: Customer is non-native speaker and struggles with language barriers regarding interpreting details on products
- Customer finds item in store
- Takes picture using phone camera and upload to website
- User selects language
- Website outputs via website AND speaker what the object is
- Website gives user some potential prompts to ask about
   - Allergen information
   - Nutrition facts
   - Price
   - etc
- User selects prompt
- Website outputs via website OR speaker information
- Asks user if they want more information
- Repeat as needed

## Project information:
### Front end:
- Website using HTML, CSS, Bootstrap
   - Choose what language customer wants it in
   - Upload a picture via camera of object
- Send image to backend
   - Classify image using customer database training images OR alternatively use text extraction and match to a brand name (could combine)
- Tell the user the product
- Give user prompts to ask about
   - Allergen Information
   - Nutrition Facts
   - Price
- User selects prompt
   - Vanna AI handles this
- Route Vanna AI output to website AND speaker (using TTS)
- Profit
