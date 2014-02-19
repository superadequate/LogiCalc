from django import forms

from lc_calc.models import LoanCalculation, LoanCompany


class LoanCalculationForm(forms.ModelForm):
    loan_company_id = forms.IntegerField(widget=forms.HiddenInput)

    class Meta:
        model = LoanCalculation
        fields = ['loan_type',
                  'current_loan_balance',
                  'current_loan_monthly_payment',
                  'current_loan_rate',
                  'current_loan_estimated_remaining_term',
                  'estimated_credit_score',
                  'estimated_collateral_value',
                  'estimated_monthly_income',
                  'estimated_monthly_expenses',
                  'estimated_year_of_collateral',
                  'loan_amount',
                  'monthly_term']

    def save(self, commit=True):
        loan_company = LoanCompany.objects.get(pk=self.cleaned_data.get('loan_company_id'))
        self.instance.loan_company = loan_company
        return super().save(commit)

