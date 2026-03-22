from dataclasses import dataclass
from typing import Optional
from enum import Enum


# ------------------------------------------------------------------
# Enums — fixed set of allowed values
# BPM parallel: like a Choice List in IBM BAW
# ------------------------------------------------------------------

class EmploymentStatus(Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"


class LoanPurpose(Enum):
    HOME = "home"
    VEHICLE = "vehicle"
    EDUCATION = "education"
    PERSONAL = "personal"
    BUSINESS = "business"
    MEDICAL = "medical"


# ------------------------------------------------------------------
# CreditApplication dataclass
# BPM parallel: like a Business Object in IBM BAW
# Each field = one process variable
# ------------------------------------------------------------------

@dataclass
class CreditApplication:
    customer_id: str
    income: float
    loan_amount: float
    credit_score: int
    employment_status: EmploymentStatus
    age: int
    loan_purpose: LoanPurpose
    existing_debts: float = 0.0
    loan_term_months: int = 12

    # --------------------------------------------------------------
    # __post_init__ runs automatically after object is created
    # This is your validation gate — like an ODM pre-condition
    # --------------------------------------------------------------

    def __post_init__(self):
        if not self.customer_id or not self.customer_id.strip():
            raise ValueError("customer_id cannot be empty")

        if self.income <= 0:
            raise ValueError(f"Income must be positive, got {self.income}")

        if self.loan_amount <= 0:
            raise ValueError(f"Loan amount must be positive, got {self.loan_amount}")

        if not 300 <= self.credit_score <= 900:
            raise ValueError(
                f"Credit score must be between 300 and 900, got {self.credit_score}"
            )

        if self.age < 18:
            raise ValueError(f"Applicant must be 18 or older, got {self.age}")

        if self.existing_debts < 0:
            raise ValueError(f"Existing debts cannot be negative, got {self.existing_debts}")

        if not 6 <= self.loan_term_months <= 360:
            raise ValueError(
                f"Loan term must be between 6 and 360 months, got {self.loan_term_months}"
            )

        if self.loan_amount > self.income * 10:
            raise ValueError(
                f"Loan amount {self.loan_amount} cannot exceed 10x annual income {self.income}"
            )

        if self.employment_status == EmploymentStatus.UNEMPLOYED and self.loan_amount > 50000: 
            raise ValueError(
                f"Loan amount {self.loan_amount} is rejected as person is UNEMPLOYED and amount is more than 50000"
            )
    # --------------------------------------------------------------
    # Properties — computed fields, not stored
    # BPM parallel: derived process variables in BAW
    # --------------------------------------------------------------

    @property
    def debt_to_income(self) -> float:
        """Total debt burden as ratio of income.
        SR 11-7 key metric — regulators require this in credit models."""
        return (self.existing_debts + self.loan_amount) / self.income

    @property
    def loan_to_income(self) -> float:
        """Requested loan as ratio of annual income."""
        return self.loan_amount / self.income

    @property
    def risk_level(self) -> str:
        """Rule-based risk classification.
        BPM parallel: exactly like an IBM ODM decision table.
        LOW / MEDIUM / HIGH maps to credit decision outcomes."""
        if self.credit_score >= 750 and self.debt_to_income < 0.3:
            return "LOW"
        elif self.credit_score >= 650 and self.debt_to_income < 0.5:
            return "MEDIUM"
        elif self.credit_score >= 500 and self.debt_to_income < 0.7:
            return "HIGH"
        else:
            return "REJECT"

    @property
    def monthly_payment_estimate(self) -> float:
        """Simple loan EMI estimate (flat rate approximation)."""
        monthly_rate = 0.10 / 12  # assuming 10% annual interest
        n = self.loan_term_months
        if monthly_rate == 0:
            return self.loan_amount / n
        emi = self.loan_amount * monthly_rate * (1 + monthly_rate) ** n
        emi = emi / ((1 + monthly_rate) ** n - 1)
        return round(emi, 2)
    
    @property
    def affordability_ratio(self) -> float:
        """Monthly EMI as percentage of monthly income.
        Above 40% means financially stressed."""
        monthly_income = self.income / 12
        return round((self.monthly_payment_estimate / monthly_income) * 100, 2)

    # --------------------------------------------------------------
    # Class methods — alternative constructors
    # BPM parallel: service task that maps incoming JSON to BO
    # --------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "CreditApplication":
        """Create a CreditApplication from a raw dictionary.
        Used when data comes in from a REST API or CSV row."""
        return cls(
            customer_id=str(data["customer_id"]),
            income=float(data["income"]),
            loan_amount=float(data["loan_amount"]),
            credit_score=int(data["credit_score"]),
            employment_status=EmploymentStatus(data["employment_status"]),
            age=int(data["age"]),
            loan_purpose=LoanPurpose(data["loan_purpose"]),
            existing_debts=float(data.get("existing_debts", 0.0)),
            loan_term_months=int(data.get("loan_term_months", 12)),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary — used when sending to ML model or logging."""
        return {
            "customer_id": self.customer_id,
            "income": self.income,
            "loan_amount": self.loan_amount,
            "credit_score": self.credit_score,
            "employment_status": self.employment_status.value,
            "age": self.age,
            "loan_purpose": self.loan_purpose.value,
            "existing_debts": self.existing_debts,
            "loan_term_months": self.loan_term_months,
            "debt_to_income": self.debt_to_income,
            "loan_to_income": self.loan_to_income,
            "risk_level": self.risk_level,
            "monthly_payment_estimate": self.monthly_payment_estimate,
        }

    def __str__(self) -> str:
        return (
            f"CreditApplication("
            f"id={self.customer_id}, "
            f"risk={self.risk_level}, "
            f"dti={self.debt_to_income:.2f}, "
            f"emi=₹{self.monthly_payment_estimate:,.2f})"
        )


# ------------------------------------------------------------------
# Manual test — run this file directly to verify it works
# python credit_application.py
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("--- Test 1: Valid LOW risk application ---")
    app1 = CreditApplication(
        customer_id="C001",
        income=120000,
        loan_amount=20000,
        credit_score=800,
        employment_status=EmploymentStatus.EMPLOYED,
        age=35,
        loan_purpose=LoanPurpose.HOME,
        existing_debts=5000,
        loan_term_months=24,
    )
    print(app1)
    print(f"  Risk level     : {app1.risk_level}")
    print(f"  Debt-to-income : {app1.debt_to_income:.2f}")
    print(f"  Monthly EMI    : ₹{app1.monthly_payment_estimate:,.2f}")
    print(f"  As dict        : {app1.to_dict()}")

    print("\n--- Test 2: from_dict (simulating API input) ---")
    raw_data = {
        "customer_id": "C002",
        "income": "80000",
        "loan_amount": "50000",
        "credit_score": "620",
        "employment_status": "self_employed",
        "age": "42",
        "loan_purpose": "business",
        "existing_debts": "10000",
        "loan_term_months": "36",
    }
    app2 = CreditApplication.from_dict(raw_data)
    print(app2)
    print(f"  Risk level     : {app2.risk_level}")

    print("\n--- Test 3: Invalid application (should raise error) ---")
    try:
        bad_app = CreditApplication(
            customer_id="C003",
            income=-5000,
            loan_amount=10000,
            credit_score=700,
            employment_status=EmploymentStatus.EMPLOYED,
            age=25,
            loan_purpose=LoanPurpose.PERSONAL,
        )
    except ValueError as e:
        print(f"  Caught expected error: {e}")

    print("\n--- Test 4: Underage applicant ---")
    try:
        bad_app2 = CreditApplication(
            customer_id="C004",
            income=50000,
            loan_amount=10000,
            credit_score=700,
            employment_status=EmploymentStatus.EMPLOYED,
            age=16,
            loan_purpose=LoanPurpose.EDUCATION,
        )
    except ValueError as e:
        print(f"  Caught expected error: {e}")

    print("\nAll manual tests completed.")


    print("\n--- Test 5: Unemployed high loan ---")
try:
    bad_app3 = CreditApplication(
        customer_id="C005",
        income=40000,
        loan_amount=80000,
        credit_score=650,
        employment_status=EmploymentStatus.UNEMPLOYED,
        age=28,
        loan_purpose=LoanPurpose.PERSONAL,
    )
except ValueError as e:
    print(f"  Caught expected error: {e}")

print("\n--- Test 6: Affordability ratio ---")
app3 = CreditApplication(
    customer_id="C006",
    income=60000,
    loan_amount=30000,
    credit_score=700,
    employment_status=EmploymentStatus.EMPLOYED,
    age=30,
    loan_purpose=LoanPurpose.MEDICAL,
    loan_term_months=36,
)
print(f"  Affordability ratio: {app3.affordability_ratio}%")
print(f"  Stressed? : {'YES' if app3.affordability_ratio > 40 else 'NO'}")

'''
Run it — you should see:
'''