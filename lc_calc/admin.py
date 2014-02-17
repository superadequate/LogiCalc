from django.contrib import admin
from lc_calc.utils.related_field_admin import RelatedFieldAdmin

from lc_calc.models import (LoanType,
                            LoanCompany,
                            LoanAdditionLookupValueType,
                            LoanAdditionLookup)

admin.site.register(LoanType)
admin.site.register(LoanCompany)
admin.site.register(LoanAdditionLookupValueType)


class LoanAdditionLookupAdmin(RelatedFieldAdmin):
    list_display = ['id',
                    'loan_company_title',
                    'loan_type_name',
                    'value_type_name',
                    'credit_score',
                    'value_index',
                    'value']
    list_filter = ['loan_company',
                   'loan_type',
                   'value_type',
                   'credit_score',
                   'value_index']
    search_fields = ['loan_company__title',
                     'loan_type__name',
                     'value_type__name']
    list_editable = ['credit_score', 'value_index', 'value']

    def loan_company_title(self, obj):
        return obj.loan_company.title
    loan_company_title.short_description = "Loan Company"
    loan_company_title.admin_order_field = 'loan_company__title'

    def loan_type_name(self, obj):
        return obj.loan_type.name
    loan_type_name.short_description = "Loan Type"
    loan_type_name.admin_order_field = 'loan_type__name'

    def value_type_name(self, obj):
        return obj.value_type.name
    value_type_name.short_description = "Value Type"
    value_type_name.admin_order_field = 'value_type__name'



admin.site.register(LoanAdditionLookup, LoanAdditionLookupAdmin)