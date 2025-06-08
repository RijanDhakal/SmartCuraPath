# disease_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

class DiseasePredictor:
    def __init__(self):
        # Initialize paths to data files (adjust as needed)
        self.data_dir = "data"
        self.model_path = os.path.join(self.data_dir, "disease_model.pkl")
        self.symptoms_path = os.path.join(self.data_dir, "training_data.csv")
        self.precautions_path = os.path.join(self.data_dir, "precautions_df.csv")
        self.description_path = os.path.join(self.data_dir, "description.csv")
        self.diet_path = os.path.join(self.data_dir, "diets.csv")
        self.workout_path = os.path.join(self.data_dir, "workout_df.csv")
        self.medicine_path = os.path.join(self.data_dir, "medications.csv")
        
        # Initialize data structures
        self.model = None
        self.symptom_dict = {}
        self.disease_info = {}
        self.load_data()
        
    def load_data(self):
        """Load all required data and train model if needed"""
        # Load symptom data
        df = pd.read_csv(self.symptoms_path)
        
        # Create symptom dictionary
        symptoms = df.drop(['disease'], axis=1)
        self.symptom_dict = {symptom: idx for idx, symptom in enumerate(symptoms.columns)}
        
        # Create disease dictionary
        self.disease_dict = {disease: idx for idx, disease in enumerate(df['disease'].unique())}
        
        # Load or train model
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.train_model(df)
        
        # Load additional disease info
        self.load_disease_info()
    
    def train_model(self, df):
        """Train and save the model"""
        X = df.drop(['disease'], axis=1)
        y = df['disease']
        
        self.model = RandomForestClassifier(n_estimators=200, random_state=42)
        self.model.fit(X, y)
        
        # Save the model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
    
    def load_disease_info(self):
        """Load additional disease information from CSV files"""
        # Load precautions
        self.precautions = pd.read_csv(self.precautions_path)
        # Load descriptions
        self.descriptions = pd.read_csv(self.description_path)
        # Load diets
        self.diets = pd.read_csv(self.diet_path)
        # Load workouts
        self.workouts = pd.read_csv(self.workout_path)
        # Load medications
        self.medications = pd.read_csv(self.medicine_path)
        
        # Disease specialties mapping
        self.disease_specialties = {
            "Fungal infection": "Infectious Disease",
            "Allergy": "Immunology/Allergy",
            "GERD": "Gastroenterology",
            # ... (add all other diseases from your notebook)
            "Impetigo": "Dermatology/Infectious Disease"
        }
    
    def predict_disease(self, symptoms_list):
        """Predict disease from list of symptoms"""
        # Symptom name mapping for common variations
        symptom_mapping = {
            'head pain': 'headache',
            'sore throat': 'throat_pain',
            'tummy ache': 'abdominal_pain',
            'high temperature': 'fever',
            'coughing': 'cough'
        }
        
        # Create input vector
        input_vector = np.zeros(len(self.symptom_dict))
        
        for symptom in symptoms_list:
            # Clean and map symptom name
            clean_symptom = symptom.strip().lower()
            mapped_symptom = symptom_mapping.get(clean_symptom, clean_symptom)
            
            # Convert to dataframe column format
            db_symptom = mapped_symptom.replace(" ", "_")
            
            if db_symptom in self.symptom_dict:
                input_vector[self.symptom_dict[db_symptom]] = 1
        
        # Make prediction
        disease = self.model.predict([input_vector])[0]
        return disease
    
    def get_disease_info(self, disease_name):
        """Get all information about a disease"""
        info = {
            "specialty": self.disease_specialties.get(disease_name, "General Physician"),
            "description": "",
            "precautions": [],
            "diet": [],
            "workout": [],
            "medications": []
        }
        
        # Get description
        desc = self.descriptions[self.descriptions['Disease'] == disease_name]['Description']
        if not desc.empty:
            info["description"] = desc.iloc[0]
        
        # Get precautions
        precautions = self.precautions[self.precautions['disease'] == disease_name]['workout']
        info["precautions"] = precautions.tolist() if not precautions.empty else []
        
        # Get diet
        diet = self.diets[self.diets['Disease'] == disease_name]['Diet']
        info["diet"] = diet.tolist() if not diet.empty else []
        
        # Get workout
        workout = self.workouts[self.workouts['disease'] == disease_name]['workout']
        info["workout"] = workout.tolist() if not workout.empty else []
        
        # Get medications
        meds = self.medications[self.medications['Disease'] == disease_name]['Medication']
        info["medications"] = meds.tolist() if not meds.empty else []
        
        return info