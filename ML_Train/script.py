
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os

# Load the dataset
Smart_Farming_Crop_Yield_2024 = pd.read_csv('C:\Users\saket.k.kohinkar\OneDrive - Accenture\Desktop\Development\New folder\Agent_2\uploads\Smart_Farming_Crop_Yield_2024.csv')

# Handle missing values
# Impute missing values for 'irrigation_type' with mode
irrigation_mode = Smart_Farming_Crop_Yield_2024['irrigation_type'].mode()[0]
Smart_Farming_Crop_Yield_2024['irrigation_type'].fillna(irrigation_mode, inplace=True)

# Drop rows with missing target 'crop_disease_status'
Smart_Farming_Crop_Yield_2024.dropna(subset=['crop_disease_status'], inplace=True)

# Drop irrelevant columns
columns_to_drop = ['farm_id', 'sensor_id', 'timestamp', 'sowing_date', 'harvest_date']
Smart_Farming_Crop_Yield_2024.drop(columns=columns_to_drop, inplace=True)

# Encode categorical variables
categorical_columns = ['region', 'crop_type', 'irrigation_type', 'fertilizer_type']
Smart_Farming_Crop_Yield_2024 = pd.get_dummies(Smart_Farming_Crop_Yield_2024, columns=categorical_columns, drop_first=True)

# Scale numerical features
numerical_columns = ['soil_moisture_%', 'soil_pH', 'temperature_C', 'rainfall_mm', 'humidity_%', 'sunlight_hours', 'pesticide_usage_ml', 'total_days', 'yield_kg_per_hectare', 'latitude', 'longitude', 'NDVI_index']
scaler = StandardScaler()
Smart_Farming_Crop_Yield_2024[numerical_columns] = scaler.fit_transform(Smart_Farming_Crop_Yield_2024[numerical_columns])

# Define the target column
target_column = 'crop_disease_status'

# Split the dataset into features and target
X = Smart_Farming_Crop_Yield_2024.drop(columns=[target_column])
y = Smart_Farming_Crop_Yield_2024[target_column]

# Split the data into training, validation, and test sets
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_validation, X_test, y_validation, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# Define the directory paths
train_dir = './data/train'
validation_dir = './data/validation'
test_dir = './data/test'

# Create directories if they do not exist
os.makedirs(train_dir, exist_ok=True)
os.makedirs(validation_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

# Save the datasets
X_train.to_csv(f'{train_dir}/input.csv', index=False)
y_train.to_csv(f'{train_dir}/label.csv', index=False)
X_validation.to_csv(f'{validation_dir}/input.csv', index=False)
y_validation.to_csv(f'{validation_dir}/label.csv', index=False)
X_test.to_csv(f'{test_dir}/input.csv', index=False)
y_test.to_csv(f'{test_dir}/label.csv', index=False)

print('Datasets saved successfully.')
