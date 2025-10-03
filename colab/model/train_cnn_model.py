import tensorflow as tf
import tensorflow_datasets as tfds
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report

# ==========================
# データロード
# ==========================
commands = ["go", "right", "left", "stop"]  # back 削除
dataset, info = tfds.load("speech_commands", with_info=True, as_supervised=True, split=["train", "test"])
train_ds, test_ds = dataset
sr = 16000
batch_size = 64

# ラベル名と整数の対応を取得
label_names = info.features['label'].names
target_label_indices = [label_names.index(w) for w in commands]

# ==========================
# データ前処理
# ==========================
def preprocess(audio, label):
    audio = tf.cast(audio, tf.float32) / tf.int16.max
    spectrogram = tf.signal.stft(audio, frame_length=128, frame_step=64)
    spectrogram = tf.abs(spectrogram)
    spectrogram = tf.expand_dims(spectrogram, -1)
    # 時間軸を固定 (128フレームにリサイズ)
    spectrogram = tf.image.resize(spectrogram, [128, spectrogram.shape[1]])
    return spectrogram, label

# 対象単語だけフィルタ
def filter_target(audio, label):
    return tf.reduce_any([tf.equal(label, idx) for idx in target_label_indices])

# ==========================
# データセット構築
# ==========================
train_ds = (train_ds
    .filter(filter_target)
    .take(2000)  # 確認用に絞る
    .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    .cache()
    .shuffle(1000)
    .batch(batch_size)
    .prefetch(tf.data.AUTOTUNE))

test_ds = (test_ds
    .filter(filter_target)
    .take(500)
    .map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    .batch(batch_size)
    .prefetch(tf.data.AUTOTUNE))

# ==========================
# 軽量CNNモデル
# ==========================
num_classes = len(commands)
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(128, None, 1)),  # 入力サイズ固定
    tf.keras.layers.Conv2D(8, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D((2,2)),
    tf.keras.layers.Conv2D(16, (3,3), activation='relu'),
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(num_classes, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# ==========================
# 学習
# ==========================
history = model.fit(train_ds, validation_data=test_ds, epochs=5)

# 学習曲線保存
plt.figure()
plt.plot(history.history['accuracy'], label="train_acc")
plt.plot(history.history['val_accuracy'], label="val_acc")
plt.legend()
plt.savefig("learning_curve.png")

# ==========================
# 評価
# ==========================
y_true, y_pred = [], []
for x, y in test_ds:
    preds = model.predict(x)
    y_true.extend(y.numpy())
    y_pred.extend(np.argmax(preds, axis=1))

# classification_report 修正: labels を指定
labels = target_label_indices
print(classification_report(y_true, y_pred, labels=labels, target_names=commands))

# ==========================
# モデル保存
# ==========================
model.save("speech_cnn.h5")

# TFLite 変換
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
with open("speech_cnn.tflite", "wb") as f:
    f.write(tflite_model)

print("✅ 学習完了 & モデル保存完了")
