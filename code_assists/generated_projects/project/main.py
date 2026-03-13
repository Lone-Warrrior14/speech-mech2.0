```python
import numpy as np
from tensorflow import keras
from cnn_model import model

# Use the trained model
model.load_weights('cnn_model_weights.h5')
loaded_model = keras.models.load_model('cnn_model.h5')
test_loss, test_acc = loaded_model.evaluate(np.random.rand(10000, 28, 28, 1), np.random.rand(10000, 10))
print('Loaded model test accuracy:', test_acc)
```