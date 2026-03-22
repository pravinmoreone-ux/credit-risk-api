import pytest

from credit_application import CreditApplication, EmploymentStatus, LoanPurpose

#
#
#
#

@pytest.fixture
def good_application():
    return CreditApplication(
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

@pytest.fixture
def high_rish_application():
    return CreditApplication(
        customer_id="C002",
        income=50000,
        loan_amount=40000,
        credit_score=520,
        employment_status=EmploymentStatus.SELF_EMPLOYED,
        age=28,
        loan_purpose=LoanPurpose.PERSONAL,
        existing_debts=15000,
        loan_term_months=36,
)

# --------------------------------------------------
# Validation tests
# --------------------------------------------------

def test_valid_application_creates_ok(good_application):
    assert good_application.customer_id == "C001"

def test_negative_income_raises_error():
    with pytest.raises(ValueError, match="Income must be positive"):
        CreditApplication("C003",-1000,500,700,
                          EmploymentStatus.EMPLOYED,30, LoanPurpose.PERSONAL)
        
def test_underage_applicant_raises_error():
    with pytest.raises(ValueError, match="18 or older"):
        CreditApplication("C004", 50000, 5000, 700,
            EmploymentStatus.EMPLOYED, 16, LoanPurpose.EDUCATION)
        
def test_invalid_credit_score_raises_error():
    with pytest.raises(ValueError, match="300 and 900"):
        CreditApplication("C005", 50000, 5000, 200,
            EmploymentStatus.EMPLOYED, 30, LoanPurpose.PERSONAL)

def test_unemployed_high_loan_raises_error():
    with pytest.raises(ValueError, match="UNEMPLOYED"):
        CreditApplication("C006", 40000, 80000, 650,
            EmploymentStatus.UNEMPLOYED, 28, LoanPurpose.PERSONAL)

def test_invalid_loan_term_raises_error():
    with pytest.raises(ValueError, match="6 and 360"):
        CreditApplication("C007", 50000, 10000, 700,
            EmploymentStatus.EMPLOYED, 30, LoanPurpose.PERSONAL,
            loan_term_months=400)
        


# --------------------------------------------------
# Property tests
# --------------------------------------------------


def test_debt_to_income_correct(good_application):
    assert round(good_application.debt_to_income, 2) == 0.21

def test_affordability_ratio_correct(good_application):
    assert good_application.affordability_ratio > 0

def test_monthly_payment_positive(good_application):
    assert good_application.monthly_payment_estimate > 0


# --------------------------------------------------
# Risk level tests — parametrize
# One test function runs 4 scenarios
# --------------------------------------------------


@pytest.mark.parametrize("score,loan,debts,expected", [
    (800, 20000, 5000,  "LOW"),
    (700, 30000, 10000, "MEDIUM"),
    (520, 40000, 15000, "HIGH"),
    (400, 45000, 20000, "REJECT"),
])

def test_risk_levels(score, loan, debts, expected):
    app = CreditApplication(
        customer_id="TEST",
        income=100000,
        loan_amount=loan,
        credit_score=score,
        employment_status=EmploymentStatus.EMPLOYED,
        age=30,
        loan_purpose=LoanPurpose.PERSONAL,
        existing_debts=debts,
    )
    assert app.risk_level == expected


# --------------------------------------------------
# from_dict test
# --------------------------------------------------

def test_from_dict_creates_correctly():
    data = {
        "customer_id": "C010",
        "income": "80000",
        "loan_amount": "20000",
        "credit_score": "720",
        "employment_status": "employed",
        "age": "32",
        "loan_purpose": "home",
        "existing_debts": "5000",
        "loan_term_months": "24",
    }
    app = CreditApplication.from_dict(data)
    assert app.customer_id == "C010"
    assert app.risk_level in ["LOW", "MEDIUM", "HIGH", "REJECT"]

def test_to_dict_contains_all_keys(good_application):
    result = good_application.to_dict()
    assert "customer_id" in result
    assert "risk_level" in result
    assert "debt_to_income" in result
    assert "monthly_payment_estimate" in result

