"""
Sentiment analysis module using LLM.
Analyzes financial news articles for sentiment using OpenAI API.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import openai

try:
    from openai.error import RateLimitError, AuthenticationError, OpenAIError
except ImportError:
    try:
        from openai import OpenAIError
    except ImportError:
        OpenAIError = Exception
    RateLimitError = AuthenticationError = OpenAIError

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment of financial news using OpenAI LLM."""

    def __init__(self, config: Dict):
        """
        Initialize SentimentAnalyzer.

        Args:
            config: Configuration dictionary with LLM settings
        """
        self.config = config
        llm_config = config.get('llm', {})

        # Initialize OpenAI
        openai.api_key = llm_config.get('api_key')
        self.model = llm_config.get('model', 'gpt-3.5-turbo')
        self.temperature = llm_config.get('temperature', 0.3)
        self.max_tokens = llm_config.get('max_tokens', 500)

        logger.info(f"SentimentAnalyzer initialized with model: {self.model}")

    def analyze_article_sentiment(self, article: Dict, context: str = None) -> Optional[Dict]:
        """
        Analyze sentiment of a single article.

        Args:
            article: Article dict with 'title', 'summary', 'content'
            context: Additional context (e.g., 'AAPL', 'Technology sector')

        Returns:
            Dict with sentiment, score, summary or None if error
        """
        # Extract text from article
        text = f"{article.get('title', '')}\n\n{article.get('summary', '')}"
        if article.get('content'):
            text += f"\n\n{article.get('content', '')}"

        # Limit text length to avoid token limits
        text = text[:2000]

        try:
            sentiment_data = self._call_openai_api(text, context)
            return sentiment_data
        except Exception as e:
            logger.error(f"Error analyzing article sentiment: {e}")
            return None

    def analyze_batch_sentiment(self, articles: List[Dict], context: str = None) -> Dict:
        """
        Analyze sentiment of multiple articles and aggregate.

        Args:
            articles: List of article dicts
            context: Context for analysis (e.g., 'AAPL', 'Technology sector')

        Returns:
            Aggregated sentiment dict
        """
        sentiments = []

        for article in articles:
            sentiment = self.analyze_article_sentiment(article, context)
            if sentiment:
                sentiments.append(sentiment)

        # Aggregate sentiments
        if sentiments:
            aggregated = self._aggregate_sentiments(sentiments)
            aggregated['article_count'] = len(sentiments)
            aggregated['analyzed_at'] = datetime.now().isoformat()
            return aggregated
        else:
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'summary': 'No articles to analyze',
                'article_count': 0,
                'analyzed_at': datetime.now().isoformat()
            }

    def _call_openai_api(self, text: str, context: str = None) -> Dict:
        """Call OpenAI API for sentiment analysis."""
        context_str = f" for {context}" if context else ""

        prompt = f"""Analyze the sentiment of the following financial news article{context_str}.

Article:
{text}

Respond ONLY with a valid JSON object (no markdown, no additional text) in this exact format:
{{
    "sentiment": "bullish" or "neutral" or "bearish",
    "score": a number between -1.0 (most bearish) and 1.0 (most bullish),
    "confidence": a number between 0.0 and 1.0 indicating confidence in the analysis,
    "summary": "one sentence summary of sentiment impact"
}}"""

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial sentiment analyzer. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            response_text = response['choices'][0]['message']['content'].strip()

            # Parse JSON response
            try:
                sentiment_data = json.loads(response_text)
                return sentiment_data
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse sentiment response as JSON: {response_text}")
                # Fallback parsing
                return self._parse_sentiment_fallback(response_text)

        except RateLimitError:
            logger.warning("OpenAI rate limit hit, using fallback sentiment")
            return self._fallback_sentiment()
        except AuthenticationError:
            logger.error("OpenAI authentication failed. Check API key.")
            return self._fallback_sentiment()
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            return self._fallback_sentiment()
        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {e}")
            return self._fallback_sentiment()

    def _parse_sentiment_fallback(self, text: str) -> Dict:
        """Fallback parsing when JSON parsing fails."""
        text_lower = text.lower()

        # Simple keyword matching
        if 'bearish' in text_lower or 'negative' in text_lower or 'down' in text_lower:
            sentiment = 'bearish'
            score = -0.5
        elif 'bullish' in text_lower or 'positive' in text_lower or 'up' in text_lower:
            sentiment = 'bullish'
            score = 0.5
        else:
            sentiment = 'neutral'
            score = 0.0

        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': 0.3,
            'summary': 'Fallback sentiment analysis'
        }

    def _fallback_sentiment(self) -> Dict:
        """Return neutral sentiment when API fails."""
        return {
            'sentiment': 'neutral',
            'score': 0.0,
            'confidence': 0.0,
            'summary': 'API unavailable, neutral sentiment assumed'
        }

    def _aggregate_sentiments(self, sentiments: List[Dict]) -> Dict:
        """Aggregate multiple sentiment analyses."""
        if not sentiments:
            return {'sentiment': 'neutral', 'score': 0.0, 'confidence': 0.0}

        # Calculate average score
        avg_score = sum(s.get('score', 0.0) for s in sentiments) / len(sentiments)

        # Determine overall sentiment
        if avg_score > 0.1:
            overall_sentiment = 'bullish'
        elif avg_score < -0.1:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'

        # Average confidence
        avg_confidence = sum(s.get('confidence', 0.5) for s in sentiments) / len(sentiments)

        # Summary of most common sentiment
        sentiment_counts = {}
        for s in sentiments:
            sent = s.get('sentiment', 'neutral')
            sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1

        return {
            'sentiment': overall_sentiment,
            'score': round(avg_score, 3),
            'confidence': round(avg_confidence, 3),
            'summary': f"Analyzed {len(sentiments)} articles. Distribution: {sentiment_counts}"
        }

    def score_to_sentiment(self, score: float) -> str:
        """Convert numeric score to sentiment label."""
        if score > 0.1:
            return 'bullish'
        elif score < -0.1:
            return 'bearish'
        else:
            return 'neutral'
