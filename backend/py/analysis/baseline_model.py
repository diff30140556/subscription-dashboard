#!/usr/bin/env python3
"""
Baseline churn prediction model using Logistic Regression.
Implements a complete ML pipeline with data preprocessing, training, evaluation, and caching.
"""

import os
import json
import pickle
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncpg
import pandas as pd
import numpy as np
from pathlib import Path

# ML imports
try:
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
    from sklearn.pipeline import Pipeline
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from ..core.db import fetch_df
from ..core.utils import safe_div, round_fp


class ChurnModelTrainer:
    """
    Churn prediction model trainer with comprehensive preprocessing and evaluation.
    """
    
    def __init__(self, model_dir: str = "../models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # Feature configuration
        self.numeric_features = ["tenure", "MonthlyCharges"]
        self.categorical_features = ["Contract", "PaymentMethod"]
        self.boolean_features = ["OnlineSecurity", "TechSupport"]
        
        # Model files
        self.model_path = self.model_dir / "baseline_model.pkl"
        self.metadata_path = self.model_dir / "baseline_metadata.json"
        self.scaler_path = self.model_dir / "baseline_scaler.pkl"
        
        # Model configuration
        self.test_size = 0.2
        self.random_state = 42
        self.model_params = {
            "solver": "liblinear",
            "class_weight": "balanced", 
            "max_iter": 1000,
            "random_state": self.random_state
        }
    
    async def load_and_preprocess_data(self, conn: Optional[asyncpg.Connection] = None) -> pd.DataFrame:
        """
        Load data from database and perform preprocessing.
        
        Returns:
            Preprocessed DataFrame ready for training
        """
        # SQL query to get all required features
        # Exclude total_charges to avoid collinearity
        sql = """
        SELECT 
            CASE WHEN "Churn" = 'Yes' THEN 1 ELSE 0 END as churn,
            tenure,
            "MonthlyCharges",
            "Contract",
            "PaymentMethod", 
            "OnlineSecurity",
            "TechSupport"
        FROM churn_customers
        WHERE tenure IS NOT NULL 
          AND "MonthlyCharges" IS NOT NULL;
        """
        
        if conn:
            # Use provided connection
            rows = await conn.fetch(sql)
            df = pd.DataFrame([dict(row) for row in rows])
        else:
            # Use global db manager
            df = await fetch_df(sql)
        
        if df.empty:
            raise ValueError("No data available for model training")
        
        # Preprocess features
        df = self._preprocess_features(df)
        
        return df
    
    def _preprocess_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess features according to specifications.
        
        Args:
            df: Raw DataFrame from database
            
        Returns:
            Preprocessed DataFrame
        """
        df = df.copy()
        
        # Handle numeric features - fill missing with median
        for col in self.numeric_features:
            if col in df.columns:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
        
        # Handle categorical features - fill missing with "Unknown"
        for col in self.categorical_features:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown")
        
        # Handle boolean features - convert to 0/1, NULL=0
        for col in self.boolean_features:
            if col in df.columns:
                # Map Yes/No to 1/0, NULL to 0
                df[col] = df[col].map({"Yes": 1, "No": 0}).fillna(0).astype(int)
        
        return df
    
    def _create_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Create feature matrix with one-hot encoding.
        
        Args:
            df: Preprocessed DataFrame
            
        Returns:
            Tuple of (feature_matrix, feature_names)
        """
        features = []
        feature_names = []
        
        # Add numeric features
        for col in self.numeric_features:
            if col in df.columns:
                features.append(df[col].values.reshape(-1, 1))
                feature_names.append(col)
        
        # Add boolean features
        for col in self.boolean_features:
            if col in df.columns:
                features.append(df[col].values.reshape(-1, 1))
                feature_names.append(col)
        
        # One-hot encode categorical features
        for col in self.categorical_features:
            if col in df.columns:
                # Get unique values
                unique_vals = sorted(df[col].unique())
                
                # Create one-hot columns (drop first to avoid multicollinearity)
                for i, val in enumerate(unique_vals[1:], 1):
                    one_hot = (df[col] == val).astype(int).values.reshape(-1, 1)
                    features.append(one_hot)
                    feature_names.append(f"{col}_{val}")
        
        # Combine all features
        if features:
            X = np.hstack(features)
        else:
            raise ValueError("No features available for training")
        
        return pd.DataFrame(X, columns=feature_names), feature_names
    
    def _train_model(self, X: pd.DataFrame, y: pd.Series) -> Tuple[Pipeline, Dict[str, Any]]:
        """
        Train logistic regression model with evaluation.
        
        Args:
            X: Feature matrix
            y: Target variable
            
        Returns:
            Tuple of (trained_pipeline, evaluation_metrics)
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=self.test_size,
            stratify=y,
            random_state=self.random_state
        )
        
        # Create pipeline with scaling and logistic regression
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(**self.model_params))
        ])
        
        # Train model
        pipeline.fit(X_train, y_train)
        
        # Evaluate model
        y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Get feature weights (coefficients)
        coefficients = pipeline.named_steps["classifier"].coef_[0]
        
        # Create feature importance ranking
        feature_importance = []
        for i, (feature_name, coef) in enumerate(zip(X.columns, coefficients)):
            feature_importance.append({
                "feature": feature_name,
                "weight": round_fp(float(coef), 4)
            })
        
        # Sort by absolute weight (most important features first)
        feature_importance.sort(key=lambda x: abs(x["weight"]), reverse=True)
        
        # Take top 10 features
        top_features = feature_importance[:10]
        
        # Evaluation metrics
        metrics = {
            "auc": round_fp(float(auc_score), 4),
            "top_features": top_features,
            "total_features": len(X.columns),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "positive_rate": round_fp(float(y.mean()), 4)
        }
        
        return pipeline, metrics
    
    def _save_model(self, pipeline: Pipeline, metrics: Dict[str, Any], feature_names: List[str]):
        """
        Save trained model and metadata to disk.
        
        Args:
            pipeline: Trained model pipeline
            metrics: Evaluation metrics
            feature_names: List of feature names
        """
        # Save model
        joblib.dump(pipeline, self.model_path)
        
        # Save metadata
        metadata = {
            "model_type": "LogisticRegression",
            "feature_names": feature_names,
            "training_date": datetime.utcnow().isoformat() + "Z",
            "model_params": self.model_params,
            "preprocessing": {
                "numeric_features": self.numeric_features,
                "categorical_features": self.categorical_features,
                "boolean_features": self.boolean_features
            },
            "metrics": metrics
        }
        
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def _load_model(self) -> Tuple[Pipeline, Dict[str, Any]]:
        """
        Load saved model and metadata from disk.
        
        Returns:
            Tuple of (model_pipeline, metadata)
        """
        if not self.model_path.exists() or not self.metadata_path.exists():
            raise FileNotFoundError("Model files not found")
        
        # Load model
        pipeline = joblib.load(self.model_path)
        
        # Load metadata
        with open(self.metadata_path, "r") as f:
            metadata = json.load(f)
        
        return pipeline, metadata
    
    async def train_and_save(self, conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
        """
        Train baseline churn prediction model and save to disk.
        
        Args:
            conn: Optional database connection
            
        Returns:
            Dict with model metrics and training info
        """
        if not ML_AVAILABLE:
            raise ImportError("scikit-learn not available. Install with: pip install scikit-learn")
        
        try:
            # Load and preprocess data
            df = await self.load_and_preprocess_data(conn)
            
            # Prepare features and target
            X, feature_names = self._create_features(df)
            y = df["churn"]
            
            # Train model
            pipeline, metrics = self._train_model(X, y)
            
            # Save model and metadata
            self._save_model(pipeline, metrics, feature_names)
            
            return {
                "status": "success",
                "message": f"Model trained and saved successfully",
                "model": {
                    "auc": metrics["auc"],
                    "top_features": metrics["top_features"]
                },
                "training_info": {
                    "total_samples": len(df),
                    "total_features": metrics["total_features"],
                    "train_samples": metrics["train_samples"],
                    "test_samples": metrics["test_samples"],
                    "positive_rate": metrics["positive_rate"]
                }
            }
            
        except Exception as e:
            raise ValueError(f"Model training failed: {str(e)}")
    
    async def load_or_train(self, conn: Optional[asyncpg.Connection] = None) -> Dict[str, Any]:
        """
        Load existing model or train new one if not exists.
        
        Args:
            conn: Optional database connection
            
        Returns:
            Dict with model metrics
        """
        try:
            # Try to load existing model
            pipeline, metadata = self._load_model()
            
            return {
                "status": "loaded",
                "message": f"Model loaded from cache (trained: {metadata.get('training_date', 'unknown')})",
                "model": {
                    "auc": metadata["metrics"]["auc"],
                    "top_features": metadata["metrics"]["top_features"]
                },
                "training_info": {
                    "total_samples": metadata["metrics"].get("train_samples", 0) + metadata["metrics"].get("test_samples", 0),
                    "total_features": metadata["metrics"]["total_features"],
                    "train_samples": metadata["metrics"]["train_samples"],
                    "test_samples": metadata["metrics"]["test_samples"],
                    "positive_rate": metadata["metrics"]["positive_rate"]
                }
            }
            
        except FileNotFoundError:
            # Model doesn't exist, train new one
            return await self.train_and_save(conn)


# Global trainer instance
_trainer = None

def get_trainer(model_dir: str = "models") -> ChurnModelTrainer:
    """Get global trainer instance."""
    global _trainer
    if _trainer is None:
        _trainer = ChurnModelTrainer(model_dir)
    return _trainer


async def train_and_save(conn: Optional[asyncpg.Connection] = None, model_dir: str = "models") -> Dict[str, Any]:
    """
    Train baseline churn prediction model and save to disk.
    
    Args:
        conn: Optional database connection
        model_dir: Directory to save model files
        
    Returns:
        Dict with model metrics and training info
    """
    trainer = get_trainer(model_dir)
    return await trainer.train_and_save(conn)


async def load_or_train(conn: Optional[asyncpg.Connection] = None, model_dir: str = "models") -> Dict[str, Any]:
    """
    Load existing model or train new one if not exists.
    
    Args:
        conn: Optional database connection
        model_dir: Directory to save/load model files
        
    Returns:
        Dict with model metrics
    """
    trainer = get_trainer(model_dir)
    return await trainer.load_or_train(conn)


async def get_model_info(model_dir: str = "models") -> Dict[str, Any]:
    """
    Get information about saved model without loading it.
    
    Args:
        model_dir: Directory containing model files
        
    Returns:
        Dict with model information
    """
    trainer = get_trainer(model_dir)
    
    try:
        _, metadata = trainer._load_model()
        return {
            "model_exists": True,
            "training_date": metadata.get("training_date"),
            "model_type": metadata.get("model_type"),
            "auc": metadata["metrics"]["auc"],
            "total_features": metadata["metrics"]["total_features"]
        }
    except FileNotFoundError:
        return {
            "model_exists": False,
            "message": "No trained model found"
        }