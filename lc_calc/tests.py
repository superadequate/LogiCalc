from django.test import TestCase

from lc_calc.utils.excel_functions import nper
from lc_calc.models import LoanCompany, LoanType, LoanCalculation


class TestExcelFunctions(TestCase):

    def test_nper(self):
        """
        Test nper using values from excel conversions spreadsheet.
        """
        # 12% is 1% per month (0.01)
        test_data = [
            ({'rate': 0.01, 'pmt': -200, 'pv': 10000}, 69.6607168936),
            ({'rate': 0.01, 'pmt': -300, 'pv': 10000}, 40.7489071561),
            ({'rate': 0.01, 'pmt': -500, 'pv': 10000}, 22.425741878),
            ({'rate': 0.01, 'pmt': -10100, 'pv': 10000}, 1.0)]
        for (params, desired) in test_data:
            actual = nper(**params)
            self.assertAlmostEqual(actual, desired)


class TestCalculations(TestCase):
    """
    Test calculations using test data
    """
    fixtures = ['test_loancompanies.json',
                'test_loantypes.json',
                'test_loanadditionvaluetypes.json',
                'test_loanadditions.json']

    def test_rate_calculation(self):
        loan_company = LoanCompany.objects.get(slug='acle-loans')
        loan_type_used = LoanType.objects.get(name="Used Vehicles")
        loan_type_new = LoanType.objects.get(name="New Vehicles")
        test_data = [
            ({'loan_company': loan_company,
              'loan_type': loan_type_used,
              'estimated_credit_score': 750,
              'estimated_collateral_value': 15000.00,
              'estimated_monthly_income': 6000.00,
              'estimated_monthly_expenses': 4000.00,
              'estimated_year_of_collateral': 2008,
              'loan_amount': 10000.00,
              'monthly_term': 48}, 0.033),
            ({'loan_company': loan_company,
              'loan_type': loan_type_new,
              'estimated_credit_score': 750,
              'estimated_collateral_value': 15000.00,
              'estimated_monthly_income': 6000.00,
              'estimated_monthly_expenses': 4000.00,
              'estimated_year_of_collateral': 2008,
              'loan_amount': 10000.00,
              'monthly_term': 48}, 0.023)]
        for (params, desired) in test_data:
            loan_calculation = LoanCalculation(**params)
            loan_calculation.save()  # necessary to calculate rate
            actual = loan_calculation.rate
            import IPython; IPython.embed()
            self.assertAlmostEqual(actual, desired)

    def test_estimate_remaining_term(self):
        self.fail('not implemented')