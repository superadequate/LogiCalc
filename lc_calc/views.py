from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404

from lc_calc.models import LoanCompany, LoanCalculation
from lc_calc.forms import LoanCalculationForm


class LoanCompanyMixin(object):

    def get_loan_company(self):
        # Add the loan company
        return get_object_or_404(
            LoanCompany,
            slug=self.kwargs['loan_company_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add the loan company
        context['loan_company'] = self.get_loan_company()
        return context


class CalculationView(LoanCompanyMixin, FormView):
    template_name = "ls_calc/calculation.html"
    form_class = LoanCalculationForm
    model = LoanCalculation

    def get_calculation(self):
        """
        If there is a calculation already available to this session, get it.
        """
        try:
            return self.calculation
        except AttributeError:
            calculation_id = self.request.session.get('calculation_id', None)
            if calculation_id is None:
                self.calculation = None
            else:
                self.calculation = LoanCalculation.objects.get(id=calculation_id)
            return self.calculation

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        calculation = self.get_calculation()
        if calculation is not None:
            kwargs['instance'] = calculation
        return kwargs

    def form_valid(self, form):
        form.save()
        form.instance = LoanCalculation.objects.get(id=form.instance.id)
        self.request.session['calculation_id'] = form.instance.id
        return self.get(self.request, *self.args, **self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calculation = self.get_calculation()
        if calculation is not None:
            context['calculation'] = calculation
        return context

