# project-showcase
implementation of a pre-trained image labelling machine learning model using tensorflow/pytorch frameworks (ResNet50, EfficientNet, VGG16) for use in the project showcase thing
## todo:
rough outline very abstract for now
1. gather sufficient amount of training data (eg. 5 products, about 50 images each, photos taken from various angles, lighting conditions, etc.)
2. find an appropriate model (those mentioned above) OR just use traditional computer vision machine learning approaches:
   - feature extraction implementations eg. SIFT, ORB
   - basic image classifiers eg. support vector machines, nearest neighbors
   - this would probably be better for smaller datasets
3. extract features --> pipeline to training --> get model ready for predictions
#### Post Training
1. set up networking communication interface w/ hardware processor on the prototype device itself and the machine hosting the classification model
     - obviously going to be space constraints on the hardware so model should be hosted on either a virtual server or someone's desktop machine (that won't go down)
2. handle incoming image information and feed into the model for predictions
3. compile predictions and align them appropriately with internal dataset information
   - price of item
   - brand name
   - nutrition information possible
   - others...
4. send relevant information back to sender

