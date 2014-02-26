from decimal import Decimal
import datetime

from django.conf import settings
from django.db import models
from django.db.models import Max

from mezzanine.core.models import Slugged, RichText, TimeStamped
from mezzanine.core.fields import RichTextField

from lc_calc.utils.excel_functions import nper, pmt
from lc_calc.utils.email import send_email


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


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provides some methods
    to determine what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self._initial = self._dict

    @property
    def _dict(self):
        """
        Return the basic fields (no relations) and their values as a dictionary.
        """
        return {field.name: field.value_from_object(self) for field in self._meta.fields}

    @property
    def diff(self):
        d1 = self._initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        if self.has_changed:
            super(ModelDiffMixin, self).save(*args, **kwargs)
            self._initial = self._dict


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

DISCLOSURE_DEFAULT = """
<p>Our financial calculator tool will help you analyze your financial needs.
The results are based on our quantitative underwriting criteria and accuracy of the inputted data.
Though we strive to provide you with the most accurate results possible, actual results will be
dependent upon our full underwriting requirements by a qualified loan officer.
The calculations on this page do not assume that the company accepts any fiduciary duties.
The calculations provided should not be taken as financial, legal or tax advice.
Our underwriting criteria is subject to change without notice.</p>
"""


class LoanCompany(Slugged, RichText):
    """
    A loan company offers a set of loans.
    """
    logo = models.ImageField(upload_to='loan_company_logos', null=True, blank=True,
                             help_text='The logo image for the company (need to set a size - keep it small)')
    email = models.EmailField(help_text='This email will be used for reporting and communication so it is essential.')
    disclosure = RichTextField("Disclosure", default=DISCLOSURE_DEFAULT)

    class Meta:
        ordering = ['title']


class LoanAdditionType(models.Model):
    """
    The type of the addition
    """
    VALUE_INDEX_METHOD_NAME_CHOICES = (
        ('_get_value_index_loan_to_value', 'Loan to value'),
        ('_get_value_index_debt_to_income', 'Debt to income'),
        ('_get_value_index_year_of_collateral', 'Year of collateral'))
    loan_company = models.ForeignKey(LoanCompany)
    loan_type = models.ForeignKey(LoanType)
    name = models.CharField(max_length=64,
                            help_text="The name of this loan type.")
    value_index_method_name = models.CharField(max_length=128,
                                               choices=VALUE_INDEX_METHOD_NAME_CHOICES,
                                               default='_get_value_index_loan_to_value',
                                               help_text="Method used on LoanCalculation to lookup value_index")
    sum_in_rate_calculation = models.BooleanField(
        default=True, help_text='If true, this type will be added into the rate calculation')

    def __str__(self):
        vi_description = next((c[1] for c in self.VALUE_INDEX_METHOD_NAME_CHOICES
                               if c[0] == self.value_index_method_name))
        return "{} {} ({})".format(self.name, self.loan_company, vi_description)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.pk is None:
            # improve default for sum_in_rate_calculation
            if self.sum_in_rate_calculation is None and self.loan_type.name == "Maximum rate":
                self.sum_in_rate_calculation = False
        super().save(force_insert, force_update, using, update_fields)


class LoanAddition(models.Model):
    """
    Data lookup value for loan calculation
    """
    loan_company = models.ForeignKey(LoanCompany)
    loan_type = models.ForeignKey(LoanType)
    value_type = models.ForeignKey(LoanAdditionType)
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


