"""
The Excel functions we need in python.

From http://www.pcreview.co.uk/forums/real-math-behind-pmt-and-ipmt-function-t2799164.html
To solve for the future value, the formula is:
fv=-if(rate=0,pmt*nper+pv,(pv*((1+rate)^nper)+pmt*(1+rate*type)*((1+rate)^nper
-1)/rate))

To solve for the present value, the formula is:
pv=-if(rate=0,pmt*nper+fv,(fv+pmt*(1+rate*type)*((1+rate)^nper-1)/rate)/((1+ra
te)^nper))

To solve for the payment value, the formula is:
pmt=-if(rate=0,(pv+fv)/nper,(pv*((1+rate)^nper)+fv)/((1+rate*type)*((1+rate)^n
per-1)/rate))

To solve for the number of periods, the formula is:
nper=-if(rate=0,(pv+fv)/pmt,(log(1+(pv+pmt*type)/pmt*rate)-log(1+(fv+pmt*type)
/pmt*rate))/log(1+rate))

To solve for the interest rate, the formula is:
rate=(fv/pv)^(1/nper)-1
if pmt is 0. Otherwise, you can only solve for the interest rate through
iteration (eg using one of the above formulae).

The fv, pv, pmt, nper and rate variables are explained in Excel's Help on PV.

Functions like ipmt are variations on the above, as also described in Excel's
Help file.
"""
from math import log10


def nper(rate, pmt, pv):
    """
    Returns the number of periods for an investment based on periodic, constant payments and a constant interest rate.
    - rate: The interest rate per period.
    - pmt: The payment made each period; it cannot change over the life of the annuity.
    Typically, pmt contains principle and interest but no other fees or taxes.
    - pv: The present value, or the lump-sum amount that a series of future payments is worth right now.
    The future value, or a cash balance is 0.
    Payments are assumed to be made at the end of the period.
    """
    return log10(pmt/(pmt + pv*rate))/log10(1 + rate)


def pmt(rate, nperiods, pv, fv=0, pmt_type=0):
    """
    Returns the periodic payment for an annuity with constant interest rates.
    - rate: The interest rate per period.
    - nperiods: The number of periods in which the annuity is paid
    - pv: The present value (cash value)
    - fv: The future value (defaults to 0)
    - pmt_type: 1 for payments at the beginning of the period, 0 at the end of the period (defaults to 0)

    pmt=-if(rate=0,(pv+fv)/nper,(pv*((1+rate)^nper)+fv)/((1+rate*type)*((1+rate)^n
per-1)/rate))
    """
    if rate == 0:
        result = (pv + fv) / nperiods
    else:
        result = (pv * ((1 + rate)**nperiods) + fv)/((1 + rate * pmt_type) * ((1 + rate)**nperiods - 1) / rate)
    return - result