"""
Synthetic Indian Banking Data Generator v2.0
Generates high-quality synthetic data tuned to Indian contexts.
"""

import numpy as np
import pandas as pd
import hashlib
import string

INDIAN_FIRST_NAMES = {
    "Male": [
        "Aarav", "Vihaan", "Arjun", "Aditya", "Rohit", "Ravi", "Suresh", "Ramesh",
        "Vikram", "Amit", "Rahul", "Sanjay", "Pradeep", "Mahesh", "Vinod", "Rajesh",
        "Deepak", "Sunil", "Naveen", "Sachin", "Yusuf", "Iqbal", "Salim", "Farhan",
        "David", "Joseph", "Thomas", "Matthew", "Gurpreet", "Harpreet", "Manpreet",
        "Rajendra", "Shivam", "Kiran", "Ajay", "Vijay", "Siddharth", "Kunal",
    ],
    "Female": [
        "Priya", "Anjali", "Neha", "Pooja", "Ananya", "Divya", "Kavya", "Shreya",
        "Isha", "Riya", "Sunita", "Geeta", "Lakshmi", "Meena", "Radha", "Sita",
        "Fatima", "Ayesha", "Zara", "Amira", "Mary", "Grace", "Preethi", "Manisha",
        "Rekha", "Usha", "Shobha", "Kavitha", "Swati", "Deepa", "Nandini", "Pallavi",
    ],
}

SURNAMES_BY_RELIGION = {
    "Hindu": ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Joshi", "Rao", "Nair",
              "Iyer", "Menon", "Pillai", "Reddy", "Chowdhury", "Mukherjee", "Chatterjee",
              "Tiwari", "Pandey", "Mishra", "Dubey", "Yadav", "Patil", "Desai", "Shah"],
    "Muslim": ["Khan", "Ali", "Sheikh", "Ansari", "Qureshi", "Siddiqui", "Mirza",
               "Ahmed", "Hassan", "Hussain", "Patel", "Shaikh", "Malik", "Chaudhary"],
    "Christian": ["D'Souza", "Fernandes", "Pereira", "Rodrigues", "Mathew", "Thomas",
                   "George", "Philip", "Abraham", "Joseph", "John", "Varghese", "Chacko"],
    "Sikh": ["Singh", "Kaur", "Dhaliwal", "Sandhu", "Gill", "Brar", "Sidhu", "Grewal", "Randhawa"],
    "Buddhist": ["Negi", "Lama", "Tamang", "Gurung", "Thapa", "Sherpa", "Rai", "Limbu"],
    "Jain": ["Jain", "Shah", "Mehta", "Sheth", "Doshi", "Sanghvi", "Kothari", "Parekh"],
    "Other": ["Bora", "Saikia", "Hazarika", "Gogoi", "Das", "Dey", "Bose", "Sen"],
}

CITIES_BY_TIER = {
    1: ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Pune", "Ahmedabad"],
    2: ["Jaipur", "Surat", "Nagpur", "Lucknow", "Kanpur", "Indore", "Bhopal", "Patna",
        "Vadodara", "Ludhiana", "Agra", "Nashik", "Visakhapatnam", "Coimbatore", "Kochi"],
    3: ["Shimla", "Dehradun", "Guwahati", "Ranchi", "Raipur", "Bhubaneswar", "Jodhpur",
        "Madurai", "Mysore", "Varanasi", "Meerut", "Amritsar", "Jabalpur", "Aurangabad",
        "Solapur", "Tiruchirappalli", "Aligarh", "Bhilai", "Gorakhpur", "Bikaner"],
}

RELIGION_WEIGHTS = [0.79, 0.14, 0.024, 0.017, 0.007, 0.004, 0.018]
RELIGIONS = ["Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain", "Other"]

EDUCATION_LEVELS = ["Below 10th", "10th Pass", "12th Pass", "Graduate", "Post-Graduate", "Professional"]
EMPLOYMENT_TYPES = ["Salaried", "Self-Employed", "Business", "Farmer", "Daily-Wage", "Unemployed"]


def _make_applicant_id(seed_str: str) -> str:
    return "IND" + hashlib.md5(seed_str.encode()).hexdigest()[:7].upper()


