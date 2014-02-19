from django.test import TestCase

from lc_calc.utils.excel_functions import nper, pmt
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

    def test_pmt(self):
        """
        Test nper using values from excel conversions spreadsheet.
        """
        # 12% is 1% per month (0.01)
        test_data = [
            ({'rate': 0.01, 'nperiods': 1, 'pv': -100, 'fv': 0, 'pmt_type': 1}, 100.0),
            ({'rate': 0.01, 'nperiods': 1, 'pv': -100, 'fv': 0, 'pmt_type': 0}, 101.0),
            ({'rate': 0.02, 'nperiods': 12, 'pv': -12000, 'fv': 0, 'pmt_type': 0}, 1134.71515948),
            ({'rate': 0.0, 'nperiods': 10, 'pv': 0, 'fv': 10000, 'pmt_type': 1}, -1000.0),
            ({'rate': 0.01, 'nperiods': 10, 'pv': 0, 'fv': 10000, 'pmt_type': 1}, -946.35719358)]
        for (params, desired) in test_data:
            actual = pmt(**params)
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
            self.assertAlmostEqual(actual, desired)

    def test_maximum_term(self):

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
              'estimated_year_of_collateral': 1899,
              'loan_amount': 10000.00,
              'monthly_term': 48}, 36),
            ({'loan_company': loan_company,
              'loan_type': loan_type_new,
              'estimated_credit_score': 750,
              'estimated_collateral_value': 15000.00,
              'estimated_monthly_income': 6000.00,
              'estimated_monthly_expenses': 4000.00,
              'estimated_year_of_collateral': 2008,
              'loan_amount': 10000.00,
              'monthly_term': 48}, 60)]

        for (params, desired) in test_data:
            loan_calculation = LoanCalculation(**params)
            loan_calculation.save()  # necessary to calculate rate
            actual = loan_calculation.maximum_term
            self.assertAlmostEqual(actual, desired)