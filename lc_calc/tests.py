from django.test import TestCase

from lc_calc.utils.excel_functions import nper


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