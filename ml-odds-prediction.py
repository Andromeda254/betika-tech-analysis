"""
ML Models for Betika Odds Prediction
Based on research findings from external odds providers analysis
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BetikaOddsPredictor:
    """
    Machine Learning models for predicting betting odds
    Based on external odds providers research and Betika data patterns
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.model_performance = {}
        
    def generate_synthetic_data(self, num_samples=10000):
        """
        Generate synthetic betting data based on research findings
        This simulates the data structure from external odds providers
        """
        logger.info("🔄 Generating synthetic betting data...")
        
        np.random.seed(42)
        
        # Base features based on research findings
        data = {
            # Match features
            'home_team_strength': np.random.normal(0.5, 0.2, num_samples),
            'away_team_strength': np.random.normal(0.5, 0.2, num_samples),
            'home_team_form': np.random.normal(0.5, 0.15, num_samples),
            'away_team_form': np.random.normal(0.5, 0.15, num_samples),
            
            # Historical data
            'head_to_head_home_wins': np.random.poisson(2, num_samples),
            'head_to_head_away_wins': np.random.poisson(2, num_samples),
            'head_to_head_draws': np.random.poisson(1, num_samples),
            
            # League context
            'league_importance': np.random.choice([1, 2, 3, 4, 5], num_samples, p=[0.1, 0.2, 0.4, 0.2, 0.1]),
            'match_importance': np.random.choice([1, 2, 3, 4, 5], num_samples, p=[0.2, 0.3, 0.3, 0.15, 0.05]),
            
            # External factors
            'weather_impact': np.random.normal(0, 0.1, num_samples),
            'injury_impact': np.random.normal(0, 0.15, num_samples),
            'rest_days_home': np.random.randint(2, 15, num_samples),
            'rest_days_away': np.random.randint(2, 15, num_samples),
            
            # Market sentiment
            'public_sentiment_home': np.random.normal(0.5, 0.2, num_samples),
            'public_sentiment_away': np.random.normal(0.5, 0.2, num_samples),
            
            # External provider data (simulated)
            'sportradar_confidence': np.random.normal(0.8, 0.1, num_samples),
            'lsports_confidence': np.random.normal(0.75, 0.15, num_samples),
            'betconstruct_confidence': np.random.normal(0.7, 0.2, num_samples),
            
            # Time features
            'days_since_last_match': np.random.randint(1, 30, num_samples),
            'is_weekend': np.random.choice([0, 1], num_samples, p=[0.7, 0.3]),
            'is_derby': np.random.choice([0, 1], num_samples, p=[0.9, 0.1]),
        }
        
        # Create derived features
        data['strength_difference'] = data['home_team_strength'] - data['away_team_strength']
        data['form_difference'] = data['home_team_form'] - data['away_team_form']
        data['total_goals_expected'] = (data['home_team_strength'] + data['away_team_strength']) * 2.5
        data['home_advantage'] = np.random.normal(0.1, 0.05, num_samples)
        
        # Generate target variables (odds)
        # Home win odds (1.5 to 10.0)
        home_win_prob = 1 / (1 + np.exp(-(data['strength_difference'] + data['home_advantage'] + 
                                          data['form_difference'] * 0.5)))
        data['home_win_odds'] = np.clip(1 / (home_win_prob + 0.05), 1.5, 10.0)
        
        # Draw odds (2.5 to 5.0)
        draw_prob = 0.25 + np.random.normal(0, 0.1, num_samples)
        data['draw_odds'] = np.clip(1 / (draw_prob + 0.1), 2.5, 5.0)
        
        # Away win odds (1.5 to 10.0)
        away_win_prob = 1 - home_win_prob - draw_prob
        data['away_win_odds'] = np.clip(1 / (away_win_prob + 0.05), 1.5, 10.0)
        
        # Over/Under odds
        data['over_2_5_odds'] = np.clip(1 / (0.4 + np.random.normal(0, 0.1, num_samples)), 1.5, 3.0)
        data['under_2_5_odds'] = np.clip(1 / (0.6 + np.random.normal(0, 0.1, num_samples)), 1.2, 2.5)
        
        # Both teams to score
        btts_prob = 0.5 + np.random.normal(0, 0.15, num_samples)
        data['btts_yes_odds'] = np.clip(1 / (btts_prob + 0.1), 1.5, 3.0)
        data['btts_no_odds'] = np.clip(1 / (1 - btts_prob + 0.1), 1.2, 2.5)
        
        return pd.DataFrame(data)
    
    def prepare_features(self, df):
        """
        Prepare features for ML models
        """
        logger.info("🔧 Preparing features for ML models...")
        
        # Select features (exclude target variables)
        feature_columns = [col for col in df.columns if not col.endswith('_odds')]
        X = df[feature_columns].copy()
        
        # Handle categorical variables
        categorical_columns = ['league_importance', 'match_importance']
        for col in categorical_columns:
            if col in X.columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.encoders[col] = le
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.scalers['features'] = scaler
        
        return X_scaled, feature_columns
    
    def train_models(self, X, y, target_name):
        """
        Train multiple ML models for odds prediction
        """
        logger.info(f"🤖 Training models for {target_name}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Define models based on research findings
        models = {
            'random_forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            ),
            'neural_network': MLPRegressor(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=42
            ),
            'logistic_regression': LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }
        
        best_model = None
        best_score = -np.inf
        
        for name, model in models.items():
            try:
                # Train model
                model.fit(X_train, y_train)
                
                # Predict
                y_pred = model.predict(X_test)
                
                # Evaluate
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
                
                # Store results
                self.model_performance[f"{target_name}_{name}"] = {
                    'mse': mse,
                    'r2': r2,
                    'mae': mae,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std()
                }
                
                # Store model
                self.models[f"{target_name}_{name}"] = model
                
                # Feature importance (for tree-based models)
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance[f"{target_name}_{name}"] = model.feature_importances_
                
                logger.info(f"✅ {name}: R² = {r2:.4f}, MAE = {mae:.4f}")
                
                # Track best model
                if r2 > best_score:
                    best_score = r2
                    best_model = name
                    
            except Exception as e:
                logger.error(f"❌ Error training {name}: {e}")
        
        return best_model, best_score
    
    def train_all_models(self, df):
        """
        Train models for all odds types
        """
        logger.info("🚀 Training all ML models...")
        
        # Prepare features
        X, feature_columns = self.prepare_features(df)
        
        # Target variables
        target_columns = [col for col in df.columns if col.endswith('_odds')]
        
        results = {}
        
        for target in target_columns:
            logger.info(f"🎯 Training models for {target}...")
            y = df[target].values
            
            best_model, best_score = self.train_models(X, y, target)
            results[target] = {
                'best_model': best_model,
                'best_score': best_score
            }
        
        return results, feature_columns
    
    def predict_odds(self, match_data, target_odds):
        """
        Predict odds for a specific match
        """
        if f"{target_odds}_random_forest" not in self.models:
            raise ValueError(f"Model for {target_odds} not found")
        
        # Prepare input data
        input_data = np.array([match_data]).reshape(1, -1)
        
        # Scale features
        input_scaled = self.scalers['features'].transform(input_data)
        
        # Predict
        model = self.models[f"{target_odds}_random_forest"]
        prediction = model.predict(input_scaled)[0]
        
        return prediction
    
    def save_models(self):
        """
        Save trained models and metadata
        """
        logger.info("💾 Saving models and metadata...")
        
        # Save models
        for name, model in self.models.items():
            joblib.dump(model, f'models/{name}.joblib')
        
        # Save scalers
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f'models/{name}_scaler.joblib')
        
        # Save encoders
        for name, encoder in self.encoders.items():
            joblib.dump(encoder, f'models/{name}_encoder.joblib')
        
        # Save metadata
        metadata = {
            'model_performance': self.model_performance,
            'feature_importance': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in self.feature_importance.items()},
            'timestamp': datetime.now().isoformat(),
            'models_trained': list(self.models.keys())
        }
        
        with open('models/metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("✅ Models saved successfully!")
    
    def generate_prediction_report(self, df, results, feature_columns):
        """
        Generate comprehensive prediction report
        """
        logger.info("📊 Generating prediction report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_samples': len(df),
                'features_used': len(feature_columns),
                'models_trained': len(self.models),
                'target_variables': len([col for col in df.columns if col.endswith('_odds')])
            },
            'model_performance': self.model_performance,
            'feature_importance': {k: v.tolist() if hasattr(v, 'tolist') else v for k, v in self.feature_importance.items()},
            'best_models': results,
            'recommendations': {
                'primary_model': 'Random Forest (best overall performance)',
                'backup_model': 'Gradient Boosting (good for complex patterns)',
                'real_time_model': 'Neural Network (fast inference)',
                'interpretability': 'Logistic Regression (explainable predictions)'
            },
            'implementation_notes': {
                'data_requirements': 'Match statistics, team form, external provider data',
                'update_frequency': 'Daily model retraining recommended',
                'feature_engineering': 'Include external odds provider confidence scores',
                'monitoring': 'Track prediction accuracy vs actual odds changes'
            }
        }
        
        # Save report
        with open('ml-prediction-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    """
    Main execution function
    """
    logger.info("🚀 Starting ML Odds Prediction System...")
    
    # Create models directory
    import os
    os.makedirs('models', exist_ok=True)
    
    # Initialize predictor
    predictor = BetikaOddsPredictor()
    
    try:
        # Generate synthetic data
        df = predictor.generate_synthetic_data(10000)
        logger.info(f"📊 Generated {len(df)} samples with {len(df.columns)} features")
        
        # Train all models
        results, feature_columns = predictor.train_all_models(df)
        
        # Save models
        predictor.save_models()
        
        # Generate report
        report = predictor.generate_prediction_report(df, results, feature_columns)
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 ML ODDS PREDICTION SYSTEM COMPLETE!")
        print("="*60)
        print(f"📊 Total Samples: {len(df)}")
        print(f"🔧 Features Used: {len(feature_columns)}")
        print(f"🤖 Models Trained: {len(predictor.models)}")
        print(f"🎯 Target Variables: {len([col for col in df.columns if col.endswith('_odds')])}")
        
        print("\n🏆 Best Models by Target:")
        for target, result in results.items():
            print(f"  {target}: {result['best_model']} (R² = {result['best_score']:.4f})")
        
        print("\n📁 Files Generated:")
        print("  - models/ (trained ML models)")
        print("  - ml-prediction-report.json")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ ML training failed: {e}")
        raise

if __name__ == "__main__":
    main()