def generate_synthetic_data(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records = []

    for i in range(n_samples):
        # Demographics
        gender = rng.choice(["Male", "Female", "Other"], p=[0.52, 0.47, 0.01])
        religion = rng.choice(RELIGIONS, p=RELIGION_WEIGHTS)
        city_tier = rng.choice([1, 2, 3], p=[0.28, 0.42, 0.30])
        city = rng.choice(CITIES_BY_TIER[city_tier])
        age = int(np.clip(rng.normal(35, 9), 21, 65))

        first_name = rng.choice(INDIAN_FIRST_NAMES.get(gender, INDIAN_FIRST_NAMES["Male"]))
        surname = rng.choice(SURNAMES_BY_RELIGION.get(religion, ["Kumar"]))
        full_name = f"{first_name} {surname}"

        education = rng.choice(EDUCATION_LEVELS, p=[0.05, 0.12, 0.20, 0.38, 0.18, 0.07])
        employment = rng.choice(EMPLOYMENT_TYPES, p=[0.42, 0.22, 0.15, 0.10, 0.08, 0.03])

        # Income varies by tier, gender, education
        base_income = {1: 55000, 2: 35000, 3: 20000}[city_tier]
        gender_mult = {"Male": 1.0, "Female": 0.78, "Other": 0.85}[gender]
        edu_mult = {"Below 10th": 0.6, "10th Pass": 0.75, "12th Pass": 0.85,
                    "Graduate": 1.0, "Post-Graduate": 1.35, "Professional": 1.70}[education]
        emp_mult = {"Salaried": 1.0, "Self-Employed": 1.15, "Business": 1.30,
                    "Farmer": 0.55, "Daily-Wage": 0.45, "Unemployed": 0.20}[employment]

        monthly_income = max(5000, int(rng.normal(
            base_income * gender_mult * edu_mult * emp_mult,
            base_income * 0.30
        )))

        # CIBIL score
        cibil_base = 680
        cibil_income_boost = min((monthly_income - 20000) / 2000, 80)
        cibil_score = int(np.clip(
            rng.normal(cibil_base + cibil_income_boost, 70), 300, 900
        ))

        # Loan details
        loan_mult = {"Home": 36, "Personal": 8, "Education": 18, "Vehicle": 24, "Business": 20}
        loan_type = rng.choice(list(loan_mult.keys()), p=[0.35, 0.30, 0.15, 0.12, 0.08])
        loan_amount = int(np.clip(
            rng.lognormal(np.log(monthly_income * loan_mult[loan_type] * 0.8), 0.5),
            50000, 10000000
        ))

        # DTI, credit history, existing loans, late payments
        existing_loans = max(0, int(rng.poisson(1.2)))
        credit_history_years = max(0, int(rng.normal(age - 23, 4)))
        num_late_payments = max(0, int(rng.poisson(0.8 + (1 - cibil_score/900) * 3)))
        debt_to_income_ratio = round(
            (loan_amount / 12 + existing_loans * 3000) / max(monthly_income, 1000), 3
        )

        # ── BIASED MODEL SCORE (simulates discriminatory model) ──
        score = 50.0
        # Financial features
        score += (cibil_score - 650) * 0.08
        score += (monthly_income - 35000) / 3000
        score -= debt_to_income_ratio * 10
        score -= num_late_payments * 3
        score += credit_history_years * 0.5
        score -= existing_loans * 2

        # BIAS INJECTION
        if gender == "Female":
            score -= 7.5   # direct gender bias
        if gender == "Other":
            score -= 12.0

        if religion == "Muslim":
            score -= 5.0   # religious discrimination
        elif religion == "Christian":
            score -= 3.0
        elif religion in ("Buddhist", "Other"):
            score -= 2.0

        if city_tier == 3:
            score -= 6.0   # geography as caste proxy
        elif city_tier == 2:
            score -= 2.5

        # Noise
        score += rng.normal(0, 4)
        score = float(np.clip(score, 0, 100))
        model_approved = 1 if score > 55 else 0

        # ── FAIR MODEL (based on financial features only) ──
        fair_score = 50.0
        fair_score += (cibil_score - 650) * 0.09
        fair_score += (monthly_income - 35000) / 2800
        fair_score -= debt_to_income_ratio * 9
        fair_score -= num_late_payments * 3.5
        fair_score += credit_history_years * 0.6
        fair_score -= existing_loans * 1.8
        fair_score += rng.normal(0, 3)
        fair_score = float(np.clip(fair_score, 0, 100))
        fair_approved = 1 if fair_score > 52 else 0

        records.append({
            "applicant_id": _make_applicant_id(f"{seed}_{i}"),
            "full_name": full_name,
            "gender": gender,
            "religion": religion,
            "city_tier": city_tier,
            "city": city,
            "age": age,
            "education": education,
            "employment_type": employment,
            "cibil_score": cibil_score,
            "monthly_income": monthly_income,
            "loan_type": loan_type,
            "loan_amount": loan_amount,
            "existing_loans": existing_loans,
            "credit_history_years": credit_history_years,
            "num_late_payments": num_late_payments,
            "debt_to_income_ratio": debt_to_income_ratio,
            "model_score": round(score, 2),
            "model_approved": model_approved,
            "fair_score": round(fair_score, 2),
            "fair_approved": fair_approved,
        })

    return pd.DataFrame(records)
