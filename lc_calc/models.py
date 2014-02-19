from decimal import Decimal
import datetime

from django.conf import settings
from django.db import models
from mezzanine.core.models import Slugged, RichText, TimeStamped
from mezzanine.utils.urls import slugify

from lc_calc.utils.excel_functions import nper


class CurrencyField(models.DecimalField):
    """
    Currency as a number with two decimal places (from
    http://stackoverflow.com/questions/2013835/django-how-should-i-store-a-money-value)
    """
    __metaclass__ = models.SubfieldBase

    def __init__(self, verbose_name=None, name=None, **kwargs):
        decimal_places = kwargs.pop('decimal_places', 2)
        max_digits = kwargs.pop('max_digits', 10)

        super(CurrencyField, self).__init__(
            verbose_name=verbose_name, name=name, max_digits=max_digits,
            decimal_places=decimal_places, **kwargs)

    def to_python(self, value):
        try:
            return super(CurrencyField, self).to_python(value).quantize(Decimal("0.01"))
        except AttributeError:
            return None


class Named(models.Model):
    name = models.CharField(max_length=64, unique=True,
                            help_text="The name of this object (must be unique).")

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name


class LoanType(Named):
    pass


class LoanCompany(Slugged, RichText):
    """
    A loan company offers a set of loans.
    """
    logo = models.ImageField(upload_to='loan_company_logos', null=True, blank=True,
                             help_text='The logo image for the company (need to set a size - keep it small)')

    class Meta:
        ordering = ['title']


class LoanAdditionValueType(Named):
    """
    The type of the addition
    """
    VALUE_INDEX_METHOD_NAME_CHOICES = (
        ('_get_value_index_loan_to_value', 'Loan to value'),
        ('_get_value_index_debt_to_income', 'Debt to income'),
        ('_get_value_index_year_of_collateral', 'Year of collateral'))
    value_index_method_name = models.CharField(max_length=128,
                                               choices=VALUE_INDEX_METHOD_NAME_CHOICES,
                                               default='_get_value_index_loan_to_value',
                                               help_text="Method used on LoanCalculation to lookup value_index")
    sum_in_rate_calculation = models.BooleanField(default=True)

    def __str__(self):
        vi_description = next((c[1] for c in self.VALUE_INDEX_METHOD_NAME_CHOICES if c[0] == self.value_index_method_name))
        return "{} ({})".format(super().__str__(), vi_description)


class LoanAddition(models.Model):
    """
    Data lookup value for loan calculation
    """
    loan_company = models.ForeignKey(LoanCompany)
    loan_type = models.ForeignKey(LoanType)
    value_type = models.ForeignKey(LoanAdditionValueType)
    credit_score = models.IntegerField(help_text="The minimum credit score for which this value is applicable.")
    value_index = models.IntegerField(help_text="The Addition lookup value (sheet column value).")
    value = models.FloatField(help_text="The value to use in the calculation.")

    class Meta:
        ordering = ['loan_company__title',
                    'loan_type__name',
                    'value_type__name',
                    'credit_score',
                    'value_index']

    def __str__(self):
        return "{} | {} | {} | {} | {} | {} |".format(self.loan_company,
                                                      self.loan_type,
                                                      self.value_type,
                                                      self.value_index,
                                                      self.credit_score,
                                                      self.value)


class LoanCalculation(TimeStamped):
    """
    User entered data and resulting calculation.
    """
    loan_company = models.ForeignKey(LoanCompany)
    loan_type = models.ForeignKey(LoanType)
    current_loan_balance = CurrencyField(null=True, blank=True)
    current_loan_monthly_payment = CurrencyField(null=True, blank=True)
    current_loan_rate = models.FloatField(null=True, blank=True)
    current_loan_estimated_remaining_term = models.IntegerField(null=True, blank=True)  # calculated in save
    estimated_credit_score = models.IntegerField(default=850, blank=True)
    estimated_collateral_value = CurrencyField(null=True, blank=True)  # default set in save
    estimated_monthly_income = CurrencyField(null=True, blank=True,
                                             default=settings.DEFAULT_MONTHLY_INCOME)
    estimated_monthly_expenses = CurrencyField(null=True, blank=True,
                                               default=settings.DEFAULT_MONTHLY_EXPENSES)
    estimated_year_of_collateral = models.IntegerField(null=True, blank=True,
                                                       default=lambda: datetime.datetime.now().year)
    loan_amount = CurrencyField()
    monthly_term = models.IntegerField()
    rate = models.FloatField()  # calculated in save

    def save(self, *args, **kwargs):
        if self.estimated_collateral_value is None:
            self.estimated_collateral_value = self.loan_amount * settings.LOAN_AMOUNT_TO_COLLATERAL_VALUE
        self.calculate_current_loan_estimated_remaining_term()
        self.calculate_rate()
        super().save(*args, **kwargs)

    def calculate_current_loan_estimated_remaining_term(self):
        if self.current_loan_balance and self.current_loan_monthly_payment and self.current_loan_rate:
            rate = self.current_loan_rate / 12.0
            pmt = -self.current_loan_monthly_payment
            pv = self.current_loan_balance
            self.current_loan_estimated_remaining_term = nper(rate, pmt, pv)

    def calculate_rate(self):
        rate = 0.0
        credit_score = self.estimated_credit_score
        for value_type in LoanAdditionValueType.objects.all():
            if value_type.sum_in_rate_calculation:
                value_index = getattr(self, value_type.value_index_method_name)()
                rate += self.get_rate_addition(value_type, credit_score, value_index)
        self.rate = rate

    def _get_value_index_loan_to_value(self):
        return (self.loan_amount / self.estimated_collateral_value) * 100.0

    def _get_value_index_debt_to_income(self):
        return (self.estimated_monthly_expenses / self.estimated_monthly_income) * 100.0

    def _get_value_index_year_of_collateral(self):
        return self.estimated_year_of_collateral

    def get_rate_addition(self, value_type, credit_score, value_index):
        loan_additions = LoanAddition.objects.filter(
            loan_company=self.loan_company,
            loan_type=self.loan_type,
            value_type=value_type,
            credit_score__gte=credit_score,
            value_index__gte=value_index)
        if len(loan_additions):
            return loan_additions[0].value
        else:
            return 0.0