class LoanCalculation(ModelDiffMixin, TimeStamped):
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
    estimated_collateral_value = CurrencyField(default=1000.00, null=True, blank=True)  # default set in save
    estimated_monthly_income = CurrencyField(null=True, blank=True,
                                             default=settings.DEFAULT_MONTHLY_INCOME)
    estimated_monthly_expenses = CurrencyField(null=True, blank=True,
                                               default=settings.DEFAULT_MONTHLY_EXPENSES)
    estimated_year_of_collateral = models.IntegerField(null=True, blank=True,
                                                       default=lambda: datetime.datetime.now().year)
    loan_amount = CurrencyField()
    monthly_term = models.IntegerField(default=60)
    maximum_term = models.IntegerField()
    rate = models.FloatField()  # calculated in save
    monthly_payment = CurrencyField()  # calculated in save

    def __str__(self):
        return "<{}: ${} / {}m>".format(self.id, self.loan_amount, self.monthly_term)


    @property
    def estimated_monthly_savings(self):
        if self.current_loan_monthly_payment:
            return self.current_loan_monthly_payment - self.monthly_payment
        else:
            return None

    @property
    def estimated_yearly_savings(self):
        if self.estimated_monthly_savings is not None:
            return self.estimated_monthly_savings * 12
        else:
            return None

    @property
    def current_loan_remaining_interest(self):
        if self.current_loan_balance and self.current_loan_monthly_payment:
            principle_value = self.current_loan_balance
            pmt = self.current_loan_monthly_payment
            remaining_term = self.current_loan_estimated_remaining_term
            return - (principle_value - (pmt * remaining_term))
        else:
            return None

    @property
    def loan_interest(self):
        principle_value = self.loan_amount
        pmt = self.monthly_payment
        remaining_term = self.monthly_term
        return - (principle_value - (pmt * remaining_term))

    @property
    def interest_savings(self):
        if self.current_loan_remaining_interest:
            return self.current_loan_remaining_interest - self.loan_interest

    def save(self, *args, **kwargs):
        self.calculate_current_loan_estimated_remaining_term()
        self.calculate_rate()
        self.calculate_maximum_term()
        if self.maximum_term < self.monthly_term:
            self.monthly_term = self.maximum_term
        self.calculate_monthly_payment()

        if self.has_changed:
            self.id = None
            kwargs['force_insert'] = True
            try:
                del kwargs['force_update']
            except KeyError:
                pass

        super().save(*args, **kwargs)

    def calculate_current_loan_estimated_remaining_term(self):
        if self.current_loan_balance and self.current_loan_monthly_payment and self.current_loan_rate:
            rate = self.current_loan_rate / 12.0
            pmt = -self.current_loan_monthly_payment
            pv = self.current_loan_balance
            self.current_loan_estimated_remaining_term = int(round(nper(rate, pmt, pv)))

    def calculate_rate(self):
        rate = 0.0
        credit_score = self.estimated_credit_score
        for value_type in LoanAdditionType.objects.filter(sum_in_rate_calculation=True,
                                                               loan_company=self.loan_company,
                                                               loan_type=self.loan_type):
            value_index = self.get_value_index(value_type)
            rate += self.get_addition(value_type, credit_score, value_index)
        self.rate = rate

    def calculate_maximum_term(self):
        value_type = LoanAdditionType.objects.get(name='Maximum term',
                                                  loan_company=self.loan_company,
                                                  loan_type=self.loan_type)
        credit_score = self.estimated_credit_score
        value_index = self.get_value_index(value_type)
        self.maximum_term = self.get_addition(value_type, credit_score, value_index)

    def get_value_index(self, value_type):
        return getattr(self, value_type.value_index_method_name)()

    def _get_value_index_loan_to_value(self):
        return Decimal(self.loan_amount / self.estimated_collateral_value) * Decimal(100.0)

    def _get_value_index_debt_to_income(self):
        return Decimal(self.estimated_monthly_expenses / self.estimated_monthly_income) * Decimal(100.0)

    def _get_value_index_year_of_collateral(self):
        return self.estimated_year_of_collateral

    def get_addition(self, value_type, credit_score, value_index):

        # Ensure that the upper bound of the indices is in range
        indices = {'credit_score': credit_score,
                   'value_index': value_index}
        for fname in indices:
            info = LoanAddition.objects.filter(loan_company=self.loan_company,
                                               loan_type=self.loan_type,
                                               value_type=value_type).aggregate(Max(fname))
            max_value = info['{}__max'.format(fname)]
            if max_value is None:
                import IPython; IPython.embed()
            if indices[fname] > max_value:
                indices[fname] = max_value

        loan_additions = LoanAddition.objects.filter(
            loan_company=self.loan_company,
            loan_type=self.loan_type,
            value_type=value_type,
            credit_score__gte=indices['credit_score'],
            value_index__gte=indices['value_index'])

        # As we've adjusted the bounds, we should always get at least one result unless the table is missing
        return loan_additions[0].value

    def calculate_monthly_payment(self):
        monthly_payment = pmt(self.rate / 12.0, self.monthly_term, -self.loan_amount)
        self.monthly_payment = Decimal(monthly_payment).quantize(Decimal('0.01'))


class LoanCompanyMessage(TimeStamped):
    """
    Loan contact email created when user submits filled in contact request.
    Email is sent when this is created.
    """
    loan_company = models.ForeignKey(LoanCompany, editable=False)
    loan_calculation = models.ForeignKey(LoanCalculation, null=True, editable=False)
    sender = models.EmailField(verbose_name="Your email address")
    message = models.TextField(max_length=1024, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        result = super().save(*args, **kwargs)
        if is_new:
            # Send the message
            subject = 'Information request from logicalc'
            to = [self.loan_company.email]
            context = {'loan_company': self.loan_company,
                       'msg': self}
            send_email(subject, to, 'lc_calc/email/company_message.html', context)
        return result




