import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import os

class SmartCurapath:
    def __init__(self, model_path=None, data_dir='.'):
        self.model = None
        self.symptom_dict = {}
        self.disease_dict = {}
        self.data_dir = data_dir
        
        # Medical specialty mapping
        self.specialty_mapping = {
            "Fungal infection": "Infectious Disease",
            "Allergy": "Immunology/Allergy",
            "GERD": "Gastroenterology",
            "Chronic cholestasis": "Gastroenterology",
            "Drug Reaction": "Allergy/Immunology",
            "Peptic ulcer diseae": "Gastroenterology",
            "AIDS": "Infectious Disease",
            "Diabetes": "Endocrinology",
            "Gastroenteritis": "Gastroenterology",
            "Bronchial Asthma": "Pulmonology",
            "Hypertension": "Cardiology",
            "Migraine": "Neurology",
            "Cervical spondylosis": "Orthopedics/Neurology",
            "Paralysis (brain hemorrhage)": "Neurology/Neurosurgery",
            "Jaundice": "Gastroenterology/Hepatology",
            "Malaria": "Infectious Disease",
            "Chicken pox": "Infectious Disease",
            "Dengue": "Infectious Disease",
            "Typhoid": "Infectious Disease",
            "Hepatitis A": "Gastroenterology/Hepatology",
            "Hepatitis B": "Gastroenterology/Hepatology",
            "Hepatitis C": "Gastroenterology/Hepatology",
            "Hepatitis D": "Gastroenterology/Hepatology",
            "Hepatitis E": "Gastroenterology/Hepatology",
            "Alcoholic hepatitis": "Gastroenterology/Hepatology",
            "Tuberculosis": "Pulmonology/Infectious Disease",
            "Common Cold": "General Physician",
            "Pneumonia": "Pulmonology",
            "Dimorphic hemmorhoids(piles)": "General Surgery",
            "Heart attack": "Cardiology",
            "Varicose veins": "Vascular Surgery",
            "Hypothyroidism": "Endocrinology",
            "Hyperthyroidism": "Endocrinology",
            "Hypoglycemia": "Endocrinology",
            "Osteoarthristis": "Orthopedics",
            "Arthritis": "Rheumatology/Orthopedics",
            "(vertigo) Paroymsal Positional Vertigo": "Neurology",
            "Acne": "Dermatology",
            "Urinary tract infection": "Urology",
            "Psoriasis": "Dermatology",
            "Impetigo": "Dermatology/Infectious Disease"
        }
        
        # Symptom normalization mapping
        self.symptom_mapping = {
            'head pain': 'headache',
            'sore throat': 'throat_pain',
            'tummy ache': 'abdominal_pain',
            'high temperature': 'fever',
            'coughing': 'cough',
            'stomach pain': 'abdominal_pain',
            'runny nose': 'runny_nose',
            'body pain': 'body_ache',
            'nausea': 'nausea',
            'dizziness': 'dizziness'
        }
        
        # Load auxiliary data
        self.load_aux_data()
        
        # Load or train model
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self.train_model()
    
    def load_aux_data(self):
        """Load all auxiliary data files"""
        try:
            self.precaution = pd.read_csv(os.path.join(self.data_dir, 'precautions_df.csv'))
            self.description = pd.read_csv(os.path.join(self.data_dir, 'description.csv'))
            self.diet = pd.read_csv(os.path.join(self.data_dir, 'diets.csv'))
            self.workout = pd.read_csv(os.path.join(self.data_dir, 'workout_df.csv'))
            self.medicine = pd.read_csv(os.path.join(self.data_dir, 'medications.csv'))
        except Exception as e:
            print(f"Error loading auxiliary data: {e}")
    
    def train_model(self):
        """Train the disease prediction model"""
        try:
            # Load training data
            df = pd.read_csv(os.path.join(self.data_dir, 'training_data.csv'))
            
            # Prepare features and target
            X = df.drop(['disease'], axis=1)
            Y = df['disease']
            
            # Create symptom dictionary
            self.symptom_dict = {symptom: idx for idx, symptom in enumerate(X.columns)}
            self.symptom_list = list(X.columns)
            
            # Create disease dictionary
            self.disease_dict = {disease: idx for idx, disease in enumerate(Y.unique())}
            self.reverse_disease_dict = {v: k for k, v in self.disease_dict.items()}
            
            # Split data
            X_train, X_test, Y_train, Y_test = train_test_split(
                X, Y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model = RandomForestClassifier(n_estimators=200, random_state=42)
            self.model.fit(X_train, Y_train)
            
            # Evaluate
            Y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(Y_pred, Y_test)
            print(f"Model trained with accuracy: {accuracy:.2f}")
            
            # Save model
            self.save_model('disease_model.pkl')
            
        except Exception as e:
            print(f"Error training model: {e}")
    
    def save_model(self, path):
        """Save the trained model to a file"""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'symptom_dict': self.symptom_dict,
                'disease_dict': self.disease_dict,
                'reverse_disease_dict': self.reverse_disease_dict,
                'symptom_list': self.symptom_list
            }, f)
    
    def load_model(self, path):
        """Load a trained model from file"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.symptom_dict = data['symptom_dict']
            self.disease_dict = data['disease_dict']
            self.reverse_disease_dict = data['reverse_disease_dict']
            self.symptom_list = data['symptom_list']
    
    def normalize_symptoms(self, symptoms):
        """Normalize symptom names using the mapping"""
        normalized = []
        for symptom in symptoms:
            # Clean the symptom name
            clean_symptom = symptom.lower().strip()
            
            # Map to standardized name if available
            mapped_symptom = self.symptom_mapping.get(clean_symptom, clean_symptom)
            
            # Replace spaces with underscores to match training data format
            formatted_symptom = mapped_symptom.replace(' ', '_')
            
            normalized.append(formatted_symptom)
        
        return normalized
    
    def predict_disease(self, symptoms):
        """Predict disease from symptoms"""
        if not self.model:
            raise ValueError("Model not loaded or trained")
        
        # Normalize symptom names
        normalized_symptoms = self.normalize_symptoms(symptoms)
        
        # Create input vector
        input_vector = np.zeros(len(self.symptom_list))
        found_symptoms = []
        
        for symptom in normalized_symptoms:
            if symptom in self.symptom_dict:
                index = self.symptom_dict[symptom]
                input_vector[index] = 1
                found_symptoms.append(symptom)
            else:
                print(f"Warning: Symptom '{symptom}' not found in training data")
        
        if not found_symptoms:
            raise ValueError("None of the provided symptoms were recognized")
        
        # Make prediction
        prediction = self.model.predict([input_vector])[0]
        
        return prediction
    
    def get_disease_info(self, disease_name):
        """Get comprehensive information about a disease"""
        info = {
            'specialty': self.specialty_mapping.get(disease_name, 'General Physician'),
            'description': '',
            'precautions': [],
            'diet': [],
            'workout': [],
            'medications': []
        }
        
        # Get description
        desc = self.description[self.description['Disease'] == disease_name]['Description']
        if not desc.empty:
            info['description'] = desc.iloc[0]
        
        # Get precautions
        prec = self.precaution[self.precaution['disease'] == disease_name]['workout']
        if not prec.empty:
            info['precautions'] = prec.tolist()
        
        # Get diet recommendations
        diet = self.diet[self.diet['Disease'] == disease_name]['Diet']
        if not diet.empty:
            info['diet'] = diet.tolist()
        
        # Get workout recommendations
        workout = self.workout[self.workout['disease'] == disease_name]['workout']
        if not workout.empty:
            info['workout'] = workout.tolist()
        
        # Get medications
        meds = self.medicine[self.medicine['Disease'] == disease_name]['Medication']
        if not meds.empty:
            info['medications'] = meds.tolist()
        
        return info
    
    def get_recommendations(self, symptoms):
        """Get comprehensive recommendations based on symptoms"""
        try:
            # Predict disease
            disease = self.predict_disease(symptoms)
            
            # Get disease information
            info = self.get_disease_info(disease)
            
            return {
                'predicted_disease': disease,
                'recommended_specialist': info['specialty'],
                'description': info['description'],
                'precautions': info['precautions'],
                'diet_recommendations': info['diet'],
                'exercise_recommendations': info['workout'],
                'medications': info['medications']
            }
        except Exception as e:
            return {
                'error': str(e)
            }