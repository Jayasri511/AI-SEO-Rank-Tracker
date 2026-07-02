import re
from collections import Counter

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

try:
    from sentence_transformers import SentenceTransformer, util
    st_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    st_model = None

try:
    from bertopic import BERTopic
except Exception:
    BERTopic = None


POSITIVE_WORDS = [
    "good", "great", "excellent", "amazing", "best", "love", "comfortable",
    "quality", "perfect", "happy", "satisfied", "affordable", "recommend",
    "awesome", "nice", "useful", "worth", "premium", "beautiful", "soft",
    "value", "durable", "fast", "original"
]

NEGATIVE_WORDS = [
    "bad", "poor", "worst", "hate", "disappointed", "expensive",
    "uncomfortable", "low quality", "delay", "delayed", "broken",
    "not good", "waste", "problem", "issue", "return", "damaged",
    "fake", "terrible", "useless", "weak"
]


class EntityExtractionAgent:
    def run(self, text):
        entities = []

        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                entities.append({"text": ent.text, "label": ent.label_})

        prices = re.findall(r"(₹\s?\d+|\$\s?\d+|\d+\s?rs|\d+\s?rupees)", text, re.I)
        for price in prices:
            entities.append({"text": price, "label": "PRICE"})

        return entities


class SemanticSimilarityAgent:
    def run(self, product_a, product_b):
        if not product_a or not product_b:
            return 0

        if st_model:
            emb1 = st_model.encode(product_a, convert_to_tensor=True)
            emb2 = st_model.encode(product_b, convert_to_tensor=True)
            return round(util.cos_sim(emb1, emb2).item() * 100, 2)

        words1 = set(product_a.lower().split())
        words2 = set(product_b.lower().split())

        if not words1 or not words2:
            return 0

        return round((len(words1 & words2) / len(words1 | words2)) * 100, 2)


class TopicDiscoveryAgent:
    def run(self, texts):
        clean_texts = [t for t in texts if len(t.strip()) > 10]

        if len(clean_texts) >= 5 and BERTopic:
            try:
                model = BERTopic(verbose=False)
                model.fit_transform(clean_texts)
                info = model.get_topic_info().head(6)

                topics = []
                for _, row in info.iterrows():
                    if int(row["Topic"]) != -1:
                        topics.append({
                            "topic_id": int(row["Topic"]),
                            "topic_name": row["Name"],
                            "count": int(row["Count"])
                        })
                return topics
            except Exception:
                pass

        stopwords = {
            "the", "is", "and", "for", "this", "that", "with", "very",
            "but", "product", "from", "have", "they", "your"
        }

        words = []
        for text in clean_texts:
            for word in re.findall(r"\b[a-zA-Z]{4,}\b", text.lower()):
                if word not in stopwords:
                    words.append(word)

        return [
            {"topic_id": i + 1, "topic_name": word, "count": count}
            for i, (word, count) in enumerate(Counter(words).most_common(5))
        ]


class SentimentIntelligenceAgent:
    def run(self, reviews):
        results = []

        for review in reviews:
            text = review.lower()
            pos = sum(1 for word in POSITIVE_WORDS if word in text)
            neg = sum(1 for word in NEGATIVE_WORDS if word in text)

            if pos > neg:
                sentiment = "Positive"
            elif neg > pos:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"

            results.append({
                "review": review,
                "positive_score": pos,
                "negative_score": neg,
                "sentiment": sentiment
            })

        total = len(results)
        positive = len([r for r in results if r["sentiment"] == "Positive"])
        neutral = len([r for r in results if r["sentiment"] == "Neutral"])
        negative = len([r for r in results if r["sentiment"] == "Negative"])

        return {
            "total_reviews": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "positive_percent": round((positive / total) * 100, 2) if total else 0,
            "neutral_percent": round((neutral / total) * 100, 2) if total else 0,
            "negative_percent": round((negative / total) * 100, 2) if total else 0,
            "details": results
        }


