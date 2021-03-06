from django import forms
from django.forms.util import ErrorList
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from lc_calc.models import LoanCalculation, LoanCompany, LoanType


class PercentInput(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, (str, bytes)):
            value *= 100.0
        result = super(PercentInput, self).render(name, value, attrs)
        return mark_safe("{}%".format(result))


class PercentageField(forms.FloatField):
    default_error_messages = {
        'positive': _(u'Must be a positive number.')}

    def to_python(self, value):
        if value and isinstance(value, (str, bytes)):
            value = value.strip()
            if value[-1] == '%':
                value = value[0:-1]
        value = super().to_python(value)
        if value:
            return value / 100.0
        else:
            return value

    def clean(self, value):
        value = super().clean(value)
        if value and value < 0:
            raise forms.ValidationError(self.error_messages['positive'])
        else:
            return value


class LoanCalculationForm(forms.ModelForm):
    loan_company_id = forms.IntegerField(widget=forms.HiddenInput)
    current_loan_rate = PercentageField(widget=PercentInput(), required=False)
    fieldset_info = {
        'required_fields': ['loan_type',
                            'loan_amount',
                            'monthly_term'],
        'current_loan_fields': ['current_loan_balance',
                                'current_loan_monthly_payment',
                                'current_loan_rate'],
        'credit_information_fields': ['estimated_credit_score',
                                      'estimated_collateral_value',
                                      'estimated_monthly_income',
                                      'estimated_monthly_expenses',
                                      'estimated_year_of_collateral']}

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

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, initial=None, error_class=ErrorList,
                 label_suffix=None, empty_permitted=False, instance=None, loan_company=None):
        if loan_company is None:
            raise Exception('No loan company supplied to calculation form')

        result = super().__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance)

        # Set the loan_type choices based on the company
        self.fields['loan_type'].widget.choices = self.get_loan_type_choices(loan_company)
        return result

    @property
    def required_fields(self):
        return (f for f in self.visible_fields() if f.name in self.fieldset_info['required_fields'])

    @property
    def current_loan_fields(self):
        return (f for f in self.visible_fields() if f.name in self.fieldset_info['current_loan_fields'])

    @property
    def credit_information_fields(self):
        return (f for f in self.visible_fields() if f.name in self.fieldset_info['credit_information_fields'])

    @staticmethod
    def get_loan_type_choices(loan_company):
        return [(lt.id, lt.name) for lt in LoanType.objects.filter(loanaddition__loan_company=loan_company).distinct()]

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
            pmt = float(cleaned_data['current_loan_monthly_payment'])
            pv = float(cleaned_data['current_loan_balance'])
            rate = float(cleaned_data['current_loan_rate'])
            if pmt <= (rate / 12) * pv:
                self._errors['current_loan_monthly_payment'] = self.error_class(
                    [_('is too small to ever pay the loan off')])
                del cleaned_data['current_loan_monthly_payment']
        return cleaned_data

    def save(self, commit=True):
        loan_company = LoanCompany.objects.get(pk=self.cleaned_data.get('loan_company_id'))
        self.instance.loan_company = loan_company
        return super().save(commit)

