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

    def test_calculation(self):

        loan_company = LoanCompany.objects.get(slug='acle-loans')
        loan_type_used = LoanType.objects.get(name="Used Vehicles")
        loan_type_new = LoanType.objects.get(name="New Vehicles")
        test_data = [
            ({'loan_company': loan_company,
              'loan_type': loan_type_used,
              'current_loan_balance': 6000.00,
              'current_loan_monthly_payment': 300.00,
              'current_loan_rate': 0.15,
              'estimated_credit_score': 750,
              'estimated_collateral_value': 15000.00,
              'estimated_monthly_income': 6000.00,
              'estimated_monthly_expenses': 4000.00,
              'estimated_year_of_collateral': 1899,
              'loan_amount': 10000.00,
              'monthly_term': 36},
             {'rate': 0.043,
              'maximum_term': 36,
              'current_loan_estimated_remaining_term': 23,
              'monthly_payment': 296.58,
              'estimated_monthly_savings': 3.42,
              'estimated_yearly_savings': 41.09}),
            ({'loan_company': loan_company,
              'loan_type': loan_type_new,
              'current_loan_balance': 6000.00,
              'current_loan_monthly_payment': 300.00,
              'current_loan_rate': 0.15,
              'estimated_credit_score': 750,
              'estimated_collateral_value': 15000.00,
              'estimated_monthly_income': 6000.00,
              'estimated_monthly_expenses': 4000.00,
              'estimated_year_of_collateral': 2014,
              'loan_amount': 10000.00,
              'monthly_term': 36},
             {'rate': 0.013,
              'maximum_term': 72,
              'current_loan_estimated_remaining_term': 23,
              'monthly_payment': 283.38,
              'estimated_monthly_savings': 16.62,
              'estimated_yearly_savings': 199.44})]

        for (params, all_desired) in test_data:
            loan_calculation = LoanCalculation(**params)
            loan_calculation.save()  # necessary to calculate
            for (attname, desired) in all_desired.items():
                actual = getattr(loan_calculation, attname)
                self.assertEqual(round(actual, 2), round(desired, 2))
