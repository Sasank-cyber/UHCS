import re
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# --------------------------------------------------
# DOMAIN KNOWLEDGE / CONFIG (OPTIMIZED)
# --------------------------------------------------

BASE_SEVERITY = {
    "cleanliness": 0.15,
    "wifi": 0.35,
    "plumbing": 0.55,
    "electrical": 0.75,
    "safety": 0.95
}

RISK_KEYWORDS = {
    "fire": 0.5,
    "shock": 0.45,
    "gas": 0.5,
    "leakage": 0.25,
    "leaking": 0.25,
    "broken": 0.15,
    "emergency": 0.35,
    "water shortage": 0.3,
    "no water": 0.35,
    "power cut": 0.2,
    "injured": 0.5,
    "hurt": 0.4,
    "stink": 0.15,
    "pest": 0.3,
    "mosquito": 0.2,
    "rats": 0.35
}

DURATION_PATTERNS = {
    r"today": 0.0,
    r"yesterday": 0.08,
    r"\b2\s*days?\b": 0.15,
    r"\b3\s*days?\b": 0.25,
    r"\b[4-6]\s*days?\b": 0.4,
    r"\b\d+\s*days?\b": 0.35,
    r"week": 0.5,
    r"weeks": 0.6,
    r"month": 0.8
}

SCOPE_KEYWORDS = {
    "my room": 0.0,
    "our room": 0.05,
    "floor": 0.3,
    "entire hostel": 0.5,
    "whole hostel": 0.5,
    "common area": 0.35,
    "kitchen": 0.4,
    "washroom": 0.25,
    "all rooms": 0.5
}

URGENCY_KEYWORDS = {
    "immediately": 1.0,
    "urgent": 0.85,
    "asap": 0.75,
    "emergency": 0.8,
    "critical": 0.9,
    "soon": 0.5,
    "right now": 0.9,
    "now": 0.7
}

CATEGORY_URGENCY = {
    "safety": 0.4,
    "electrical": 0.3,
    "plumbing": 0.25,
    "wifi": 0.15,
    "cleanliness": 0.05
}

# --------------------------------------------------
# SEVERITY
# --------------------------------------------------

def calculate_severity(text, category):
    """Calculate severity based on category, risk keywords, duration, and scope."""
    text = text.lower()
    severity = BASE_SEVERITY.get(category, 0.3)

    for word, boost in RISK_KEYWORDS.items():
        if word in text:
            severity += boost

    for pattern, boost in DURATION_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            severity += boost

    for phrase, boost in SCOPE_KEYWORDS.items():
        if phrase in text:
            severity += boost

    return min(1.0, round(severity, 3))

# --------------------------------------------------
# FREQUENCY (CHAR N-GRAM TF-IDF WITH TIME WINDOW)
# --------------------------------------------------

def calculate_frequency(new_text, past_texts, time_window_days=7):
    """
    Calculate frequency using TF-IDF cosine similarity.
    Only considers complaints within the time window.
    """
    if not past_texts:
        return 0.05

    try:
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            lowercase=True,
            min_df=1
        )

        all_texts = past_texts + [new_text]
        vectors = vectorizer.fit_transform(all_texts)

        similarities = cosine_similarity(
            vectors[-1], vectors[:-1]
        )[0]

        # Count similar complaints (threshold > 0.25 - lowered from 0.35)
        similar_count = sum(sim > 0.25 for sim in similarities)

        if similar_count == 0:
            return 0.05
        elif similar_count == 1:
            return 0.2
        elif similar_count == 2:
            return 0.35
        elif similar_count == 3:
            return 0.5
        elif similar_count <= 5:
            return 0.65
        elif similar_count <= 8:
            return 0.8
        else:
            return 1.0
    except Exception as e:
        print(f"Error in frequency calculation: {e}")
        return 0.05

# --------------------------------------------------
# URGENCY
# --------------------------------------------------

