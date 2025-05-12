from django import forms
from app.models import Proposal, Opportunity, Vacancy

class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['company', 'pricing_total', 'pricing_details']
        widgets = {
            'pricing_details': forms.Textarea(attrs={'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario.
        """
        super().__init__(*args, **kwargs)
        self.fields['company'].widget.attrs.update({'class': 'form-control'})
        self.fields['pricing_total'].widget.attrs.update({'class': 'form-control'})
        self.fields['pricing_details'].widget.attrs.update({'class': 'form-control'})
        
    def clean_pricing_total(self):
        """
        Valida el total del pricing.
        
        Returns:
            float: Total del pricing
            
        Raises:
            forms.ValidationError: Si el total es inválido
        """
        pricing_total = self.cleaned_data.get('pricing_total')
        if pricing_total <= 0:
            raise forms.ValidationError('El total del pricing debe ser mayor a cero.')
        return pricing_total
        
    def clean_pricing_details(self):
        """
        Valida los detalles del pricing.
        
        Returns:
            dict: Detalles del pricing
            
        Raises:
            forms.ValidationError: Si los detalles son inválidos
        """
        pricing_details = self.cleaned_data.get('pricing_details')
        try:
            details = json.loads(pricing_details)
            if not isinstance(details, dict):
                raise forms.ValidationError('Los detalles del pricing deben ser un objeto JSON válido.')
            return details
        except json.JSONDecodeError:
            raise forms.ValidationError('Los detalles del pricing deben ser un objeto JSON válido.')

class ProposalFilterForm(forms.Form):
    company = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + Proposal.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def filter_queryset(self, queryset):
        """
        Filtra el queryset según los criterios del formulario.
        
        Args:
            queryset: QuerySet a filtrar
            
        Returns:
            QuerySet: QuerySet filtrado
        """
        if self.cleaned_data['company']:
            queryset = queryset.filter(
                company__name__icontains=self.cleaned_data['company']
            )
            
        if self.cleaned_data['status']:
            queryset = queryset.filter(
                status=self.cleaned_data['status']
            )
            
        if self.cleaned_data['start_date']:
            queryset = queryset.filter(
                created_at__gte=self.cleaned_data['start_date']
            )
            
        if self.cleaned_data['end_date']:
            queryset = queryset.filter(
                created_at__lte=self.cleaned_data['end_date']
            )
            
        return queryset
