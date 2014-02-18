"""
The Excel functions we need in python.
"""
from math import log10


def nper(rate, pmt, pv):
    """
    Returns the number of periods for an investment based on periodic, constant payments and a constant interest rate.
    - rate: The interest reate per period.
    - pmt: The payment made each period; it cannot change over the life of the annuity.
    Typically, pmt contains principle and interest but no other fees or taxes.
    - pv: The present value, or the lump-sum amount that a series of future payments is worth right now.
    The future value, or a cash balance is 0.
    Payments are assumed to be made at the end of the period.
    """
    return log10(pmt/(pmt + pv*rate))/log10(1 + rate)