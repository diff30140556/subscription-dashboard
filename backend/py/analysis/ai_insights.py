#!/usr/bin/env python3
"""
AI-powered churn analysis insights using OpenAI GPT-4o.
Generates strategic recommendations and insights from churn analysis data.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# OpenAI imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class ChurnInsightsAI:
    """
    AI-powered churn insights generator using OpenAI GPT-4o.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI insights generator.
        
        Args:
            api_key: OpenAI API key (if None, loads from OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with: pip install openai")
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize OpenAI client with explicit parameters only
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            # If there are initialization issues, try with minimal parameters
            logger.warning(f"Initial OpenAI client creation failed: {e}")
            # Clear any proxy-related environment variables that might interfere
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client created successfully after clearing proxy vars")
            except Exception as e2:
                logger.error(f"Failed to create OpenAI client: {e2}")
                raise ValueError(f"Could not initialize OpenAI client: {e2}")
        
        # Model configuration
        self.model = "gpt-4o"
        self.max_tokens = 2000
        self.temperature = 0.3  # Lower temperature for more focused, analytical responses
    
    def _format_churn_data_prompt(self, churn_data: Dict[str, Any]) -> str:
        """
        Format churn analysis data into a structured prompt for GPT-4o.
        
        Args:
            churn_data: Dictionary containing churn analysis metrics
            
        Returns:
            Formatted prompt string for the AI model
        """
        prompt = """
You are a senior customer retention strategist specializing in Apple's subscription services ecosystem. Analyze the following subscription churn data from an Apple service (Apple Music, Apple TV+, iCloud+, etc.) and provide customer-centric insights and strategic recommendations that align with Apple's values of thoughtful innovation and exceptional user experience.

# SUBSCRIPTION CHURN ANALYSIS DATA

## Overall Metrics
"""
        
        # Add overall metrics
        if "overall_churn_rate" in churn_data:
            prompt += f"- Overall Churn Rate: {churn_data['overall_churn_rate']:.2%}\n"
        
        if "total_customers" in churn_data:
            prompt += f"- Total Subscribers: {churn_data['total_customers']:,}\n"
        
        if "churned_customers" in churn_data:
            prompt += f"- Churned Subscribers: {churn_data['churned_customers']:,}\n"
        
        if "average_tenure" in churn_data:
            prompt += f"- Average Subscription Tenure: {churn_data['average_tenure']:.1f} months\n"
        
        if "average_monthly_charges" in churn_data:
            prompt += f"- Average Monthly Subscription Cost: ${churn_data['average_monthly_charges']:.2f}\n"
        
        # Add contract analysis
        if "churn_by_contract" in churn_data:
            prompt += "\n## Churn by Subscription Plan\n"
            for contract in churn_data["churn_by_contract"]:
                prompt += f"- {contract['key']}: {contract['churn_rate']:.2%} churn rate ({contract['n']:,} subscribers)\n"
        
        # Add payment method analysis
        if "churn_by_payment" in churn_data:
            prompt += "\n## Churn by Payment Method\n"
            for payment in churn_data["churn_by_payment"]:
                prompt += f"- {payment['key']}: {payment['churn_rate']:.2%} churn rate ({payment['n']:,} subscribers)\n"
        
        # Add service features analysis
        if "churn_by_features" in churn_data:
            prompt += "\n## Churn by Service Features\n"
            for feature, feature_data in churn_data["churn_by_features"].items():
                prompt += f"### {feature}\n"
                for item in feature_data:
                    prompt += f"- {item['key']}: {item['churn_rate']:.2%} churn rate ({item['n']:,} subscribers)\n"
        
        # Add tenure distribution
        if "tenure_distribution" in churn_data:
            prompt += "\n## Churned Subscribers by Tenure\n"
            for tenure_bin in churn_data["tenure_distribution"]:
                prompt += f"- {tenure_bin['range']} months: {tenure_bin['count']:,} subscribers ({tenure_bin['pct']:.1%})\n"
        
        # Add monthly charges distribution
        if "monthly_charges_distribution" in churn_data:
            prompt += "\n## Churned Subscribers by Monthly Cost\n"
            for charge_bin in churn_data["monthly_charges_distribution"]:
                prompt += f"- ${charge_bin['range']}: {charge_bin['count']:,} subscribers ({charge_bin['pct']:.1%})\n"
        
        # Add ML model insights if available
        if "model_insights" in churn_data:
            model_data = churn_data["model_insights"]
            prompt += f"\n## Predictive Model Insights\n"
            prompt += f"- Model Performance (AUC): {model_data.get('auc', 'N/A')}\n"
            
            if "top_features" in model_data:
                prompt += "- Most Important Predictive Features:\n"
                for i, feature in enumerate(model_data["top_features"][:5], 1):
                    weight_direction = "increases" if feature["weight"] > 0 else "decreases"
                    prompt += f"  {i}. {feature['feature']} ({weight_direction} churn likelihood)\n"
        
        # Add analysis request
        prompt += """

# ANALYSIS REQUEST

As an Apple subscription retention strategist, provide a comprehensive analysis that reflects Apple's customer-first philosophy:

1. **KEY INSIGHTS**: Identify the 3 most critical findings from this subscription data that reveal why customers are leaving Apple's service ecosystem.

2. **STRATEGIC RECOMMENDATIONS**: Provide 2 specific, actionable strategies to improve subscriber retention that leverage Apple's strengths in user experience, ecosystem integration, and customer delight.

3. **IMPACT FORECAST**: Write one clear paragraph predicting what will happen if no retention action is taken. Consider the potential consequences including: projected churn rate increases, revenue impact, damage to Apple's customer loyalty reputation, and long-term effects on the Apple services ecosystem. Be specific about timeframes and quantify the risks where possible based on the current data trends.

Frame your analysis with Apple's focus on creating meaningful customer relationships, seamless experiences across devices, and long-term value creation. Consider how subscription churn affects the broader Apple ecosystem and customer lifetime value. Use the actual data points to support your strategic insights and recommendations.
"""
        
        return prompt
    
    async def generate_insights(self, churn_data: Dict[str, Any]) -> str:
        """
        Generate AI-powered insights from churn analysis data.
        
        Args:
            churn_data: Dictionary containing churn analysis metrics
            
        Returns:
            AI-generated insights and recommendations as text
            
        Raises:
            ValueError: If churn_data is empty or invalid
            Exception: For OpenAI API errors
        """
        if not churn_data:
            raise ValueError("Churn data cannot be empty")
        
        try:
            # Format data into prompt
            prompt = self._format_churn_data_prompt(churn_data)
            
            logger.info(f"Generating AI insights using {self.model}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior customer retention analyst and business strategist with expertise in telecom and subscription businesses. Provide actionable, data-driven insights and recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract the assistant's response
            insights = response.choices[0].message.content
            
            logger.info(f"AI insights generated successfully ({len(insights)} characters)")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            raise Exception(f"Failed to generate AI insights: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key by making a simple test request.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Make a minimal test request
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for validation
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False


# Global AI insights generator instance
_ai_generator = None

def get_ai_generator() -> ChurnInsightsAI:
    """Get global AI insights generator instance."""
    global _ai_generator
    if _ai_generator is None:
        _ai_generator = ChurnInsightsAI()
    return _ai_generator


async def generate_churn_insights(churn_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate AI-powered churn insights from analysis data.
    
    Args:
        churn_data: Dictionary containing churn analysis metrics
        
    Returns:
        Dict with AI insights and metadata
        
    Example:
        {
            "insights": "AI-generated strategic recommendations...",
            "metadata": {
                "generated_at": "2024-01-15T10:30:00Z",
                "model_used": "gpt-4o",
                "data_points_analyzed": 8
            }
        }
    """
    try:
        ai_generator = get_ai_generator()
        
        # Generate insights
        insights_text = await ai_generator.generate_insights(churn_data)
        
        # Count data points for metadata
        data_points = 0
        if "overall_churn_rate" in churn_data:
            data_points += 1
        if "churn_by_contract" in churn_data:
            data_points += len(churn_data["churn_by_contract"])
        if "churn_by_payment" in churn_data:
            data_points += len(churn_data["churn_by_payment"])
        if "churn_by_features" in churn_data:
            for feature_data in churn_data["churn_by_features"].values():
                data_points += len(feature_data)
        
        return {
            "insights": insights_text,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "model_used": ai_generator.model,
                "data_points_analyzed": data_points,
                "prompt_length": len(ai_generator._format_churn_data_prompt(churn_data))
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to generate churn insights: {str(e)}")


async def validate_openai_connection() -> Dict[str, Any]:
    """
    Validate OpenAI API connection and key.
    
    Returns:
        Dict with validation results
    """
    try:
        ai_generator = get_ai_generator()
        is_valid = ai_generator.validate_api_key()
        
        return {
            "api_key_valid": is_valid,
            "model_configured": ai_generator.model,
            "openai_available": OPENAI_AVAILABLE
        }
        
    except Exception as e:
        return {
            "api_key_valid": False,
            "model_configured": None,
            "openai_available": OPENAI_AVAILABLE,
            "error": str(e)
        }