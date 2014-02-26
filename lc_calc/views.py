from django.views.generic.edit import FormView, CreateView
from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages

import lc_calc.models as lcmodels
from lc_calc.forms import LoanCalculationForm


class LoanCompanyMixin(object):
    """
    Provides view with calculation and template with loan_company and calculation (if present)
    """
    def get_loan_company(self):
        # Add the loan company
        return get_object_or_404(
            lcmodels.LoanCompany,
            slug=self.kwargs['loan_company_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add the loan company
        context['loan_company'] = self.get_loan_company()

        calculation = self.get_calculation()
        if calculation is not None:
            context['calculation'] = calculation

        return context

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
                calculation = lcmodels.LoanCalculation.objects.get(id=calculation_id)
                if calculation.loan_company == self.get_loan_company():
                    self.calculation = calculation
                else:
                    self.calculation = None
        return self.calculation

    def put_calculation(self, calculation):
        """
        Record calculation in the session and on self
        """
        self.request.session['calculation_id'] = calculation.id
        self.request.session.set_expiry(3600)  # remember it for an hour


class CalculationView(LoanCompanyMixin, FormView):
    template_name = "lc_calc/calculation.html"
    form_class = LoanCalculationForm
    model = lcmodels.LoanCalculation

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # Add in the loan company so we can determine the available loan types
        kwargs['loan_company'] = self.get_loan_company()

        # Add in the calculation if it already exists
        calculation = self.get_calculation()
        if calculation is not None:
            kwargs['instance'] = calculation
        return kwargs

    def form_valid(self, form):
        form.save()
        self.put_calculation(form.instance)
        return redirect("calculation", **self.kwargs)


class LoanCompanyMessageView(LoanCompanyMixin, CreateView):
    model = lcmodels.LoanCompanyMessage

    def form_valid(self, form):
        """
        Specialisation to record the loan_company and calculation if available.
        """
        self.success_url = reverse('calculation', kwargs={'loan_company_slug': self.kwargs['loan_company_slug']})
        messages.success(self.request, 'Your message has been sent.')
        lcm = form.instance
        lcm.loan_company = self.get_loan_company()
        calculation = self.get_calculation()
        if calculation:
            lcm.loan_calculation = calculation
        return super().form_valid(form)