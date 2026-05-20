import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import os

def build_transfer_model(input_shape=(224, 224, 3), num_classes=4):
    """
    Builds a high-accuracy transfer learning model using MobileNetV2 
    pre-trained on ImageNet as the feature extractor.
    """
    # Load MobileNetV2 without the top classification layer
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=input_shape)
    
    # Freeze the base model layers initially
    base_model.trainable = False
    
    # Add custom classification head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.4)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    predictions = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model, base_model

if __name__ == '__main__':
    print("=" * 60)
    print("  Eye Disease Detection - Transfer Learning Training")
    print("  Using MobileNetV2 (ImageNet Pre-trained)")
    print("=" * 60)
    
    base_dir = r"c:\Users\yrake\.antigravity\eye_diagonisis\dataset\dataset"
    
    # Strong data augmentation for better generalization
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    val_datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2
    )
    
    print("\nLoading training data...")
    train_generator = train_datagen.flow_from_directory(
        base_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='training',
        shuffle=True
    )
    
    print("Loading validation data...")
    val_generator = val_datagen.flow_from_directory(
        base_dir,
        target_size=(224, 224),
        batch_size=32,
        class_mode='categorical',
        subset='validation',
        shuffle=False
    )
    
    print(f"\nClass indices: {train_generator.class_indices}")
    print(f"Training samples: {train_generator.samples}")
    print(f"Validation samples: {val_generator.samples}")
    
    model, base_model = build_transfer_model()
    
    # Callbacks for smarter training
    early_stop = EarlyStopping(
        monitor='val_accuracy', 
        patience=5, 
        restore_best_weights=True,
        verbose=1
    )
    
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss', 
        factor=0.5, 
        patience=3, 
        min_lr=1e-7,
        verbose=1
    )
    
    # Phase 1: Train only the classification head (base frozen)
    print("\n" + "=" * 60)
    print("  PHASE 1: Training Classification Head (Base Frozen)")
    print("=" * 60)
    
    model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=10,
        callbacks=[early_stop, reduce_lr]
    )
    
    # Phase 2: Fine-tune the last 30 layers of MobileNetV2
    print("\n" + "=" * 60)
    print("  PHASE 2: Fine-tuning Top Layers of MobileNetV2")
    print("=" * 60)
    
    base_model.trainable = True
    # Freeze everything except last 30 layers
    for layer in base_model.layers[:-30]:
        layer.trainable = False
    
    # Recompile with a much lower learning rate for fine-tuning
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=10,
        callbacks=[early_stop, reduce_lr]
    )
    
    # Evaluate final performance
    print("\n" + "=" * 60)
    print("  FINAL EVALUATION")
    print("=" * 60)
    loss, accuracy = model.evaluate(val_generator)
    print(f"\n  Validation Accuracy: {accuracy*100:.2f}%")
    print(f"  Validation Loss: {loss:.4f}")
    
    # Save the model
    os.makedirs('model', exist_ok=True)
    model.save('model/eye_disease_cnn.keras')
    print(f"\n  Model saved to model/eye_disease_cnn.keras")
    print("  Training Complete! The AI is now ready to use.")
