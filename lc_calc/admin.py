from django.contrib import admin
from lc_calc.utils.related_field_admin import RelatedFieldAdmin

from lc_calc.models import (LoanType,
                            LoanCompany,
                            LoanAdditionValueType,
                            LoanAddition,
                            LoanCalculation,
                            LoanCompanyMessage)

admin.site.register(LoanType)


class LoanCompanyMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'loan_company', 'sender', 'loan_calculation']
    list_filter = ['created', 'loan_company']
    search_fields = ['sender']

    def has_add_permission(self, request):
        return False

admin.site.register(LoanCompanyMessage, LoanCompanyMessageAdmin)


class LoanCalculationAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'loan_company', 'loan_type', 'loan_amount', 'monthly_term', 'rate', 'monthly_payment']
    list_filter = ['created', 'loan_company', 'loan_type', 'loan_amount']
    search_fields = ['loan_company', 'loan_type']

    def has_add_permission(self, request):
        return False


admin.site.register(LoanCalculation, LoanCalculationAdmin)


class LoanAdditionValueTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'value_index_method_name', 'sum_in_rate_calculation']
    list_editable = ['value_index_method_name', 'sum_in_rate_calculation']

admin.site.register(LoanAdditionValueType, LoanAdditionValueTypeAdmin)


class LoanCompanyAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'email']
    fields = ['title', 'slug', 'email', 'content', 'logo', 'disclosure']
    readonly_fields = ['slug']

admin.site.register(LoanCompany, LoanCompanyAdmin)


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



admin.site.register(LoanAddition, LoanAdditionLookupAdmin)