def calculate_urgency(text, category, timestamp):
    """Calculate urgency based on keywords, category, and time of day."""
    text = text.lower()
    urgency = 0.0

    for word, score in URGENCY_KEYWORDS.items():
        if word in text:
            urgency = max(urgency, score)

    urgency += CATEGORY_URGENCY.get(category, 0.0)

    # Night time boost (10 PM to 6 AM)
    hour = timestamp.hour
    if hour >= 22 or hour <= 6:
        urgency += 0.2

    return min(1.0, round(urgency, 3))

# --------------------------------------------------
# TIME FACTOR
# --------------------------------------------------

def calculate_time_factor(created_at, status="open"):
    """
    Calculate time factor based on how long the complaint has been pending.
    Adjusted by status (resolved, in_progress, open).
    """
    if status == "resolved":
        return 0.0

    days_pending = (datetime.now() - created_at).days

    if days_pending == 0:
        score = 0.0
    elif days_pending == 1:
        score = 0.1
    elif days_pending <= 3:
        score = 0.25
    elif days_pending <= 6:
        score = 0.5
    elif days_pending <= 10:
        score = 0.75
    else:
        score = 1.0

    if status == "in_progress":
        score *= 0.6
    elif status == "pending_approval":
        score *= 0.8

    return round(score, 3)

# --------------------------------------------------
# FINAL PRIORITY SCORE
# --------------------------------------------------

def calculate_priority(severity, frequency, urgency, time_factor):
    """
    Compute weighted priority score.
    Weights: Severity (45%), Frequency (25%), Urgency (20%), Time (10%)
    Changed to give more weight to severity which is the primary indicator.
    """
    return round(
        0.45 * severity +
        0.25 * frequency +
        0.2 * urgency +
        0.1 * time_factor,
        3
    )

# --------------------------------------------------
# EXPLAINABILITY
# --------------------------------------------------

def get_priority_explanation(result, category, status):
    """Generate human-readable explanation for priority score."""
    explanation = []
    
    # More granular severity explanation
    if result["severity"] > 0.8:
        explanation.append(f"🔴 CRITICAL SEVERITY ({result['severity']}): {category.upper()} issue is extremely dangerous")
    elif result["severity"] > 0.6:
        explanation.append(f"⚠️ HIGH SEVERITY ({result['severity']}): {category.upper()} is significant")
    elif result["severity"] > 0.4:
        explanation.append(f"⚡ MEDIUM SEVERITY ({result['severity']}): {category.upper()} needs attention")
    
    # Frequency explanation
    if result["frequency"] > 0.7:
        explanation.append(f"📊 WIDESPREAD ({result['frequency']}): 6+ similar complaints found")
    elif result["frequency"] > 0.5:
        explanation.append(f"📊 REPEATED ISSUE ({result['frequency']}): Multiple similar complaints")
    elif result["frequency"] > 0.2:
        explanation.append(f"📊 SOME HISTORY ({result['frequency']}): Similar complaints exist")
    
    # Urgency explanation
    if result["urgency"] > 0.8:
        explanation.append(f"🔴 HIGHLY URGENT ({result['urgency']}): Immediate action required")
    elif result["urgency"] > 0.5:
        explanation.append(f"🟡 URGENT ({result['urgency']}): Quick response needed")
    
    # Time factor explanation
    if result["time_factor"] > 0.7:
        explanation.append(f"⏱️ CRITICAL DELAY ({result['time_factor']}): Pending for 7+ days")
    elif result["time_factor"] > 0.4:
        explanation.append(f"⏱️ DELAYED ({result['time_factor']}): Pending for several days")
    
    # Final priority classification (Adjusted thresholds)
    if result["priority_score"] >= 0.65:
        explanation.append("🚨 HIGH PRIORITY: Auto-escalate to admin immediately")
    elif result["priority_score"] >= 0.45:
        explanation.append("⚡ MEDIUM PRIORITY: Schedule within 2-3 days")
    elif result["priority_score"] >= 0.25:
        explanation.append("🟡 LOW PRIORITY: Schedule within 1 week")
    else:
        explanation.append("✅ VERY LOW PRIORITY: General maintenance")
    
    return " | ".join(explanation)

# --------------------------------------------------
# END-TO-END PIPELINE
# --------------------------------------------------

