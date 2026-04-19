from django import forms
from accounts.models import StudentProfile

class PreferredNumberForm(forms.Form):
    preferred_number = forms.IntegerField(
        label='Enter Preferred Number',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter student preferred number',
            'autofocus': True
        })
    )
    
    def clean_preferred_number(self):
        number = self.cleaned_data.get('preferred_number')
        try:
            student = StudentProfile.objects.get(preferred_number=number)
        except StudentProfile.DoesNotExist:
            raise forms.ValidationError(f"No student found with preferred number {number}")
        return number

class FilterForm(forms.Form):
    company = forms.ChoiceField(
        choices=[('', 'All Companies')] + list(StudentProfile.COMPANIES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    course = forms.ChoiceField(
        choices=[('', 'All Courses')] + list(StudentProfile.COURSES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + [('present', 'Present'), ('absent', 'Absent'), 
                                        ('late', 'Late'), ('cutting', 'Cutting')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )