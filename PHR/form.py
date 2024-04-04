from django import forms
from . import views
import time
from fhirclient import client
from fhirclient.models.patient import Patient
import requests
import fhirclient.models.humanname as hn
from fhirclient.models import fhirdate, bundle as b, meta, resource, fhirabstractresource, observation, address
from fhirclient.models import patient, contactpoint, period, codeableconcept, coding, quantity, fhirreference
from fhirclient.models import medicationrequest, dosage, extension, duration, timing, ratio, medication, bodystructure
from fhirclient.models import device, allergyintolerance, diagnosticreport, imagingstudy, attachment, binary, media

"""settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
smart = client.FHIRClient(settings=settings)
NHINumber = request.session['NHINumber']
p1 = Patient.read(NHINumber, smart.server)
c_time = time.ctime()
c_time = int(c_time[-4:])
year_Range = range(int(p1.birthDate.isostring[0:4]), c_time)
year_Range = year_Range[::-1]"""

class UserForm(forms.Form):
    username = forms.CharField(label="Username", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Username", 'autofocus': ''}))
    password = forms.CharField(label="Password", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': "Password"}))

class RegisterForm(forms.Form):
    username = forms.CharField(label="Username", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Username"}))
    #patient_name = forms.CharField(label="Patient Name", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Username"}))
    phoneNumber = forms.CharField(label="Phone number", max_length=128,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Phone number"}))
    NHINumber = forms.CharField(label="NHINumber", max_length=128,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "National Health Insurrence Number"}))
    password1 = forms.CharField(label="Password", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': "Password"}))
    password2 = forms.CharField(label="Confirm Password", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': "Confirm Password"}))

class NameForm(forms.Form):
    #your_date = forms.DateField(label="Date", widget=forms.SelectDateWidget(years=year_Range, attrs={'class': 'col-4', 'size': '3', 'style': 'border-radius: 9px;background-color: rgba(198, 220, 245, 1);color: rgba(238, 47, 5, 1);font-size: 14px;text-align: left;box-shadow: 0px 3px 6px 0px rgba(0, 0, 0, 0.4);font-family: Arial;border: 1px solid rgba(22, 132, 252, 1);'}))
    your_date = forms.DateField(label="Date", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Y-m-d H:i','style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_height = forms.CharField(label="Your height", max_length=10,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_weight = forms.CharField(label="Your weight", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_temperature = forms.CharField(label="Your temperature", max_length=10,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_steps = forms.CharField(label="Your steps", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_BMI = forms.CharField(label="Your BMI", max_length=10,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_blood_pressure_up = forms.CharField(label="Your blood pressure up", max_length=10,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_blood_pressure_down = forms.CharField(label="Your blood pressure down", max_length=10,
                                             widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_pulse_rate = forms.CharField(label="Your pulse rate", max_length=10,
                                             widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_respiration = forms.CharField(label="Your respiration", max_length=10,
                                             widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    your_smoking = forms.CharField(label="Your smoking", max_length=10,
                                             widget=forms.TextInput(attrs={'class': 'form-control', 'style': 'border-radius: 4px 4px 4px 4px;background-color: rgba(198, 220, 245, 1);border: 1px solid rgba(187, 187, 187, 1);'}))
    #your_dateYear = forms.DateField(label="Date_Year", widget=forms.TextInput(attrs={'class': 'form-control'}))
    #your_dateMonth = forms.DateField(label="Date_Month", widget=forms.TextInput(attrs={'class': 'form-control'}))
    #your_dateDay = forms.DateField(label="Date_Day", widget=forms.TextInput(attrs={'class': 'form-control'}))
    """your_date = forms.DateField(label="Date", widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_pulse_rate = forms.CharField(label="Your pulse rate(bpm)", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_blood_pressure_up = forms.CharField(label="Your systolic blood pressure(mmHg)", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_blood_pressure_down = forms.CharField(label="Your diastolic blood pressure(mmHg)", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_temperature = forms.CharField(label="Your temperature(℃)", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_weight = forms.CharField(label="Your weight(Kg)", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_disease = forms.CharField(label="Your disease", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))"""


class BasicChangeForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_gender = forms.fields.ChoiceField(
        choices=(("Male", "Male"), ("Female", "Female")),
        label="Your gender",
        initial="Male",
        widget=forms.widgets.Select(attrs={'class': 'form-control'})
    )
class PatientChangeForm(forms.Form):
    your_name = forms.CharField(label="New Patient's name", max_length=100,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    your_gender = forms.fields.ChoiceField(
        choices=(("Male", "Male"), ("Female", "Female")),
        label="New Patient's gender",
        initial="Male",
        widget=forms.widgets.Select(attrs={'class': 'form-control'})
    )

class DiseaseChangeForm(forms.Form):
    your_disease_1 = forms.BooleanField(label="Chickenpox")
    your_disease_2 = forms.BooleanField(label="Influenza")
    your_disease_3 = forms.BooleanField(label="Common cold")
    your_disease_4 = forms.BooleanField(label="Pneumonia")
    your_disease_5 = forms.BooleanField(label="Salmonella infections")
    your_disease = forms.CharField(label="Your disease", max_length=100,
                                       widget=forms.TextInput(attrs={'class': 'form-control'}))
    index = forms.CharField(label="Disease index(1-5, 0 means remove)", max_length=100,
                                   widget=forms.TextInput(attrs={'class': 'form-control'}))

class PrescriptionForm(forms.Form):
    drug_name = forms.CharField(label="Drug Name", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    frequency = forms.CharField(label="Frequency", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    method = forms.CharField(label="Method", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

class LabTestForm(forms.Form):
    test_name = forms.CharField(label="Test Name", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    r_time = forms.DateField(label="Test Time", widget=forms.TextInput(attrs={'class': 'form-control'}))
class LabForm(forms.Form):
    item_name = forms.CharField(label="Item Name", max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    estimated_value = forms.CharField(label="Estimated Value", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    unit = forms.CharField(label="Unit", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    standard_value = forms.CharField(label="Standard Value", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