class WinnerSelectionAgent:
    def run(self, product_a, product_b, similarity_score, topics):
        score_a = 50
        score_b = 50

        a_text = product_a.lower()
        b_text = product_b.lower()

        strength_words = ["quality", "comfortable", "durable", "affordable", "premium", "fast", "best"]

        for word in strength_words:
            if word in a_text:
                score_a += 5
            if word in b_text:
                score_b += 5

        if len(product_a) > len(product_b):
            score_a += 10
        elif len(product_b) > len(product_a):
            score_b += 10

        if similarity_score > 85:
            decision = "Tie / Highly Similar"
        elif score_a > score_b:
            decision = "Product A"
        elif score_b > score_a:
            decision = "Product B"
        else:
            decision = "Tie"

        confidence = min(95, abs(score_a - score_b) + 70)

        return {
            "product_a_score": score_a,
            "product_b_score": score_b,
            "winner": decision,
            "confidence": confidence
        }


class ReviewValidationAgent:
    def run(self, winner, reviews):
        sentiment_agent = SentimentIntelligenceAgent()
        sentiment = sentiment_agent.run(reviews)

        if sentiment["total_reviews"] == 0:
            validation = "No review data available for validation."
        elif sentiment["positive_percent"] >= 60:
            validation = "Customer reviews support the selected winner."
        elif sentiment["negative_percent"] >= 40:
            validation = "Customer reviews raise concerns about the selected winner."
        else:
            validation = "Customer reviews are mixed, so the winner needs careful evaluation."

        return {
            "winner_reviewed": winner,
            "review_sentiment": sentiment,
            "validation_result": validation
        }


class StrategyRecommendationAgent:
    def run(self, winner_result, review_validation, topics, entities):
        recommendations = []

        winner = winner_result["winner"]

        recommendations.append(f"Final selected option: {winner}.")

        if review_validation["review_sentiment"]["positive_percent"] >= 60:
            recommendations.append("Use positive customer feedback as a marketing advantage.")
        elif review_validation["review_sentiment"]["negative_percent"] >= 40:
            recommendations.append("Resolve repeated customer complaints before recommending strongly.")
        else:
            recommendations.append("Customer feedback is mixed; compare more reviews before final purchase.")

        if topics:
            recommendations.append(f"Important customer discussion area: {topics[0]['topic_name']}.")

        if entities:
            recommendations.append("Extracted brands, prices, and locations can support targeted positioning.")

        return recommendations


class FinalAgentOrchestrator:
    def run(self, product_a, product_b, category, reviews):
        entity_agent = EntityExtractionAgent()
        similarity_agent = SemanticSimilarityAgent()
        topic_agent = TopicDiscoveryAgent()
        winner_agent = WinnerSelectionAgent()
        review_validation_agent = ReviewValidationAgent()
        strategy_agent = StrategyRecommendationAgent()

        combined_text = product_a + " " + product_b + " " + category + " " + " ".join(reviews)

        entities = entity_agent.run(combined_text)
        similarity_score = similarity_agent.run(product_a, product_b)
        topics = topic_agent.run([product_a, product_b] + reviews)

        winner_result = winner_agent.run(product_a, product_b, similarity_score, topics)

        review_validation = review_validation_agent.run(
            winner_result["winner"],
            reviews
        )

        recommendations = strategy_agent.run(
            winner_result,
            review_validation,
            topics,
            entities
        )

        return {
            "agents_used": [
                "Entity Extraction Agent using spaCy",
                "Semantic Similarity Agent using Sentence Transformers",
                "Topic Discovery Agent using BERTopic",
                "Winner Selection Agent",
                "Review Validation Agent",
                "Strategy Recommendation Agent"
            ],
            "entities": entities,
            "similarity_score": similarity_score,
            "topics": topics,
            "winner_result": winner_result,
            "review_validation": review_validation,
            "recommendations": recommendations
        }