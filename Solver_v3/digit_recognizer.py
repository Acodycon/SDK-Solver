import os
import numpy as np
import tensorflow as tf
from PIL import Image

image_dir = "D:\\Coding\\SudokuSolver\\SudokuSolver\\Training_Data"
image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir)]

labels = np.array([int(os.path.basename(f)[0]) for f in image_files])
labels = labels.astype(int)
print(f"image: {image_files[1]}")
image_files = [np.array(Image.open(path)) for path in image_files]
images = np.expand_dims(np.array(image_files), -1)
# images = images.astype(float)

model = tf.keras.models.Sequential([
    tf.keras.layers.Flatten(input_shape=(28, 28, 1)),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dense(10, activation="softmax")
])

model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

model.fit(images, labels, epochs=100)

model.save("recog_model.keras")
