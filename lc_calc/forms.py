from decimal import Decimal

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from lc_calc.models import LoanCalculation, LoanCompany


class PercentInput(forms.TextInput):
    def render(self, name, value, attrs=None):
        result = super(PercentInput, self).render(name, value, attrs)
        return mark_safe("{}%".format(result))


class PercentageField(forms.DecimalField):
    default_error_messages = {
        'positive': _(u'Must be a positive number.')}

    def prepare_value(self, value):
        # On error recovery the value comes in as an already prepared string which is wierd
        if isinstance(value, Decimal):
            value *= 100
        return super().prepare_value(value)

    def clean(self, value):
        value = super().clean(value)
        if value is not None:
            if value < 0:
                raise forms.ValidationError(self.error_messages['positive'])
            value = Decimal(value / 100)
        return value


class LoanCalculationForm(forms.ModelForm):
    loan_company_id = forms.IntegerField(widget=forms.HiddenInput)
    current_loan_rate = PercentageField(widget=PercentInput(attrs={'size': 4}))

    class Meta:
        model = LoanCalculation
        fields = ['loan_type',
                  'current_loan_balance',
                  'current_loan_monthly_payment',
                  'current_loan_rate',
                  'estimated_credit_score',
                  'estimated_collateral_value',
                  'estimated_monthly_income',
                  'estimated_monthly_expenses',
                  'estimated_year_of_collateral',
                  'loan_amount',
                  'monthly_term']

    def clean(self):
        """
        The current loan figures could lead to infinite value issues.
        This method checks the entries in combination to ensure that they are reasonable.
        """
        cleaned_data = super().clean()
        attnames = ('current_loan_balance',
                    'current_loan_monthly_payment',
                    'current_loan_rate')

        # If supplied, they must be greater than zero
        all_good = True
        for attname in attnames:
            value = cleaned_data.get(attname)
            if value is None:
                all_good = False
            elif value < 0:
                all_good = False
                self._errors[attname] = self.error_class([_('must be greater than zero')])
                del cleaned_data[attname]

        # If all supplied, the loan must terminate (pmt > pv * (interest / 12)
        if all_good:
            pmt = cleaned_data['current_loan_monthly_payment']
            pv = cleaned_data['current_loan_balance']
            rate = cleaned_data['current_loan_rate']
            if pmt <= (rate / 12) * pv:
                self._errors['current_loan_monthly_payment'] = self.error_class(
                    [_('is too small to ever pay the loan off')])
                del cleaned_data['current_loan_monthly_payment']
        return cleaned_data

    def save(self, commit=True):
        loan_company = LoanCompany.objects.get(pk=self.cleaned_data.get('loan_company_id'))
        self.instance.loan_company = loan_company
        return super().save(commit)

