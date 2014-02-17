from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from lc_calc.models import LoanCompany

class CalculatorView(TemplateView):
    template_name = "ls_calc/calculator.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add the loan company
        loan_company = get_object_or_404(
            LoanCompany,
            slug=kwargs['loan_company_slug'])
        context['loan_company'] = loan_company
        return context