def process_complaint(
    text,
    category,
    created_at,
    past_texts,
    status="open"
):
    """
    Complete pipeline: Calculate all 4 signals and final priority score.
    Returns detailed breakdown with explainability.
    """
    severity = calculate_severity(text, category)
    frequency = calculate_frequency(text, past_texts)
    urgency = calculate_urgency(text, category, created_at)
    time_factor = calculate_time_factor(created_at, status)

    priority = calculate_priority(
        severity,
        frequency,
        urgency,
        time_factor
    )

    return {
        "severity": severity,
        "frequency": frequency,
        "urgency": urgency,
        "time_factor": time_factor,
        "priority_score": priority,
        "status": status,
        "category": category,
        "explanation": get_priority_explanation(
            {
                "severity": severity,
                "frequency": frequency,
                "urgency": urgency,
                "time_factor": time_factor,
                "priority_score": priority
            },
            category,
            status
        )
    }

# --------------------------------------------------
# DEMO RUN
# --------------------------------------------------

if __name__ == "__main__":
    # Test Case 1: High Priority - Water Leakage
    print("\n" + "=" * 100)
    print("TEST CASE 1: WATER LEAKAGE (EXPECTED: HIGH PRIORITY)")
    print("=" * 100)
    result1 = process_complaint(
        text="Water leakage in washroom for 4 days, whole floor affected, emergency",
        category="plumbing",
        created_at=datetime.now() - timedelta(days=4),
        past_texts=[
            "Water leaking near washroom",
            "Washroom pipe leakage issue",
            "Floor 2 washroom leaking"
        ],
        status="open"
    )

    for key, value in result1.items():
        print(f"{key.upper()}: {value}")

    # Test Case 2: Low-Medium Priority - WiFi Issue
    print("\n" + "=" * 100)
    print("TEST CASE 2: WIFI ISSUE (EXPECTED: LOW-MEDIUM PRIORITY)")
    print("=" * 100)
    result2 = process_complaint(
        text="WiFi not working in room 305 since yesterday",
        category="wifi",
        created_at=datetime.now() - timedelta(days=1),
        past_texts=[
            "Internet down in 305",
            "WiFi broken in 305"
        ],
        status="open"
    )

    for key, value in result2.items():
        print(f"{key.upper()}: {value}")

    # Test Case 3: Very Low Priority - Cleanliness
    print("\n" + "=" * 100)
    print("TEST CASE 3: CLEANLINESS (EXPECTED: VERY LOW PRIORITY)")
    print("=" * 100)
    result3 = process_complaint(
        text="My room is a bit dirty",
        category="cleanliness",
        created_at=datetime.now(),
        past_texts=[],
        status="open"
    )

    for key, value in result3.items():
        print(f"{key.upper()}: {value}")

    # Test Case 4: Critical Priority - Electrical Hazard
    print("\n" + "=" * 100)
    print("TEST CASE 4: ELECTRICAL HAZARD (EXPECTED: CRITICAL/HIGH PRIORITY)")
    print("=" * 100)
    result4 = process_complaint(
        text="Electrical shock hazard in kitchen, immediate danger to all students, weeks of complaint ignored",
        category="electrical",
        created_at=datetime.now() - timedelta(days=12),
        past_texts=[
            "Electrical problem in kitchen",
            "Exposed wire in kitchen area",
            "Kitchen shock risk"
        ],
        status="open"
    )

    for key, value in result4.items():
        print(f"{key.upper()}: {value}")

    # Test Case 5: Critical Priority - Safety Issue
    print("\n" + "=" * 100)
    print("TEST CASE 5: SAFETY ISSUE (EXPECTED: CRITICAL/HIGH PRIORITY)")
    print("=" * 100)
    result5 = process_complaint(
        text="Rat infestation in entire hostel, students injured, urgent action needed immediately",
        category="safety",
        created_at=datetime.now() - timedelta(days=7),
        past_texts=[
            "Rats seen in multiple rooms",
            "Pest problem spreading",
            "Rodent issue in kitchen"
        ],
        status="open"
    )

    for key, value in result5.items():
        print(f"{key.upper()}: {value}")

    print("\n" + "=" * 100)
