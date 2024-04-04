import requests.exceptions
from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.server import FHIRNotFoundException
import fhirclient.models.humanname as hn
from fhirclient.models import fhirdate, bundle as b, meta, resource, fhirabstractresource, observation, address
from fhirclient.models import patient, contactpoint, period, codeableconcept, coding, quantity, fhirreference, organization
from fhirclient.models import medicationrequest, dosage, extension, duration, timing, ratio, medication, bodystructure, condition
from fhirclient.models import device, allergyintolerance, diagnosticreport, imagingstudy, attachment, binary, media, encounter
from collections import defaultdict
import time
import base64
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseRedirect
from .form import NameForm
from django.views import View
from . import models
from . import form
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
import hashlib
import datetime
import time
import json
import re
import fhirclient.models.observation as ob
from fhirclient import client
import fhirclient.models.patient as p
from fhirclient.models.medication import Medication
import fhirclient.models.humanname as hn
from fhirclient.models import fhirdate, bundle as b, meta, resource, fhirabstractresource
from .decorators import log_Ation
import requests
@csrf_exempt

def MakeOrder(list):
    data_tem = []
    for i in list:
        date_tem = i.effectiveDateTime.isostring
        try:
            date_tem = datetime.datetime.strptime(date_tem, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            try:
                date_tem = datetime.datetime.strptime(date_tem, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                date_tem = datetime.datetime.strptime(date_tem, "%Y-%m-%d")
        data_tem.append([date_tem, i])
    data_tem.sort(key=lambda x: x[0], reverse=True)
    return data_tem

def hash_code(s, salt='PHR'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()

def takeFirst(elem):
    return elem[0]
def fetch_page(url, server, retries=3):
    try:
        return b.Bundle.read_from(url, server)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 410 and retries>0:
            print("Link expired, retrying... Retries left:", retries)
            return fetch_page(url, server, retries=retries-1)
        else:
            raise
def fetch_all_pages(initial_bundle):
    settings = {
        'app_id': 'phr',
        'api_base': 'https://server.fire.ly'
    }
    smart = client.FHIRClient(settings=settings)
    resources = []
    bundle = initial_bundle
    while bundle:
        # 添加当前页面的资源
        resources.extend(entry.resource for entry in bundle.entry or [])  # 确保entry存在
        # 准备下一个请求
        next_link = next((link.url for link in bundle.link if link.relation == 'next'), None)
        #bundle = b.Bundle.read_from(next_link, smart.server) if next_link else None
        if next_link:
            bundle = fetch_page(next_link, smart.server)
        else:
            bundle = None
    return resources


def phrOrganization():
    settings = {
        'app_id': 'phr',
        'api_base': 'https://server.fire.ly'
    }
    smart = client.FHIRClient(settings=settings)
    phr = organization.Organization()
    phr.name = "PHR Prototype"
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.system = "http://terminology.hl7.org/CodeSystem/organization-type"
    coding1.code = "prov"
    coding1.display = "Healthcare Provider"
    code1 = [coding1]
    phr.type = [code1]
    tele1 = contactpoint.ContactPoint()
    tele1.system = "phone"
    tele1.value = "022-655-2300"
    tele1.use = "work"
    phr.telecom = [tele1]
    tele2 = contactpoint.ContactPoint()
    tele2.system = "phone"
    tele2.value = "080-3338-2334"
    telecom = [tele2]
    phr.contact = [telecom]
    response = phr.create(smart.server)
    if response:
        print(f"Created Organzation with id: {response['id']}")
    else:
        print("Failed to create Organzation")

def create_BloodPressure(value1, value2, patient_id, date, organization_id):
    BP = observation.Observation()
    BP.status = "final"
    BP.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '85354-9'
    coding1.system = "http://loinc.org"
    coding1.display = "Blood pressure panel with all children optional"
    code1.coding = [coding1]
    code1.text = "Blood pressure systolic & diastolic"
    BP.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding2]
    BP.category = [code2]
    code3 = codeableconcept.CodeableConcept()
    coding3 = coding.Coding()
    coding3.code = '8480-6'
    coding3.display = 'Systolic blood pressure'
    coding3.system = "http://loinc.org"
    code3.coding = [coding3]
    quantity1 = quantity.Quantity()
    quantity1.value = value1
    quantity1.unit = 'mmHg'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = 'mm[Hg]'
    code4 = codeableconcept.CodeableConcept()
    coding4 = coding.Coding()
    coding4.code = '8462-4'
    coding4.display = 'Diastolic blood pressure'
    coding4.system = "http://loinc.org"
    code4.coding = [coding4]
    quantity2 = quantity.Quantity()
    quantity2.value = value2
    quantity2.unit = 'mmHg'
    quantity2.system = "http://unitsofmeasure.org"
    quantity2.code = 'mm[Hg]'
    component1 = observation.ObservationComponent()
    component1.code = code3
    component1.valueQuantity = quantity1
    component2 = observation.ObservationComponent()
    component2.code = code4
    component2.valueQuantity = quantity2
    BP.component = [component1, component2]
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    BP.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    BP.performer = [performer1]
    return BP

def create_Smoking(value, patient_id, date, organization_id):
    height = observation.Observation()
    height.status = "final"
    height.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '63773-6'
    coding1.system = "http://loinc.org"
    coding1.display = "Smoking"
    code1.text = "Smoking"
    code1.coding = [coding1]
    height.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'social-history'
    coding2.display = 'Social History'
    coding2.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding2]
    height.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = '/d'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = '/d'
    height.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    height.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    height.performer = [performer1]
    return height

def create_BodyHeight(value, patient_id, date, organization_id):
    height = observation.Observation()
    height.status = "final"
    height.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '8302-2'
    coding1.system = "http://loinc.org"
    coding1.display = "Body Height"
    code1.text = "Body Height"
    code1.coding = [coding1]
    height.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding2]
    height.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = 'cm'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = 'cm'
    height.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    height.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    height.performer = [performer1]
    return height

def create_HeartRate(value, patient_id, date, organization_id):
    HR = observation.Observation()
    HR.status = "final"
    HR.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '8867-4'
    coding1.system = "http://loinc.org"
    coding1.display = "Heart rate"
    code1.text = "Heart rate"
    code1.coding = [coding1]
    HR.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding2]
    HR.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = 'beats/minute'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = '/min'
    HR.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    HR.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    HR.performer = [performer1]
    return HR

def create_RespiratoryRate(value, patient_id, date, organization_id):
    RR = observation.Observation()
    RR.status = "final"
    RR.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '9279-1'
    coding1.system = "http://loinc.org"
    coding1.display = "Respiratory rate"
    code1.text = "Respiratory rate"
    code1.coding = [coding1]
    RR.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding2]
    RR.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = 'breaths/minute'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = '/min'
    RR.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    RR.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    RR.performer = [performer1]
    return RR

def create_BodyWeight(value, patient_id ,date, organization_id):
    weight = observation.Observation()
    weight.status = "final"
    weight.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '29463-7'
    coding1.system = "http://loinc.org"
    coding1.display = "Body Weight"
    code1.text = "Body Weight"
    code1.coding = [coding1]
    weight.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding2]
    weight.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = 'kg'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = 'kg'
    weight.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    weight.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    weight.performer = [performer1]
    return weight

def create_BodyTemp(value, patient_id, date, organization_id):
    temp = observation.Observation()
    temp.status = "final"
    temp.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '8310-5'
    coding1.system = "http://loinc.org"
    coding1.display = "Body temperature"
    code1.text = "Body temperature"
    code1.coding = [coding1]
    temp.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding3 = coding.Coding()
    coding3.code = 'vital-signs'
    coding3.display = 'vital-signs'
    coding3.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding3]
    temp.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = 'Cel'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = 'Cel'
    temp.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    temp.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    temp.performer = [performer1]
    return temp

def create_BMI(value, patient_id, date, organization_id):
    BMI = observation.Observation()
    BMI.status = "registered"
    BMI.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '39156-5'
    coding1.system = "http://loinc.org"
    coding1.display = "Body mass index (BMI) [Ratio]"
    code1.text = "BMI"
    code1.coding = [coding1]
    BMI.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://terminology.hl7.org/CodeSystem/observation-category"
    code2.coding = [coding2]
    BMI.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = 'kg/m2'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = 'kg/m2'
    BMI.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    BMI.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    BMI.performer = [performer1]
    return BMI

def create_Steps(value, patient_id, date, organization_id):
    steps = observation.Observation()
    steps.status = "final"
    steps.effectiveDateTime = fhirdate.FHIRDate(date)
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '41950-7'
    coding1.system = "http://loinc.org"
    coding1.display = "Number of steps"
    code1.text = "Steps"
    code1.coding = [coding1]
    steps.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://terminology.hl7.org/CodeSystem/observation-category"
    code2.coding = [coding2]
    steps.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = '/24h'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = '/24h'
    steps.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient_id
    steps.subject = subject1
    performer1 = fhirreference.FHIRReference()
    performer1.reference = "Organization/" + organization_id
    steps.performer = [performer1]
    return steps
@log_Ation('Main interface')
def index(request):
    request.session['is_new'] = True
    request.session['RecordType'] = "Allergies"
    request.session['Encounter'] = "None"
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    p_id = request.session['patient_id']
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    patient = models.Patient.objects.filter(cid=p_id)
    if len(patient) > 1:
        patient = patient.get(name=request.session['patient_name'])
    else:
        patient = patient[0]
    #NHINumber = 'baede442-d962-45f1-8958-0cb838540ecf'
    NHINumber = patient.NHINumber
    request.session['NHINumber'] = NHINumber
    request.session['DataType'] = "Record"
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    smart = client.FHIRClient(settings=settings)
    p1 = Patient.read(NHINumber, smart.server)
    print("##########Patient##########")
    print(smart.human_name(p1.name[0]))
    p1_Name = smart.human_name(p1.name[0])
    patient.name = p1_Name
    patient.save()
    c_time = time.ctime()
    age = str(int(c_time[-4:]) - int(p1.birthDate.isostring[0:4]))
    print(p1.gender, p1.birthDate.isostring, age, p1.address)
    """organization_id = "dea39875-4931-43b5-9d3b-6d52142b1cc5"
    patient.organization_id = organization_id
    patient.NHINumber = NHINumber
    patient.save()"""
    if p1.address:
        Address = p1.address[0].line[0] + "," + p1.address[0].city + "," + p1.address[0].country
    if p1.telecom:
        for i in p1.telecom:
            if i.system=="phone":
                Phone = i.value
            else:
                Phone = "None"
            if i.system=="email":
                Email = i.value
            else:
                Email = "None"
    else:
        Phone = "None"
        Email = "None"
    BirthDate = p1.birthDate.isostring
    if p1.photo:
        Photo = p1.photo[0].data
    else:
        Photo = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBAUEBAYFBQUGBgYHCQ4JCQgICRINDQoOFRIWFhUSFBQXGiEcFxgfGRQUHScdHyIjJSUlFhwpLCgkKyEkJST/2wBDAQYGBgkICREJCREkGBQYJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCT/wAARCAIAAgADAREAAhEBAxEB/8QAHQABAAICAwEBAAAAAAAAAAAAAAcIAQYEBQkDAv/EAE4QAAEDAwIDBQUEBQgHBwUBAAEAAgMEBREGIQcSMQgTQVFhFCIycYEVI0KRFlJygqEkM2KSorHBwkNTY3Oy0fAXJSZUk6OzNIPD4fHT/8QAFAEBAAAAAAAAAAAAAAAAAAAAAP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/ALOoCAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICANzgbk+A6oOHdr3a7DT+03e5UNtgPSWsnZC313eQg0e9doXhdY3PjqNYUVRI3IDaGOSqDsDoHRtLfqT9UGnXDtjcPqXmZTW/UdZIBlrmU0UcZPkS6TI+eCg1ip7blHG/FNoWedn60t0EZ/JsR/vQdTU9te7vlzTaPtsUf6stZI8/mAB/BBxX9tPU5/m9MWM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wwOIzvhBa/hf2atI8Pu5r66Nt/vTMOFVVxjuoHZODFEcgEe77zi52RkcvRBLxJOSSSfElBhAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQdXqLS1j1bbnW2/WqjudI4kiKoj5gw4xzNPVh36twfVBXziD2NqKqMlZoW7exPOT9nXJxfF16MmALmgDoHB2/VwQV51lww1hoGTGo7BWUMZIDajlD4Hk9AJWEsJ9M59EGqoMICAgICAgICAgICAgICAgIP2ATjA38PVBKOh+zZxD1qY5/sn7FoHjPtV1zDkDB92PBkdkHIPLg+YQWO0F2VdDaRMdTd436mr2YPPXMDacEZ3EAJBGD0eX9PBBMkbGxsaxjQxrAGta0YDRjAAHgAPAbIP0gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICD8yRsljfFI1r45AWvY4Za4HrkEHI9CEEX6u7NPDXVpdKLKbLUux9/aHiAfLuyDH+Tc+qCFtT9jDUdFzzab1BbrpGAXdzVsdSy+jQRzMJ9SWhBEmo+D+v9Jl/2xpK7QMYMvnihM0IH+8j5mfxQad1QCMIMICAgICAgICDOPyQciioKu5VLKahpZ6qof8MUEZe93yA3QSPpjs28TNTuY5unZbVTuPKZ7q4UwYfVjvvD9GlBL2kuxbRw93Nq3U0tQ7HvUtrj7tocP9tICSPkwH1QTdo/hTonQRbJp7TlDSVDc4qntM1RuMH715LgD5AgeiDbOpOcknqT1KAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAy34SRnrg4QdJftD6X1QXPvmnLPcpHNI72qo2PkA9Hkcw+YKDQL12WeFt2a4w2WqtcjySZKGtkHXybIXNGOuAAEGn3XsV6ZmyLTqm80m2xq4YqjB8zy8mR6INbr+xNcYzig1pRVA856CSLH9VzkHTzdi7XQkPcX3Sz4/AvnnYT9O6P96D4v7GXEFnS76Vf8qub/ABhCDLexfxAIybzpMfOrn/8A8UHKpOxbrA59t1Fp2LfbuDPL/kag76h7EhIa+u1y1pzl0VPbCdvIOdIP4hBtFs7GuhaZrH1931DWytJLgyWGGN/pgMLh9HIN2svZ54XWJ0ckGkKOokbjLq6SSpDiPNsjiz8h9EG92u02+yUoo7VQUlvph0hpIWwsH7rQB0CDleJPiepQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQf//Z"
    Observation = observation.Observation.where({'patient': NHINumber, '_sort': '-date'}).perform(smart.server)
    Weight = []
    Height = []
    HR = []
    BodyTem = []
    BP = []
    RR = []
    Steps = []
    BMI = []
    Smoking = []
    if Observation.entry != None:
        Observation = fetch_all_pages(Observation)
        #Observation = [ob.resource for ob in Observation.entry]
        # 可以尝试用include进行优化
        if len(Observation) > 0:
            for Ob in Observation:
                print(Ob.code)
                if Ob.code.coding[0].code == '29463-7':
                    Weight.append(Ob)
                elif Ob.code.coding[0].code == '8302-2':
                    Height.append(Ob)
                elif Ob.code.coding[0].code == '8867-4':
                    HR.append(Ob)
                elif Ob.code.coding[0].code == '8310-5':
                    BodyTem.append(Ob)
                elif Ob.code.coding[0].code == '85354-9':
                    BP.append(Ob)
                elif Ob.code.coding[0].code == '9279-1':
                    RR.append(Ob)
                elif Ob.code.coding[0].code == '41950-7':
                    Steps.append(Ob)
                elif Ob.code.coding[0].code == '39156-5':
                    BMI.append(Ob)
                elif Ob.code.coding[0].code == '63773-6':
                    Smoking.append(Ob)

    """Weight = observation.Observation.where({'patient': NHINumber, 'code': '29463-7', '_count': '2', '_sort': '-date'}).perform(smart.server)
    HR = observation.Observation.where({'patient': NHINumber, 'code': '8867-4', '_count': '2', '_sort': '-date'}).perform(smart.server)
    BodyTem = observation.Observation.where({'patient': NHINumber, 'code': '8310-5', '_count': '2', '_sort': '-date'}).perform(smart.server)
    BP = observation.Observation.where({'patient': NHINumber, 'code': '85354-9', '_count': '2', '_sort': '-date'}).perform(smart.server)
    Height = observation.Observation.where({'patient': NHINumber, 'code': '8302-2', '_count': '2', '_sort': '-date'}).perform(smart.server)
    #RR = observation.Observation.where({'patient': NHINumber, 'code': '9279-1'}).perform(smart.server)
    RR = observation.Observation.where({'patient': NHINumber, 'code': '9279-1', '_count': '2', '_sort': '-date'}).perform(smart.server)
    Steps = observation.Observation.where({'patient': NHINumber, 'code': '41950-7', '_count': '2', '_sort': '-date'}).perform(
        smart.server)
    BMI = observation.Observation.where(
        {'patient': NHINumber, 'code': '39156-5', '_count': '2', '_sort': '-date'}).perform(
        smart.server)
    Smoking = observation.Observation.where(
        {'patient': NHINumber, 'code': '63773-6', '_count': '2', '_sort': '-date'}).perform(
        smart.server)"""
    print("#######################PGHD")
    #print(NHINumber)

    RR = MakeOrder(RR)
    if RR != []:
        RR_Name = RR[0][1].code.text
        if len(RR) > 0:
            RR_Last = str(RR[0][1].valueQuantity.value) + str(RR[0][1].valueQuantity.code)
            if len(RR) > 1:
                RR_Trend = str(RR[0][1].valueQuantity.value - RR[1][1].valueQuantity.value)
            else:
                RR_Trend = "None"
        else:
            RR_Last = "None"
    else:
        RR_last = "None"
        RR_Trend = "None"
    Height = MakeOrder(Height)
    if Height != []:
        if len(Height) > 0:
            Height_Last = str(Height[0][1].valueQuantity.value) + str(Height[0][1].valueQuantity.unit)
            if len(Height) > 1:
                Height_Trend = str(Height[0][1].valueQuantity.value - Height[1][1].valueQuantity.value)
            else:
                Height_Trend = "None"
        else:
            Height_Last = "None"
    else:
        Height_Last = "None"
        Height_Trend = "None"
    Weight = MakeOrder(Weight)
    if Weight != []:
        if len(Weight) > 0:
            Weight_Last = str(Weight[0][1].valueQuantity.value) + str(Weight[0][1].valueQuantity.unit)
            if len(Weight) > 1:
                Weight_Trend = str(Weight[0][1].valueQuantity.value - Weight[1][1].valueQuantity.value)
            else:
                Weight_Trend = "None"
        else:
            Weight_Last = "None"
    else:
        Weight_Last = "None"
        Weight_Trend = "None"
    BodyTem = MakeOrder(BodyTem)
    if BodyTem != []:

        if len(BodyTem) > 0:
            BodyTem_Last = str(BodyTem[0][1].valueQuantity.value) + str(BodyTem[0][1].valueQuantity.unit)
            if len(BodyTem) > 1:
                BodyTem_Trend = str(BodyTem[0][1].valueQuantity.value - BodyTem[1][1].valueQuantity.value)
            else:
                BodyTem_Trend = "None"
        else:
            BodyTem_Last = "None"
    else:
        BodyTem_Last = "None"
        BodyTem_Trend = "None"
    Steps = MakeOrder(Steps)
    if Steps != []:
        if len(Steps) > 0:
            Steps_Last = str(int(Steps[0][1].valueQuantity.value)) + str(Steps[0][1].valueQuantity.unit)
            if len(Steps) > 1:
                Steps_Trend = str(int(Steps[0][1].valueQuantity.value - Steps[1][1].valueQuantity.value))
            else:
                Steps_Trend = "None"
        else:
            Steps_Last = "None"
    else:
        Steps_Last = "None"
        Steps_Trend = "None"
    BMI = MakeOrder(BMI)
    if BMI != []:

        if len(BMI) > 0:
            BMI_Last = str(BMI[0][1].valueQuantity.value) + str(BMI[0][1].valueQuantity.unit)
            if len(BMI) > 1:
                BMI_Trend = str(BMI[0][1].valueQuantity.value - BMI[1][1].valueQuantity.value)
            else:
                BMI_Trend = "None"
        else:
            BMI_Last = "None"
    else:
        BMI_Last = "None"
        BMI_Trend = "None"
    BP = MakeOrder(BP)
    if BP != []:
        if len(BP) > 0:
            BP_Last = str(str(BP[0][1].component[0].valueQuantity.value) + "/" + str(BP[0][1].component[1].valueQuantity.value) + str(BP[0][1].component[0].valueQuantity.unit))
            if len(BP) > 1:
                BP_Trend = str(BP[0][1].component[0].valueQuantity.value - BP[1][1].component[0].valueQuantity.value) + "/" + str(BP[0][1].component[1].valueQuantity.value - BP[1][1].component[1].valueQuantity.value)
            else:
                BP_Trend = "None"
        else:
            BP_Last = "None"
    else:
        BP_Last = "None"
        BP_Trend = "None"
    HR = MakeOrder(HR)
    if HR != []:
        if len(HR) > 0:
            HR_Last = str(HR[0][1].valueQuantity.value) + str(HR[0][1].valueQuantity.code)
            if len(HR) > 1:
                HR_Trend = str(HR[0][1].valueQuantity.value - HR[1][1].valueQuantity.value)
            else:
                HR_Trend = "None"
        else:
            HR_Last = "None"
    else:
        HR_Last = "None"
        HR_Trend = "None"
    Smoking = MakeOrder(Smoking)
    if Smoking != []:

        if len(Smoking) > 0:
            Smoking_Last = str(int(Smoking[0][1].valueQuantity.value)) + str(Smoking[0][1].valueQuantity.unit)
            if len(HR) > 1:
                Smoking_Trend = str(int(Smoking[0][1].valueQuantity.value - Smoking[1][1].valueQuantity.value))
            else:
                Smoking_Trend = "None"
        else:
            Smoking_Last = "None"
    else:
        Smoking_Last = "None"
        Smoking_Trend = "None"


    ##################################

    #Encounter_List = encounter.Encounter.where({'patient': NHINumber, '_include': ['Encounter:diagnosis', 'Encounter:serviceProvider'], '_sort': '-date'}).perform(smart.server)
    Encounter_List = encounter.Encounter.where({'patient': NHINumber, '_revinclude': 'Condition:encounter', '_sort': '-date'}).perform(smart.server)

    En_All_DataList = []
    En_In_DataList = []
    En_Out_DataList = []
    En_All_List = []
    Condition_TemList = []

    if Encounter_List.entry != None:
        Encounter_List = fetch_all_pages(Encounter_List)
        #Encounter_List = [e.resource for e in Encounter_List.entry]
        #可以尝试用include进行优化
        print("Encounter_List")
        print(len(Encounter_List))
        A = 0
        B = 0
        if len(Encounter_List)>0:
            for i in Encounter_List:
                if i.resource_type == "Encounter":
                    En_All_List.append(i)
                if i.resource_type == "Condition":
                    Condition_TemList.append(i)
            print(len(En_All_List))
            for i in En_All_List:
                Condition_List = []

                if i.serviceProvider:
                    Organization_ID = i.serviceProvider.reference.split("/")
                    Organization_ID = Organization_ID[-1]
                    Organization_List = organization.Organization.where({'_id': Organization_ID}).perform(smart.server)
                    if Organization_List.entry != None:
                        Organization_List = [c.resource for c in Organization_List.entry]
                        if len(Organization_List) > 0:
                            Organization_Tem = Organization_List[0]
                            #Organization_BelongTo_ID = Organization_Tem.partOf.reference.split("/")
                            if Organization_Tem:
                                Organization_Tem = Organization_Tem.name
                            else:
                                Organization_Tem = "None"
                else:
                    Organization_Tem = "None"

                En_id = i.id
                tem_str = ""

                for c in Condition_TemList:
                    Encounter_Tem = c.encounter.reference.split("/")
                    Encounter_Tem = Encounter_Tem[-1]
                    if Encounter_Tem == En_id:
                        Condition_List.append(c)
                T_Start = i.period.start.isostring

                try:
                    T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%dT%H:%M:%S%z").strftime(
                        "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d %H:%M:%S").strftime(
                            "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d").strftime("%Y-%m-%d")

                T_End = i.period.end.isostring
                try:
                    T_End = datetime.datetime.strptime(T_End, "%Y-%m-%dT%H:%M:%S%z").strftime(
                        "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        T_End = datetime.datetime.strptime(T_End, "%Y-%m-%d %H:%M:%S").strftime(
                            "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        T_End = datetime.datetime.strptime(T_End, "%Y-%m-%d").strftime("%Y-%m-%d")

                if Condition_List != None:
                    A += 1
                    if len(Condition_List) > 0:
                        tem = []
                        for c in Condition_List:

                            for disease in c.code.coding:
                                if tem_str == "":
                                    tem_str += disease.display
                                else:
                                    tem_str += "; " + disease.display


                        if i.class_fhir.code == "IMP" or i.class_fhir.code == "ACUTE" or i.class_fhir.code == "NONAC":
                            tem = [i.id, "Inpatient", T_Start, T_End,
                                   Organization_Tem, tem_str]
                        else:
                            tem = [i.id, "Outpatient", T_Start, T_End,
                                   Organization_Tem, tem_str]
                        En_All_DataList.append(tem)
                    else:
                        B += 1
                        if i.class_fhir.code == "IMP" or i.class_fhir.code == "ACUTE" or i.class_fhir.code == "NONAC":
                            tem = [i.id, "Inpatient", T_Start, T_End,
                                   Organization_Tem, "None"]
                        else:
                            tem = [i.id, "Outpatient", T_Start, T_End,
                                   Organization_Tem, "None"]
                        En_All_DataList.append(tem)

            En_All_DataList.sort(key=lambda x: x[2], reverse=True)
            print(len(En_All_DataList))
            print(A, B)
    print("########END############")


    if request.method == "POST":
        pass
    else:
        return render(request, 'index.html', locals())
@log_Ation('Record health daily data')
def phr(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    NHINumber = request.session['NHINumber']
    smart = client.FHIRClient(settings=settings)
    p1 = Patient.read(NHINumber, smart.server)
    p1_Name = smart.human_name(p1.name[0])
    c_time = time.ctime()
    age = str(int(c_time[-4:]) - int(p1.birthDate.isostring[0:4]))

    Photo="/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBAUEBAYFBQUGBgYHCQ4JCQgICRINDQoOFRIWFhUSFBQXGiEcFxgfGRQUHScdHyIjJSUlFhwpLCgkKyEkJST/2wBDAQYGBgkICREJCREkGBQYJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCQkJCT/wAARCAIAAgADAREAAhEBAxEB/8QAHQABAAICAwEBAAAAAAAAAAAAAAcIAQYEBQkDAv/EAE4QAAEDAwIDBQUEBQgHBwUBAAEAAgMEBREGIQcSMQgTQVFhFCIycYEVI0KRFlJygqEkM2KSorHBwkNTY3Oy0fAXJSZUk6OzNIPD4fHT/8QAFAEBAAAAAAAAAAAAAAAAAAAAAP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/ALOoCAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICANzgbk+A6oOHdr3a7DT+03e5UNtgPSWsnZC313eQg0e9doXhdY3PjqNYUVRI3IDaGOSqDsDoHRtLfqT9UGnXDtjcPqXmZTW/UdZIBlrmU0UcZPkS6TI+eCg1ip7blHG/FNoWedn60t0EZ/JsR/vQdTU9te7vlzTaPtsUf6stZI8/mAB/BBxX9tPU5/m9MWM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wwOIzvhBa/hf2atI8Pu5r66Nt/vTMOFVVxjuoHZODFEcgEe77zi52RkcvRBLxJOSSSfElBhAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQdXqLS1j1bbnW2/WqjudI4kiKoj5gw4xzNPVh36twfVBXziD2NqKqMlZoW7exPOT9nXJxfF16MmALmgDoHB2/VwQV51lww1hoGTGo7BWUMZIDajlD4Hk9AJWEsJ9M59EGqoMICAgICAgICAgICAgICAgIP2ATjA38PVBKOh+zZxD1qY5/sn7FoHjPtV1zDkDB92PBkdkHIPLg+YQWO0F2VdDaRMdTd436mr2YPPXMDacEZ3EAJBGD0eX9PBBMkbGxsaxjQxrAGta0YDRjAAHgAPAbIP0gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICD8yRsljfFI1r45AWvY4Za4HrkEHI9CEEX6u7NPDXVpdKLKbLUux9/aHiAfLuyDH+Tc+qCFtT9jDUdFzzab1BbrpGAXdzVsdSy+jQRzMJ9SWhBEmo+D+v9Jl/2xpK7QMYMvnihM0IH+8j5mfxQad1QCMIMICAgICAgICDOPyQciioKu5VLKahpZ6qof8MUEZe93yA3QSPpjs28TNTuY5unZbVTuPKZ7q4UwYfVjvvD9GlBL2kuxbRw93Nq3U0tQ7HvUtrj7tocP9tICSPkwH1QTdo/hTonQRbJp7TlDSVDc4qntM1RuMH715LgD5AgeiDbOpOcknqT1KAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAy34SRnrg4QdJftD6X1QXPvmnLPcpHNI72qo2PkA9Hkcw+YKDQL12WeFt2a4w2WqtcjySZKGtkHXybIXNGOuAAEGn3XsV6ZmyLTqm80m2xq4YqjB8zy8mR6INbr+xNcYzig1pRVA856CSLH9VzkHTzdi7XQkPcX3Sz4/AvnnYT9O6P96D4v7GXEFnS76Vf8qub/ABhCDLexfxAIybzpMfOrn/8A8UHKpOxbrA59t1Fp2LfbuDPL/kag76h7EhIa+u1y1pzl0VPbCdvIOdIP4hBtFs7GuhaZrH1931DWytJLgyWGGN/pgMLh9HIN2svZ54XWJ0ckGkKOokbjLq6SSpDiPNsjiz8h9EG92u02+yUoo7VQUlvph0hpIWwsH7rQB0CDleJPiepQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQf//Z"
    if p1.photo is not None:
        Photo =  p1.photo[0].data
    print(p1.gender, p1.birthDate.isostring, age, p1.address)
    if p1.address:
        Address = p1.address[0].line[0] + "," + p1.address[0].city + "," + p1.address[0].country
    if p1.telecom:
        if p1.telecom[0]:
            Phone = p1.telecom[0].value
        else:
            Phone = "None"
        if len(p1.telecom)==2:
            Email = p1.telecom[1].value
        else:
            Email = "None"
    else:
        Phone = "None"
        Email = "None"

    BirthDate = p1.birthDate.isostring
    Observation = observation.Observation.where({'patient': NHINumber, '_sort': '-date'}).perform(smart.server)

    Weight_List = []
    Height_List = []
    if Observation.entry != None:
        Observation = fetch_all_pages(Observation)
        #Observation = [ob.resource for ob in Observation.entry]
        #可以尝试用include进行优化
        if len(Observation)>0:
            for Ob in Observation:
                if Ob.code.coding[0].code == '29463-7':
                    Weight_List.append(Ob)
                elif Ob.code.coding[0].code == '8302-2':
                    Height_List.append(Ob)

        if len(Weight_List)>0:
            Weight = Weight_List[0]
            Weight_Name = Weight.code.text
            Weight_Last = str(Weight.valueQuantity.value) + Weight.valueQuantity.unit
        else:
            Weight = "None"
        if len(Height_List)>0:
            Height = Height_List[0]
            Height_Name = Height.code.text
            Height_Last = str(Height.valueQuantity.value) + Height.valueQuantity.unit
        else:
            Height = "None"

    p_id = request.session['patient_id']
    patient = models.Patient.objects.filter(cid=p_id)
    if len(patient) > 1:
        patient = patient.get(name=request.session['patient_name'])
    else:
        patient = patient[0]
    organization_id = patient.organization_id
    """time_data = patient.get_list("r_time")
    if request.session['is_new'] == False:
        your_number = int(request.session['number'])
        tem_date = time_data[your_number]"""
    if request.method == "POST":
        phr_form = form.NameForm(request.POST)
        message = 'Please write your information!'

        if request.session['user_name']:
            your_name = request.session['user_name']
        your_date = request.POST.get('your_date')
        your_height = request.POST.get('your_height')
        your_weight = request.POST.get('your_weight')
        your_temperature = request.POST.get('your_temperature')
        your_steps = request.POST.get('your_steps')
        your_BMI = request.POST.get('your_BMI')
        your_bp_up = request.POST.get('your_blood_pressure_up')
        your_bp_down = request.POST.get('your_blood_pressure_down')
        your_pr = request.POST.get('your_pulse_rate')
        your_respiration = request.POST.get('your_respiration')
        your_smoking = request.POST.get('your_smoking')

        regInt = '^0$|^[1-9]\d*$'
        regFloat = '^0\.\d+$|^[1-9]\d*\.\d+$'
        IntOrFloat = regInt + '|' + regFloat
        patternIntOrFloat = re.compile(IntOrFloat)
        patternInt = re.compile(regInt)
        date = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        date = date[:-2] + ":" + date[-2:]
        if your_smoking:
            print("your_smoking")
            if patternInt.search(your_smoking):
                your_smoking = float(your_smoking)
                if float(your_smoking) < 0:
                    message = "Wrong Smoking data!(0<Smoking)"
                    return render(request, 'phr_change.html', locals())
                else:
                    Smoking = create_Smoking(your_smoking, p1.id, date, organization_id)
                    response = Smoking.create(smart.server)
                    if response:
                        print(f"Created Smoking with id: {response['id']}")
                    else:
                        print("Failed to create Steps")
            else:
                message = "Data is not numeric!"
                return render(request, 'phr_change.html', locals())
        if your_steps:
            print("your_steps")
            if patternInt.search(your_steps):
                your_steps = float(your_steps)
                if float(your_steps) < 0:
                    message = "Wrong Steps data!(0<Steps)"
                    return render(request, 'phr_change.html', locals())
                else:
                    Steps = create_Steps(your_steps, p1.id, date, organization_id)
                    print(Steps.as_json())
                    response = Steps.create(smart.server)
                    if response:
                        print(f"Created Steps with id: {response['id']}")
                    else:
                        print("Failed to create Steps")
            else:
                message = "Data is not numeric!"
                return render(request, 'phr_change.html', locals())
        if your_BMI:
            print("your_BMI")
            if patternIntOrFloat.search(your_BMI):
                your_BMI = float(your_BMI)
                if float(your_BMI) > 50 or float(your_BMI) < 0:
                    message = "Wrong BMI data!(0<BMI<50)"
                    return render(request, 'phr_change.html', locals())
                else:
                    BMI = create_BMI(your_BMI, p1.id, date, organization_id)
                    response = BMI.create(smart.server)
                    if response:
                        print(f"Created BMI with id: {response['id']}")
                    else:
                        print("Failed to create BMI")
            else:
                message = "Data is not numeric or decimal!"
                return render(request, 'phr_change.html', locals())
        if your_respiration:
            print("your_respiration")
            if patternIntOrFloat.search(your_respiration):
                your_respiration = float(your_respiration)
                if float(your_respiration) > 80 or float(your_respiration) < 0:
                    message = "Wrong respiration data!(0<respiration<80)"
                    return render(request, 'phr_change.html', locals())
                else:
                    Respiration = create_RespiratoryRate(your_respiration, p1.id, date, organization_id)
                    response = Respiration.create(smart.server)
                    if response:
                        print(f"Created Respiration with id: {response['id']}")
                    else:
                        print("Failed to create Respiration")
            else:
                message = "Data is not numeric or decimal!"
                return render(request, 'phr_change.html', locals())
        if your_height:
            print("your_height")
            if patternIntOrFloat.search(your_height):
                your_height = float(your_height)
                if float(your_height) > 300 or float(your_height) < 0:
                    message = "Wrong height data!(0<height<300)"
                    return render(request, 'phr_change.html', locals())
                else:
                    Height = create_BodyHeight(your_height, p1.id, date, organization_id)
                    response = Height.create(smart.server)
                    if response:
                        print(f"Created Height with id: {response['id']}")
                    else:
                        print("Failed to create Height")
            else:
                message = "Data is not numeric or decimal!"
                return render(request, 'phr_change.html', locals())
        if your_weight:
            print("your_weight")
            if patternIntOrFloat.search(your_weight):
                your_weight = float(your_weight)
                if float(your_weight) > 300 or float(your_weight) < 0:
                    message = "Wrong weight data!(0<weight<300)"
                    return render(request, 'phr_change.html', locals())
                else:
                    Weight = create_BodyWeight(your_weight, p1.id, date, organization_id)
                    response = Weight.create(smart.server)
                    if response:
                        print(f"Created Weight with id: {response['id']}")
                    else:
                        print("Failed to create Weight")
            else:
                message = "Data is not numeric or decimal!"
                return render(request, 'phr_change.html', locals())

        if your_pr:
            print("your_hr")
            if patternIntOrFloat.search(your_pr):
                your_pr = float(your_pr)
                if float(your_pr) > 250 or float(your_pr) < 0:
                    message = "Wrong heart rate data!(0<heart rate<250)"
                    return render(request, 'phr_change.html', locals())
                else:
                    Pulse = create_HeartRate(your_pr, p1.id, date, organization_id)
                    response = Pulse.create(smart.server)
                    if response:
                        print(f"Created Pulse with id: {response['id']}")
                    else:
                        print("Failed to create Pulse")
            else:
                message = "Data is not numeric or decimal!"
                return render(request, 'phr_change.html', locals())

        if your_temperature:
            print("your_temperature")
            if patternIntOrFloat.search(your_temperature):
                your_temperature = float(your_temperature)
                if float(your_temperature) > 50 or float(your_temperature) < 0:
                    message = "Wrong temperature data!(0<temperature<50)"
                    return render(request, 'phr_change.html', locals())
                else:

                    Temperature = create_BodyTemp(your_temperature, p1.id, date, organization_id)
                    response = Temperature.create(smart.server)
                    if response:
                        print(f"Created Temperature with id: {response['id']}")
                    else:
                        print("Failed to create Temperature")
            else:
                message = "Data is not numeric or decimal!"
                return render(request, 'phr_change.html', locals())

        if your_bp_up and your_bp_down:
            print("your_bp_up")
            if patternIntOrFloat.search(your_bp_up) and patternIntOrFloat.search(your_bp_down):
                your_bp_up = float(your_bp_up)
                your_bp_down = float(your_bp_down)
                if float(your_bp_up) > 250 or float(your_bp_up) < 50:
                    message = "Wrong Systolic blood pressure data!(50<upper blood pressure<250)"
                    return render(request, 'phr_change.html', locals())
                elif float(your_bp_down) > 250 or float(your_bp_down) < 50:
                    message = "Wrong Diastolic blood pressure data!(50<lower blood pressure<250)"
                    return render(request, 'phr_change.html', locals())
                else:
                    patient.blood_pressure_up = your_bp_up
                    Weight = create_BloodPressure(your_bp_up, your_bp_down, p1.id, date, organization_id)
                    response = Weight.create(smart.server)
                    if response:
                        print(f"Created Weight with id: {response['id']}")
                    else:
                        print("Failed to create Weight")
            else:
                message = "Data is not numeric or decimal!"
                return render(request, 'phr_change.html', locals())

        return HttpResponseRedirect('/PHR/index/')

    else:
        phr_form = form.NameForm()
        print("322")
    return render(request, 'phr_change.html', locals())





def register(request):

    if request.method == 'POST':

        register_form = form.RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password1 = register_form.cleaned_data.get('password1')
            password2 = register_form.cleaned_data.get('password2')
            NHINumber = register_form.cleaned_data.get('NHINumber')
            phoneNumber = register_form.cleaned_data.get('phoneNumber')
            organization_id = "dea39875-4931-43b5-9d3b-6d52142b1cc5"
            if password2 != password1:

                message = 'Password not same!'
                return render(request, 'register.html', locals())
            else:
                same_username = models.User.objects.filter(username=username)
                if same_username:
                    message = 'This user name already exists!'
                    return render(request, 'register.html', locals())
                new_user = models.User()
                new_user.username = username
                new_user.password = hash_code(password1)

                new_patient = models.Patient()
                new_user.save()
                new_patient.cid = new_user
                new_patient.NHINumber = NHINumber
                new_patient.phoneNumber = phoneNumber
                new_patient.organization_id = organization_id
                new_patient.save()
                new_patient.add_time = new_patient.cc_time.strftime("%Y-%m-%d %H:%M:%S")
                new_patient.save()

                return redirect('/PHR/login/')
        else:

            return render(request, 'register.html', locals())
    register_form = form.RegisterForm()

    return render(request, 'register.html', locals())

def login(request):
    if request.session.get('is_login', None):
        print(request.session.get('is_login', None))
        return redirect('/PHR/index/')
    if request.method == "POST":
        login_form = form.UserForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')

            try:
                print(username)
                user = models.User.objects.get(username=username)
            except:
                message = 'User not exist!'
                """return render(request, 'PHR/login.html', locals())"""
                return render(request, 'login.html', {'message': message, 'login_form': login_form})
            if user.password == hash_code(password):
                pid = user.u_id
                print(pid)

                patient = models.Patient.objects.filter(cid=pid)
                patient = patient[0]
                print("666")
                request.session['is_login'] = True
                print(request.session.get('is_login', None))
                request.session['user_id'] = user.username
                request.user = username
                request.session['user_name'] = patient.name
                #request.session['patient_id'] = user.get_list("pid")[0]
                p_tem = models.Patient.objects.filter(cid_id=user.u_id)
                request.session['patient_id'] = p_tem[0].cid_id
                request.session["patient_name"] = p_tem[0].name
                return redirect('/PHR/index/')
            else:
                message = 'Password not correct!'
                return render(request, 'login.html', {'message': message, 'login_form': login_form})
        else:
            return render(request, 'login.html', {'login_form': login_form})
    login_form = form.UserForm()
    return render(request, 'login.html', locals())

def logout(request):
    if not request.session.get('is_login', None):
        return redirect("/PHR/login/")
    request.session.flush()
    return redirect("/PHR/login/")
@log_Ation('Weight record')
def WeightRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Weight"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Weight = observation.Observation.where({'patient': NHINumber, 'code': '29463-7', '_sort': '-date'}).perform(smart.server)
    Weight_tem = []
    Weight_TimeList = []
    Weight_DataList = []
    Weight_YearDic = {}
    Weight_MonthDic = {}
    Weight_DayDic = {}
    Weight_DataList1 = []
    Weight_DataList2 = []
    # one month
    Weight_DataList3 = []
    # one years
    Weight_DataList4 = []
    # all
    Weight_DataList5 = []
    if Weight.entry != None:
        Weight = fetch_all_pages(Weight)
        #Weight = [ob.resource for ob in Weight.entry]
        if len(Weight) > 0:
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Weight:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        Weight_tem.append(i)
            Weight = Weight_tem
            for i in Weight:
                print("Weight Test-----------------")
                if i.effectiveDateTime != None:
                    Weight_TimeList.append(i.effectiveDateTime.isostring)
                    # Height_DataList.append(str(i.valueQuantity.value) + " " + i.valueQuantity.unit)
                    Weight_DataList.append(float(i.valueQuantity.value))

            if Weight_TimeList != []:
                for i in range(len(Weight_TimeList)):
                    #Height_TimeList[i] = Height_TimeList[i][:-1]
                    #Height_TimeList[i] = Height_TimeList[i][:10] + " " + Height_TimeList[i][11:]
                    Weight_DataList1.append([Weight_TimeList[i], Weight_DataList[i]])
                    Weight_DataList1.reverse()
                    Weight_DataList2.append([Weight_TimeList[i], str(Weight_DataList[i])])

                try:
                    date_tem = datetime.datetime.strptime(Weight_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Weight_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Weight_TimeList[0], "%Y-%m-%d")
                try:
                    Weight_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Weight_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Weight_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Weight_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Weight_MonthTem)
                Weight_DataList1.sort(key=lambda x: x[0])
                Weight_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Weight_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Weight_DayDic:
                        Weight_DayDic[str(date_tem.date())].append(data)
                    else:
                        Weight_DayDic[str(date_tem.date())] = [data]
                for time, value in Weight_DayDic.items():
                    average = sum(value) / len(value)
                    Weight_DataList5.append([time, average])
                for t, data in Weight_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Weight_MonthTem:
                        Weight_DataList3.append([t, data])
                    if date_tem > Weight_YearTem:
                        Weight_DataList4.append([t,data])
                print(Weight_YearDic, Weight_MonthDic, Weight_DayDic)
                print(Weight_DataList3,Weight_DataList4,Weight_DataList5)
            Weight_DataList1 = json.dumps(Weight_DataList1)
            Weight_DataList3 = json.dumps(Weight_DataList3)
            Weight_DataList4 = json.dumps(Weight_DataList4)
            Weight_DataList5 = json.dumps(Weight_DataList5)
    return render(request, 'Weight_Record.html', locals())
@log_Ation('Height record')
def HeightRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }

    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Height"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Height = observation.Observation.where({'patient': NHINumber, 'code': '8302-2', '_sort': '-date'}).perform(smart.server)
    Height_TimeList = []
    Height_DataList = []
    Height_YearDic = {}
    Height_MonthDic = {}
    Height_DayDic = {}
    Height_DataList1 = []
    Height_DataList2 = []
    # one month
    Height_DataList3 = []
    # one years
    Height_DataList4 = []
    # all
    Height_DataList5 = []
    if Height.entry != None:
        Height = fetch_all_pages(Height)
        #Height = [ob.resource for ob in Height.entry]
        Height_tem = []
        if len(Height)>0:
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Height:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        Height_tem.append(i)
            Height = Height_tem

            for i in Height:
                print("Height Test-----------------")
                if i.effectiveDateTime != None:
                    Height_TimeList.append(i.effectiveDateTime.isostring)
                    # Height_DataList.append(str(i.valueQuantity.value) + " " + i.valueQuantity.unit)
                    Height_DataList.append(float(i.valueQuantity.value))

            if Height_TimeList != []:
                for i in range(len(Height_TimeList)):
                    #Height_TimeList[i] = Height_TimeList[i][:-1]
                    #Height_TimeList[i] = Height_TimeList[i][:10] + " " + Height_TimeList[i][11:]
                    Height_DataList1.append([Height_TimeList[i], Height_DataList[i]])
                    Height_DataList1.reverse()
                    Height_DataList2.append([Height_TimeList[i], str(Height_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Height_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Height_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Height_TimeList[0], "%Y-%m-%d")
                try:
                    Height_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Height_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Height_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Height_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Height_MonthTem)
                Height_DataList1.sort(key=lambda x: x[0])
                Height_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Height_DataList1:
                    print(t,data)

                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Height_DayDic:
                        Height_DayDic[str(date_tem.date())].append(data)
                    else:
                        Height_DayDic[str(date_tem.date())] = [data]
                for time, value in Height_DayDic.items():
                    average = sum(value) / len(value)
                    Height_DataList5.append([time, average])
                for t, data in Height_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Height_MonthTem:
                        Height_DataList3.append([t, data])
                    if date_tem > Height_YearTem:
                        Height_DataList4.append([t,data])
                print(Height_YearDic, Height_MonthDic, Height_DayDic)
                print(Height_DataList3,Height_DataList4,Height_DataList5)
            Height_DataList1 = json.dumps(Height_DataList1)
            Height_DataList3 = json.dumps(Height_DataList3)
            Height_DataList4 = json.dumps(Height_DataList4)
            Height_DataList5 = json.dumps(Height_DataList5)
    return render(request, 'Height_Record.html', locals())
@log_Ation('Temperature record')
def TemperatureRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Temperature"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Temperature = observation.Observation.where({'patient': NHINumber, 'code': '8310-5', '_sort': '-date'}).perform(smart.server)
    Temperature_TimeList = []
    Temperature_DataList = []
    Temperature_YearDic = {}
    Temperature_MonthDic = {}
    Temperature_DayDic = {}
    Temperature_DataList1 = []
    Temperature_DataList2 = []
    # one month
    Temperature_DataList3 = []
    # one years
    Temperature_DataList4 = []
    # all
    Temperature_DataList5 = []
    if Temperature.entry != None:
        Temperature = fetch_all_pages(Temperature)
        #Temperature = [ob.resource for ob in Temperature.entry]
        if len(Temperature)>0:
            Temperature_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Temperature:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        Temperature_tem.append(i)
            Temperature = Temperature_tem

            for i in Temperature:
                print("Temperature Test-----------------")
                if i.effectiveDateTime != None:
                    Temperature_TimeList.append(i.effectiveDateTime.isostring)

                    Temperature_DataList.append(float(i.valueQuantity.value))

            if Temperature_TimeList != []:
                for i in range(len(Temperature_TimeList)):

                    Temperature_DataList1.append([Temperature_TimeList[i], Temperature_DataList[i]])
                    Temperature_DataList1.reverse()
                    Temperature_DataList2.append([Temperature_TimeList[i], str(Temperature_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%d")
                try:
                    Temperature_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Temperature_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Temperature_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Temperature_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Temperature_MonthTem)
                Temperature_DataList1.sort(key=lambda x: x[0])
                Temperature_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Temperature_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Temperature_DayDic:
                        Temperature_DayDic[str(date_tem.date())].append(data)
                    else:
                        Temperature_DayDic[str(date_tem.date())] = [data]
                for time, value in Temperature_DayDic.items():
                    average = sum(value) / len(value)
                    Temperature_DataList5.append([time, average])
                for t, data in Temperature_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Temperature_MonthTem:
                        Temperature_DataList3.append([t, data])
                    if date_tem > Temperature_YearTem:
                        Temperature_DataList4.append([t,data])
                print(Temperature_YearDic, Temperature_MonthDic, Temperature_DayDic)
                print(Temperature_DataList3,Temperature_DataList4,Temperature_DataList5)
            Temperature_DataList1 = json.dumps(Temperature_DataList1)
            Temperature_DataList3 = json.dumps(Temperature_DataList3)
            Temperature_DataList4 = json.dumps(Temperature_DataList4)
            Temperature_DataList5 = json.dumps(Temperature_DataList5)
    return render(request, 'Temperature_Record.html', locals())
@log_Ation('Steps record')
def StepsRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Steps"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Steps = observation.Observation.where({'patient': NHINumber, 'code': '41950-7', '_sort': '-date'}).perform(smart.server)
    Steps_TimeList = []
    Steps_DataList = []
    Steps_YearDic = {}
    Steps_MonthDic = {}
    Steps_DayDic = {}
    Steps_DataList1 = []
    Steps_DataList2 = []
    # one month
    Steps_DataList3 = []
    # one years
    Steps_DataList4 = []
    # all
    Steps_DataList5 = []
    if Steps.entry != None:
        Steps = fetch_all_pages(Steps)
        #Steps = [ob.resource for ob in Steps.entry]
        if len(Steps)>0:
            Steps_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Steps:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        Steps_tem.append(i)
            Steps = Steps_tem
            for i in Steps:
                print("Steps Test-----------------")
                if i.effectiveDateTime != None:
                    Steps_TimeList.append(i.effectiveDateTime.isostring)

                    Steps_DataList.append(float(i.valueQuantity.value))

            if Steps_TimeList != []:
                for i in range(len(Steps_TimeList)):

                    Steps_DataList1.append([Steps_TimeList[i], Steps_DataList[i]])
                    Steps_DataList1.reverse()
                    Steps_DataList2.append([Steps_TimeList[i], str(Steps_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Steps_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Steps_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Steps_TimeList[0], "%Y-%m-%d")
                try:
                    Steps_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Steps_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Steps_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Steps_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Steps_MonthTem)
                Steps_DataList1.sort(key=lambda x: x[0])
                Steps_DataList2.sort(key=lambda x: x[0], reverse=True)

                for t, data in Steps_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")


                    if str(date_tem.date()) in Steps_DayDic:
                        Steps_DayDic[str(date_tem.date())].append(data)
                    else:
                        Steps_DayDic[str(date_tem.date())] = [data]
                for time, value in Steps_DayDic.items():
                    average = sum(value) / len(value)
                    Steps_DataList5.append([time, average])
                for t, data in Steps_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Steps_MonthTem:
                        Steps_DataList3.append([t, data])
                    if date_tem > Steps_YearTem:
                        Steps_DataList4.append([t,data])
                print(Steps_YearDic, Steps_MonthDic, Steps_DayDic)
                print(Steps_DataList3,Steps_DataList4,Steps_DataList5)
            Steps_DataList1 = json.dumps(Steps_DataList1)
            Steps_DataList3 = json.dumps(Steps_DataList3)
            Steps_DataList4 = json.dumps(Steps_DataList4)
            Steps_DataList5 = json.dumps(Steps_DataList5)
    return render(request, 'Steps_Record.html', locals())
@log_Ation('BMI record')
def BMIRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["BMI"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    BMI = observation.Observation.where({'patient': NHINumber, 'code': '39156-5', '_sort': '-date'}).perform(smart.server)
    BMI_TimeList = []
    BMI_DataList = []
    BMI_YearDic = {}
    BMI_MonthDic = {}
    BMI_DayDic = {}
    BMI_DataList1 = []
    BMI_DataList2 = []
    # one month
    BMI_DataList3 = []
    # one years
    BMI_DataList4 = []
    # all
    BMI_DataList5 = []
    if BMI.entry != None:
        BMI = fetch_all_pages(BMI)
        #BMI = [ob.resource for ob in BMI.entry]
        if len(BMI)>0:
            BMI_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in BMI:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        BMI_tem.append(i)
            BMI = BMI_tem
            for i in BMI:
                print("BMI Test-----------------")
                if i.effectiveDateTime != None:
                    BMI_TimeList.append(i.effectiveDateTime.isostring)

                    BMI_DataList.append(float(i.valueQuantity.value))

            if BMI_TimeList != []:
                for i in range(len(BMI_TimeList)):

                    BMI_DataList1.append([BMI_TimeList[i], BMI_DataList[i]])
                    BMI_DataList1.reverse()
                    BMI_DataList2.append([BMI_TimeList[i], str(BMI_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(BMI_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(BMI_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(BMI_TimeList[0], "%Y-%m-%d")
                try:
                    BMI_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BMI_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    BMI_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BMI_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(BMI_MonthTem)
                BMI_DataList1.sort(key=lambda x: x[0])
                BMI_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in BMI_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in BMI_DayDic:
                        BMI_DayDic[str(date_tem.date())].append(data)
                    else:
                        BMI_DayDic[str(date_tem.date())] = [data]
                for time, value in BMI_DayDic.items():
                    average = sum(value) / len(value)
                    BMI_DataList5.append([time, average])
                for t, data in BMI_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > BMI_MonthTem:
                        BMI_DataList3.append([t, data])
                    if date_tem > BMI_YearTem:
                        BMI_DataList4.append([t,data])
                print(BMI_YearDic, BMI_MonthDic, BMI_DayDic)
                print(BMI_DataList3,BMI_DataList4,BMI_DataList5)
            BMI_DataList1 = json.dumps(BMI_DataList1)
            BMI_DataList3 = json.dumps(BMI_DataList3)
            BMI_DataList4 = json.dumps(BMI_DataList4)
            BMI_DataList5 = json.dumps(BMI_DataList5)
    return render(request, 'BMI_Record.html', locals())
@log_Ation('Blood pressure record')
def BloodPressureRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    # higher lower
    Legend_Data = ["Systolic Blood Pressure", "Diastolic Blood Pressure"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    """if BP.entry != None:
        BP = [ob.resource for ob in BP.entry]
        if len(BP) > 0:
            BP_Last = str(str(BP[0].component[0].valueQuantity.value) + "/" + str(BP[0].component[1].valueQuantity.value))
            if len(BP) > 1:
                BP_Trend = str(BP[0].component[0].valueQuantity.value - BP[1].component[0].valueQuantity.value) + "/" + str(BP[0].component[1].valueQuantity.value - BP[1].component[1].valueQuantity.value)
            else:
                BP_Trend = "None"
        else:
            BP_Last = "None"
    else:
        BP_Last = "None"
        BP_Trend = "None"
        """
    NHINumber = request.session['NHINumber']
    BloodPressure = observation.Observation.where({'patient': NHINumber, 'code': '85354-9', '_sort': '-date'}).perform(smart.server)
    BloodPressure_TimeList = []
    # lower
    DiastolicBloodPressure_DataList = []
    DiastolicBloodPressure_YearDic = {}
    DiastolicBloodPressure_MonthDic = {}
    DiastolicBloodPressure_DayDic = {}
    # higher
    SystolicBloodPressure_DataList = []
    SystolicBloodPressure_YearDic = {}
    SystolicBloodPressure_MonthDic = {}
    SystolicBloodPressure_DayDic = {}
    SystolicBloodPressure_DataList1 = []
    # SystolicBloodPressure_DataList2 = []
    DiastolicBloodPressure_DataList1 = []
    # DiastolicBloodPressure_DataList2 = []
    BloodPressure_DataList2 = []

    # one month
    SystolicBloodPressure_DataList3 = []
    # one years
    SystolicBloodPressure_DataList4 = []
    # all
    SystolicBloodPressure_DataList5 = []
    # one month
    DiastolicBloodPressure_DataList3 = []
    # one years
    DiastolicBloodPressure_DataList4 = []
    # all
    DiastolicBloodPressure_DataList5 = []
    if BloodPressure.entry != None:
        BloodPressure = fetch_all_pages(BloodPressure)
        #BloodPressure = [ob.resource for ob in BloodPressure.entry]
        if len(BloodPressure)>0:
            BloodPressure_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in BloodPressure:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        BloodPressure_tem.append(i)
            BloodPressure = BloodPressure_tem
            for i in BloodPressure:
                print("BloodPressure Test-----------------")
                if i.effectiveDateTime != None:
                    BloodPressure_TimeList.append(i.effectiveDateTime.isostring)
                    for o in i.component:
                        code_List = o.code.coding
                        for code in code_List:
                            if code.code == "8480-6" or code.code == "271649006" or code.code == "bp-s":
                                SystolicBloodPressure_DataList.append(float(o.valueQuantity.value))
                                print("8480-6")
                            if code.code == "8462-4":
                                DiastolicBloodPressure_DataList.append(float(o.valueQuantity.value))
                                print("8462-4")
                        print(o.valueQuantity.value)

            if BloodPressure_TimeList != []:
                for i in range(len(BloodPressure_TimeList)):
                    print(BloodPressure_TimeList)
                    print(SystolicBloodPressure_DataList)
                    SystolicBloodPressure_DataList1.append([BloodPressure_TimeList[i], SystolicBloodPressure_DataList[i]])
                    SystolicBloodPressure_DataList1.reverse()


                    DiastolicBloodPressure_DataList1.append([BloodPressure_TimeList[i], DiastolicBloodPressure_DataList[i]])
                    DiastolicBloodPressure_DataList1.reverse()

                    BloodPressure_DataList2.append([BloodPressure_TimeList[i], str(SystolicBloodPressure_DataList[i]), str(DiastolicBloodPressure_DataList[i])])

                try:
                    date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%d")
                try:
                    BloodPressure_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BloodPressure_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    BloodPressure_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BloodPressure_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(BloodPressure_MonthTem)
                SystolicBloodPressure_DataList1.sort(key=lambda x: x[0])
                BloodPressure_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in SystolicBloodPressure_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if str(date_tem.date()) in SystolicBloodPressure_DayDic:
                        SystolicBloodPressure_DayDic[str(date_tem.date())].append(data)
                    else:
                        SystolicBloodPressure_DayDic[str(date_tem.date())] = [data]
                for time, value in SystolicBloodPressure_DayDic.items():
                    average = sum(value) / len(value)
                    SystolicBloodPressure_DataList5.append([time, average])
                for t, data in SystolicBloodPressure_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > BloodPressure_MonthTem:
                        SystolicBloodPressure_DataList3.append([t, data])
                    if date_tem > BloodPressure_YearTem:
                        SystolicBloodPressure_DataList4.append([t,data])
                DiastolicBloodPressure_DataList1.sort(key=lambda x: x[0])
                BloodPressure_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in DiastolicBloodPressure_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if str(date_tem.date()) in DiastolicBloodPressure_DayDic:
                        DiastolicBloodPressure_DayDic[str(date_tem.date())].append(data)
                    else:
                        DiastolicBloodPressure_DayDic[str(date_tem.date())] = [data]
                for time, value in DiastolicBloodPressure_DayDic.items():
                    average = sum(value) / len(value)
                    DiastolicBloodPressure_DataList5.append([time, average])
                for t, data in DiastolicBloodPressure_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > BloodPressure_MonthTem:
                        DiastolicBloodPressure_DataList3.append([t, data])
                    if date_tem > BloodPressure_YearTem:
                        DiastolicBloodPressure_DataList4.append([t,data])
                #print(BloodPressure_YearDic, BloodPressure_MonthDic, BloodPressure_DayDic)
                #print(BloodPressure_DataList3,BloodPressure_DataList4,BloodPressure_DataList5)

                #BloodPressure_DataList1 = json.dumps(BloodPressure_DataList1)
            SystolicBloodPressure_DataList3 = json.dumps(SystolicBloodPressure_DataList3)
            SystolicBloodPressure_DataList4 = json.dumps(SystolicBloodPressure_DataList4)
            SystolicBloodPressure_DataList5 = json.dumps(SystolicBloodPressure_DataList5)

            DiastolicBloodPressure_DataList3 = json.dumps(DiastolicBloodPressure_DataList3)
            DiastolicBloodPressure_DataList4 = json.dumps(DiastolicBloodPressure_DataList4)
            DiastolicBloodPressure_DataList5 = json.dumps(DiastolicBloodPressure_DataList5)
    return render(request, 'BloodPressure_Record.html', locals())
@log_Ation('Height record')
def HeartRateRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["HeartRate"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    HeartRate = observation.Observation.where({'patient': NHINumber, 'code': '8867-4', '_sort': '-date'}).perform(smart.server)
    HeartRate_TimeList = []
    HeartRate_DataList = []
    HeartRate_YearDic = {}
    HeartRate_MonthDic = {}
    HeartRate_DayDic = {}
    HeartRate_DataList1 = []
    HeartRate_DataList2 = []
    # one month
    HeartRate_DataList3 = []
    # one years
    HeartRate_DataList4 = []
    # all
    HeartRate_DataList5 = []
    if HeartRate.entry != None:
        HeartRate = fetch_all_pages(HeartRate)
        #HeartRate = [ob.resource for ob in HeartRate.entry]
        if len(HeartRate)>0:
            HeartRate_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in HeartRate:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        HeartRate_tem.append(i)
            HeartRate = HeartRate_tem
            for i in HeartRate:
                print("HeartRate Test-----------------")
                if i.effectiveDateTime != None:
                    HeartRate_TimeList.append(i.effectiveDateTime.isostring)

                    HeartRate_DataList.append(float(i.valueQuantity.value))

            if HeartRate_TimeList != []:
                for i in range(len(HeartRate_TimeList)):

                    HeartRate_DataList1.append([HeartRate_TimeList[i], HeartRate_DataList[i]])
                    HeartRate_DataList1.reverse()
                    HeartRate_DataList2.append([HeartRate_TimeList[i], str(HeartRate_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%d")
                try:
                    HeartRate_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    HeartRate_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    HeartRate_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    HeartRate_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(HeartRate_MonthTem)
                HeartRate_DataList1.sort(key=lambda x: x[0])
                HeartRate_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in HeartRate_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in HeartRate_DayDic:
                        HeartRate_DayDic[str(date_tem.date())].append(data)
                    else:
                        HeartRate_DayDic[str(date_tem.date())] = [data]
                for time, value in HeartRate_DayDic.items():
                    average = sum(value) / len(value)
                    HeartRate_DataList5.append([time, average])
                for t, data in HeartRate_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > HeartRate_MonthTem:
                        HeartRate_DataList3.append([t, data])
                    if date_tem > HeartRate_YearTem:
                        HeartRate_DataList4.append([t,data])
                print(HeartRate_YearDic, HeartRate_MonthDic, HeartRate_DayDic)
                print(HeartRate_DataList3,HeartRate_DataList4,HeartRate_DataList5)
            HeartRate_DataList1 = json.dumps(HeartRate_DataList1)
            HeartRate_DataList3 = json.dumps(HeartRate_DataList3)
            HeartRate_DataList4 = json.dumps(HeartRate_DataList4)
            HeartRate_DataList5 = json.dumps(HeartRate_DataList5)
    return render(request, 'HeartRate_Record.html', locals())
@log_Ation('Respiration record')
def RespirationRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Respiration"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Respiration = observation.Observation.where({'patient': NHINumber, 'code': '9279-1', '_sort': '-date'}).perform(smart.server)
    Respiration_TimeList = []
    Respiration_DataList = []
    Respiration_YearDic = {}
    Respiration_MonthDic = {}
    Respiration_DayDic = {}
    Respiration_DataList1 = []
    Respiration_DataList2 = []
    # one month
    Respiration_DataList3 = []
    # one years
    Respiration_DataList4 = []
    # all
    Respiration_DataList5 = []
    if Respiration.entry != None:
        Respiration = fetch_all_pages(Respiration)
        #Respiration = [ob.resource for ob in Respiration.entry]
        if len(Respiration)>0:
            Respiration_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Respiration:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        Respiration_tem.append(i)
            Respiration = Respiration_tem
            for i in Respiration:
                print("Respiration Test-----------------")
                if i.effectiveDateTime != None:
                    Respiration_TimeList.append(i.effectiveDateTime.isostring)

                    Respiration_DataList.append(float(i.valueQuantity.value))

            if Respiration_TimeList != []:
                for i in range(len(Respiration_TimeList)):

                    Respiration_DataList1.append([Respiration_TimeList[i], Respiration_DataList[i]])
                    Respiration_DataList1.reverse()
                    Respiration_DataList2.append([Respiration_TimeList[i], str(Respiration_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%d")
                try:
                    Respiration_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Respiration_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Respiration_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Respiration_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Respiration_MonthTem)
                Respiration_DataList1.sort(key=lambda x: x[0])
                Respiration_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Respiration_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Respiration_DayDic:
                        Respiration_DayDic[str(date_tem.date())].append(data)
                    else:
                        Respiration_DayDic[str(date_tem.date())] = [data]
                for time, value in Respiration_DayDic.items():
                    average = sum(value) / len(value)
                    Respiration_DataList5.append([time, average])
                for t, data in Respiration_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Respiration_MonthTem:
                        Respiration_DataList3.append([t, data])
                    if date_tem > Respiration_YearTem:
                        Respiration_DataList4.append([t,data])
                print(Respiration_YearDic, Respiration_MonthDic, Respiration_DayDic)
                print(Respiration_DataList3,Respiration_DataList4,Respiration_DataList5)
            Respiration_DataList1 = json.dumps(Respiration_DataList1)
            Respiration_DataList3 = json.dumps(Respiration_DataList3)
            Respiration_DataList4 = json.dumps(Respiration_DataList4)
            Respiration_DataList5 = json.dumps(Respiration_DataList5)
    return render(request, 'Respiration_Record.html', locals())
@log_Ation('Smoking record')
def SmokingRecord(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Smoking"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Smoking = observation.Observation.where({'patient': NHINumber, 'code': '63773-6', '_sort': '-date'}).perform(smart.server)
    Smoking_TimeList = []
    Smoking_DataList = []
    Smoking_YearDic = {}
    Smoking_MonthDic = {}
    Smoking_DayDic = {}
    Smoking_DataList1 = []
    Smoking_DataList2 = []
    # one month
    Smoking_DataList3 = []
    # one years
    Smoking_DataList4 = []
    # all
    Smoking_DataList5 = []
    if Smoking.entry != None:
        Smoking = fetch_all_pages(Smoking)
        #Smoking = [ob.resource for ob in Smoking.entry]
        if len(Smoking)>0:
            Smoking_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Smoking:
                if i.performer:
                    if organization_id == i.performer[0].reference.spilt('/')[-1]:
                        Smoking_tem.append(i)
            Smoking = Smoking_tem
            for i in Smoking:
                print("Smoking Test-----------------")
                if i.effectiveDateTime != None:
                    Smoking_TimeList.append(i.effectiveDateTime.isostring)

                    Smoking_DataList.append(float(i.valueQuantity.value))

            if Smoking_TimeList != []:
                for i in range(len(Smoking_TimeList)):

                    Smoking_DataList1.append([Smoking_TimeList[i], Smoking_DataList[i]])
                    Smoking_DataList1.reverse()
                    Smoking_DataList2.append([Smoking_TimeList[i], str(Smoking_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Smoking_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Smoking_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Smoking_TimeList[0], "%Y-%m-%d")
                try:
                    Smoking_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Smoking_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Smoking_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Smoking_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Smoking_MonthTem)
                Smoking_DataList1.sort(key=lambda x: x[0])
                Smoking_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Smoking_DataList1:
                    print(t,data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Smoking_DayDic:
                        Smoking_DayDic[str(date_tem.date())].append(data)
                    else:
                        Smoking_DayDic[str(date_tem.date())] = [data]
                for time, value in Smoking_DayDic.items():
                    average = sum(value) / len(value)
                    Smoking_DataList5.append([time, average])
                for t, data in Smoking_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Smoking_MonthTem:
                        Smoking_DataList3.append([t, data])
                    if date_tem > Smoking_YearTem:
                        Smoking_DataList4.append([t,data])
                print(Smoking_YearDic, Smoking_MonthDic, Smoking_DayDic)
                print(Smoking_DataList3,Smoking_DataList4,Smoking_DataList5)
            Smoking_DataList1 = json.dumps(Smoking_DataList1)
            Smoking_DataList3 = json.dumps(Smoking_DataList3)
            Smoking_DataList4 = json.dumps(Smoking_DataList4)
            Smoking_DataList5 = json.dumps(Smoking_DataList5)
    return render(request, 'Smoking_Record.html', locals())
@log_Ation('Imaging history')
def ImagingHistory(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    request.session['RecordType'] = "Imaging"
    request.session['DataType'] = "Record"
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Imaging_List = []

    Imaging_DataList1 = []

    DiagnosticReport_List = diagnosticreport.DiagnosticReport.where(
        {'patient': NHINumber, '_sort': '-date'}).perform(smart.server)
    if DiagnosticReport_List.entry != None:
        DiagnosticReport_List = fetch_all_pages(DiagnosticReport_List)
        #DiagnosticReport_List = [c.resource for c in DiagnosticReport_List.entry]
        # MedicationRequest_List.pop(0)
        if len(DiagnosticReport_List) > 0:
            for DR in DiagnosticReport_List:
                if DR.resource_type == "DiagnosticReport":
                    if DR.category:
                        if DR.category[0].coding[0].code == "LP29684-5":
                            Imaging_List.append(DR)
            for image in Imaging_List:
                Imaging_DataList_1 = []

                Name = image.code.coding[0].display
                Time = image.effectiveDateTime.isostring
                try:
                    date_tem = datetime.datetime.strptime(Time, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    date_tem = datetime.datetime.strptime(Time, "%Y-%m-%d %H:%M:%S")
                Time = date_tem.strftime("%Y-%m-%d %H:%M:%S")
                En_id = image.encounter.reference.split("/")
                En_id = En_id[-1]
                Record_ID = image.id
                # Conclusion = image.
                Imaging_DataList_1.append(Name)
                Imaging_DataList_1.append(Time)
                Imaging_DataList_1.append(En_id)
                Imaging_DataList_1.append(Record_ID)
                Imaging_DataList1.append(Imaging_DataList_1)

    if request.method == "post":
        if 'Report' in request.POST:
            request.session['DataType'] = "Report"
            render(request, 'Imaging_History.html', locals())

    return render(request, 'Imaging_History.html', locals())
@log_Ation('Laboratory history')
def LaboratoryHistory(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    request.session['RecordType'] = "Laboratory"
    request.session['DataType'] = "Record"
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Lab_List = []

    Imaging_List = []

    Laboratory_DataList1 = []
    Value_List = []
    DiagnosticReport_List = diagnosticreport.DiagnosticReport.where(
        {'patient': NHINumber, '_include': 'DiagnosticReport:result', '_sort': '-date'}).perform(smart.server)

    if DiagnosticReport_List.entry != None:
        DiagnosticReport_List = fetch_all_pages(DiagnosticReport_List)
        #DiagnosticReport_List = [c.resource for c in DiagnosticReport_List.entry]
        # MedicationRequest_List.pop(0)
        if len(DiagnosticReport_List) > 0:
            for DR in DiagnosticReport_List:
                if DR.resource_type == "DiagnosticReport":
                    if DR.category:
                        if DR.category[0].coding[0].code == "LAB":
                            Lab_List.append(DR)
                if DR.resource_type == "Observation":
                    Value_List.append(DR)
            for lab in Lab_List:
                Lab_DataList = []
                Name = lab.code.text
                Time = lab.effectiveDateTime.isostring
                try:
                    date_tem = datetime.datetime.strptime(Time, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    date_tem = datetime.datetime.strptime(Time, "%Y-%m-%d %H:%M:%S")
                Time = date_tem.strftime("%Y-%m-%d %H:%M:%S")
                En_id = lab.encounter.reference.split("/")
                En_id = En_id[-1]
                Record_ID = lab.id
                Value_idList_1 = []
                Value_List1 = []
                for i in lab.result:
                    Ob_tem = i.reference.split("/")
                    Value_idList_1.append(Ob_tem[-1])
                for Ob in Value_List:
                    if Ob.id in Value_idList_1:
                        Value_List1.append(Ob)

                """DR_Tem_List = diagnosticreport.DiagnosticReport.where(
        {'_id': Record_ID, '_include': 'DiagnosticReport:result', '_sort': '-date'}).perform(smart.server)
                DR_Tem_List = [c.resource for c in DR_Tem_List.entry]
                for DR_Tem in DR_Tem_List:
                    if DR_Tem.resource_type == "Observation":
                        Value_List.append(DR_Tem)"""
                Critical_Sign = "-"
                for Ob in Value_List1:
                    if Ob.interpretation:
                        if Ob.interpretation[0].coding[0].code == "LL":
                            Critical_Sign = "!"
                        if Ob.interpretation[0].coding[0].code == "HH":
                            Critical_Sign = "!"
                Lab_DataList.append(Name)
                Lab_DataList.append(Time)
                Lab_DataList.append(Critical_Sign)
                Lab_DataList.append(En_id)
                Lab_DataList.append(Record_ID)
                Laboratory_DataList1.append(Lab_DataList)

    if request.method == "post":
        if 'Report' in request.POST:
            request.session['DataType'] = "Report"
            render(request, 'Imaging_History.html', locals())
    return render(request, 'Laboratory_History.html', locals())
@log_Ation('Medications history')
def MedicationsHistory(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    request.session['RecordType'] = "Medications"
    request.session['DataType'] = "Record"
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    MedicationRequestTem_List = []
    Medication_List = []
    Medications_DataList = []
    MedicationTem_List = []
    Medications_DataList1 = []
    MedicationRequest_List = medicationrequest.MedicationRequest.where(
        {'patient': NHINumber, '_include': 'MedicationRequest:medication', '_sort': '-date'}).perform(smart.server)
    if MedicationRequest_List.entry != None:
        MedicationRequest_List = fetch_all_pages(MedicationRequest_List)
        #MedicationRequest_List = [c.resource for c in MedicationRequest_List.entry]
        # MedicationRequest_List.pop(0)
        if len(MedicationRequest_List) > 0:
            for MR in MedicationRequest_List:

                if MR.resource_type == "MedicationRequest":
                    MedicationRequestTem_List.append(MR)
                if MR.resource_type == "Medication":
                    Medication_List.append(MR)
            for i in range(len(MedicationRequestTem_List)):
                if len(Medication_List) > 0:
                    MedicationTem_List.append(Medication_List[i].code.coding[0].display)
                else:
                    MedicationTem_List.append(MedicationRequestTem_List[i].medicationCodeableConcept.coding[0].display)
                if MedicationRequestTem_List[i].dosageInstruction:

                    Me = MedicationRequestTem_List[i].dosageInstruction[0]
                    if Me.doseAndRate:
                        # Dose_Str = str(Me.doseAndRate[0].doseQuantity.value) + " " + str(Me.doseAndRate[0].doseQuantity.unit)
                        if Me.doseAndRate[0].doseQuantity.value:
                            value_tem = str(Me.doseAndRate[0].doseQuantity.value)
                            if Me.doseAndRate[0].doseQuantity.unit:
                                unit_tem = str(Me.doseAndRate[0].doseQuantity.unit)
                                Dose_Str = value_tem + " " + unit_tem
                            else:
                                Dose_Str = value_tem
                    else:
                        Dose_Str = "None"
                    if Me.timing:
                        Fre_Str = str(Me.timing.repeat.frequency) + "/" + str(Me.timing.repeat.period) + \
                                  str(Me.timing.repeat.periodUnit)
                    else:
                        Fre_Str = "None"
                    if Me.route:
                        Route = Me.route.coding[0].display
                    else:
                        Route = "None"
                else:
                    Dose_Str = "None"
                    Fre_Str = "None"
                    Route = "None"
                if MedicationRequestTem_List[i].dispenseRequest:
                    try:
                        Start = datetime.datetime.strptime(
                            MedicationRequestTem_List[i].dispenseRequest.validityPeriod.start.isostring,
                            "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            Start = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.start.isostring,
                                "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            Start = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.start.isostring, "%Y-%m-%d")
                    Start = str(Start.date())
                    try:
                        End = datetime.datetime.strptime(
                            MedicationRequestTem_List[i].dispenseRequest.validityPeriod.end.isostring,
                            "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            End = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.end.isostring,
                                "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            End = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.end.isostring, "%Y-%m-%d")
                    End = str(End.date())
                else:
                    Start = "None"
                    End = "None"
                En_id = MedicationRequestTem_List[i].encounter.reference.split("/")
                En_id = En_id[-1]
                MedicationTem_List.append(Dose_Str)
                MedicationTem_List.append(Route)
                MedicationTem_List.append(Fre_Str)
                MedicationTem_List.append(Start)
                MedicationTem_List.append(En_id)
                Medications_DataList1.append(MedicationTem_List)
                MedicationTem_List = []
    return render(request, 'Medications_History.html', locals())
@log_Ation('Allergies history')
def AllergiesHistory(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    request.session['RecordType'] = "Allergies"
    request.session['DataType'] = "Record"
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Allergy_List = allergyintolerance.AllergyIntolerance.where(
        {'patient': NHINumber, '_sort': '-date'}).perform(smart.server)
    if Allergy_List.entry != None:

        Allergy_List = fetch_all_pages(Allergy_List)
        #Allergy_List = [a.resource for a in Allergy_List.entry]
        Allergies_DataList1 = []
        if len(Allergy_List) > 0:
            for allergy in Allergy_List:
                #En_id = allergy.encounter.reference.split("/")
                #En_id = En_id[-1]
                tem = []
                tem.append(allergy.code.coding[0].display)
                try:
                    date_tem = datetime.datetime.strptime(allergy.recordedDate.isostring, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(allergy.recordedDate.isostring, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(allergy.recordedDate.isostring, "%Y-%m-%d")

                tem.append(allergy.criticality)
                tem.append(str(date_tem.date()))
                Str_Tem = ""
                if allergy.reaction:
                    Reaction = allergy.reaction

                    for reaction in Reaction:
                        if reaction.manifestation:
                            for c in reaction.manifestation:
                                for d in c.coding:
                                    if Str_Tem == "":
                                        Str_Tem = d.display
                                    else:
                                        Str_Tem += ", " + d.display
                tem.append(Str_Tem)
                #tem.append(En_id)
                Allergies_DataList1.append(tem)
    return render(request, 'Allergies_History.html', locals())
@log_Ation('Diagnosis history')
def DiagnosisHistory(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    request.session['RecordType'] = "Diagnosis"
    request.session['DataType'] = "Record"
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Encounter_List = encounter.Encounter.where({'patient': NHINumber, '_revinclude': 'Condition:encounter', '_include': 'Encounter:participant',
                                                '_sort': '-date'}).perform(smart.server)

    En_All_DataList = []
    En_In_DataList = []
    En_Out_DataList = []
    En_All_List = []
    Condition_TemList = []
    Practitioner_TemList = []
    print("#############DiagnosisHistory###############")
    if Encounter_List.entry != None:
        Encounter_List = fetch_all_pages(Encounter_List)
        #Encounter_List = [e.resource for e in Encounter_List.entry]
        if len(Encounter_List) > 0:
            for i in Encounter_List:
                if i.resource_type == "Encounter":
                    En_All_List.append(i)
                if i.resource_type == "Condition":
                    Condition_TemList.append(i)
                if i.resource_type == "Practitioner":
                    Practitioner_TemList.append(i)
            for i in En_All_List:
                Diagnosis_FirstID = []
                Condition_List = []
                print(i.id)
                En_id = i.id
                if i.participant[0].individual:
                    Practitioner_id = i.participant[0].individual.reference.split("/")
                    Practitioner_id = Practitioner_id[-1]
                    for p in Practitioner_TemList:
                        if p.id == Practitioner_id:
                            Practitioner = smart.human_name(p.name[0])
                else:
                    Practitioner = "None"

                for c in Condition_TemList:
                    Encounter_Tem = c.encounter.reference.split("/")
                    Encounter_Tem = Encounter_Tem[-1]
                    if Encounter_Tem == En_id:
                        Condition_List.append(c)

                if Condition_List != None:
                    if len(Condition_List) > 0:
                        tem = []

                        T_Start = i.period.start.isostring

                        try:
                            T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%dT%H:%M:%S%z").strftime(
                                "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d %H:%M:%S").strftime(
                                    "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d").strftime("%Y-%m-%d")

                        diseases = []
                        d1 = ""
                        for disease in Condition_List[-1].code.coding:
                            if d1 == "":
                                d1 += disease.display
                            else:
                                d1 += "; " + disease.display
                        Condition_List.pop(-1)
                        for c in Condition_List:
                            for disease in c.code.coding:
                                diseases.append(disease.display)
                        tem.append(d1)
                        tem.append(diseases)
                        tem.append(T_Start)
                        tem.append(Practitioner)
                        tem.append(En_id)
                        En_All_DataList.append(tem)
                    else:
                        tem = []

                        T_Start = i.period.start.isostring

                        try:
                            T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%dT%H:%M:%S%z").strftime(
                                "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d %H:%M:%S").strftime(
                                    "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d").strftime("%Y-%m-%d")

                        diseases = []
                        d1 = "None"

                        tem.append(d1)
                        tem.append(diseases)
                        tem.append(T_Start)
                        tem.append(Practitioner)
                        tem.append(En_id)
                        En_All_DataList.append(tem)
    return render(request, 'Diagnosis_History.html', locals())
@log_Ation('Encounter history')
def Visit(request, En_id):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    RecordType = request.session['RecordType']
    DataType = request.session['DataType']
    NHINumber = request.session['NHINumber']
    request.session['Encounter'] = En_id
    smart = client.FHIRClient(settings=settings)
    Legend_Data = ["Temperature", "Pulse", "Respiration", "Systolic Blood Pressure", "Diastolic Blood Pressure"]
    Encounter_Tem = encounter.Encounter.read(En_id, smart.server)
        ##encounter.Encounter.where({'patient': NHINumber, '_sort': '-date'}).perform(smart.server)
    En_All_DataList = []
    if Encounter_Tem:

        if Encounter_Tem.serviceProvider:
            Organization_ID = Encounter_Tem.serviceProvider.reference.split("/")
            Organization_ID = Organization_ID[-1]
            Organization_List = organization.Organization.where({'_id': Organization_ID}).perform(smart.server)
            Organization_BelongTo_ID = None
            if Organization_List.entry != None:
                Organization_List = fetch_all_pages(Organization_List)
                #Organization_List = [c.resource for c in Organization_List.entry]

                if len(Organization_List) > 0:
                    Organization_Tem = Organization_List[0]
                    if Organization_Tem.partOf:
                        Organization_BelongTo_ID = Organization_Tem.partOf.reference.split("/")
                        Organization_BelongTo_ID = Organization_BelongTo_ID[-1]

                    if Organization_Tem:
                        Organization_Tem = Organization_Tem.name
            else:
                Organization_Tem = "None"



            if Organization_BelongTo_ID:
                Organization_List = organization.Organization.where({'_id': Organization_BelongTo_ID}).perform(
                    smart.server)
                if Organization_List.entry != None:
                    Organization_List = fetch_all_pages(Organization_List)
                    #Organization_List = [c.resource for c in Organization_List.entry]
                    if len(Organization_List) > 0:
                        Organization_BelongTo_Tem = Organization_List[0]
                        if Organization_BelongTo_Tem:
                            Organization_BelongTo_Tem = Organization_BelongTo_Tem.name
                else:
                    Organization_BelongTo_Tem = "None"
            else:
                Organization_BelongTo_Tem = "None"
        else:
            Organization_Tem = "None"
            Organization_BelongTo_Tem = "None"
        print(Organization_BelongTo_Tem)
        Condition_List = condition.Condition.where({'encounter': Encounter_Tem.id}).perform(smart.server)
        if Condition_List.entry != None:
            Condition_List = fetch_all_pages(Condition_List)
            #Condition_List = [c.resource for c in Condition_List.entry]
            if len(Condition_List) > 0:
                for c in Condition_List:

                    tem_str = ""
                    for disease in c.code.coding:
                        if tem_str == "":
                            tem_str += disease.display
                        else:
                            tem_str += "; " + disease.display

                T_Start = Encounter_Tem.period.start.isostring
                try:
                    T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%dT%H:%M:%S%z").strftime(
                        "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d %H:%M:%S").strftime(
                            "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        T_Start = datetime.datetime.strptime(T_Start, "%Y-%m-%d").strftime("%Y-%m-%d")
                T_End = Encounter_Tem.period.end.isostring
                try:
                    T_End = datetime.datetime.strptime(T_End, "%Y-%m-%dT%H:%M:%S%z").strftime(
                        "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        T_End = datetime.datetime.strptime(T_End, "%Y-%m-%d %H:%M:%S").strftime(
                            "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        T_End = datetime.datetime.strptime(T_End, "%Y-%m-%d").strftime("%Y-%m-%d")
                if Encounter_Tem.class_fhir.code == "AMB":
                    tem = [T_Start, T_End]
                    if Organization_BelongTo_Tem:
                        tem.append(Organization_BelongTo_Tem)
                    else:
                        tem.append("None")
                    if Organization_Tem:
                        tem.append(Organization_Tem)
                    else:
                        tem.append("None")
                    reason_Str = ""
                    if Encounter_Tem.reasonCode:
                        for reason in Encounter_Tem.reasonCode:
                            if reason_Str == "":
                                reason_Str = reason.text
                            else:
                                reason_Str += reason.text
                    else:
                        reason_Str = "None"
                    tem.append(reason_Str)
                    tem.append(tem_str)
                if Encounter_Tem.class_fhir.code == "IMP" or Encounter_Tem.class_fhir.code == "ACUTE" or Encounter_Tem.class_fhir.code == "NONAC":
                    tem = [T_Start, T_End]
                    if Organization_BelongTo_Tem:
                        tem.append(Organization_BelongTo_Tem)
                    else:
                        tem.append("None")
                    if Organization_Tem:
                        tem.append(Organization_Tem)
                    else:
                        tem.append("None")
                    reason_Str = ""
                    for reason in Encounter_Tem.reasonCode:
                        if reason_Str == "":
                            reason_Str = reason.text
                        else:
                            reason_Str += reason.text
                    tem.append(reason_Str)
                    tem.append(tem_str)


                En_All_DataList.append(tem)
    # ###############################Vital Signs
    HeartRate = []
    Temperature = []
    BloodPressure = []
    Respiration = []

    Sign_Tem = []
    FileCode = "1"
    VitalSigns_DataList1 = []
    VitalSign_List = encounter.Encounter.where(
        {'_id': En_id, '_revinclude': 'Observation:encounter', '_sort': '-date'}).perform(smart.server)
    if VitalSign_List.entry != None:
        VitalSign_List = fetch_all_pages(VitalSign_List)
        #VitalSign_List = [c.resource for c in VitalSign_List.entry]
        VitalSign_List.pop(0)

        if len(VitalSign_List) > 0:
            for VitalSign in VitalSign_List:
                for c in VitalSign.code.coding:
                    #Heart Rate
                    if c.code == '8867-4':
                        HeartRate.append(VitalSign)
                    #Temperature
                    if c.code == '8310-5':
                        Temperature.append(VitalSign)
                    #Blood Pressure
                    if c.code == '85354-9':
                        BloodPressure.append(VitalSign)
                    #Respiration
                    if c.code == '9279-1':
                        Respiration.append(VitalSign)
    else:
        VitalSign_List = None

    HeartRate_TimeList = []
    HeartRate_DataList = []
    HeartRate_YearDic = {}
    HeartRate_MonthDic = {}
    HeartRate_DayDic = {}
    HeartRate_DataList1 = []
    HeartRate_DataList2 = []
    # one month
    HeartRate_DataList3 = []
    # one years
    HeartRate_DataList4 = []
    # all
    HeartRate_DataList5 = []

    if len(HeartRate) > 0:

        for i in HeartRate:
            print("HeartRate Test-----------------")
            if i.effectiveDateTime != None:
                HeartRate_TimeList.append(i.effectiveDateTime.isostring)

                HeartRate_DataList.append(float(i.valueQuantity.value))

        if HeartRate_TimeList != []:
            for i in range(len(HeartRate_TimeList)):
                HeartRate_DataList1.append([HeartRate_TimeList[i], HeartRate_DataList[i]])
                HeartRate_DataList1.reverse()
                HeartRate_DataList2.append([HeartRate_TimeList[i], str(HeartRate_DataList[i])])
            try:
                date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                try:
                    date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%d")
            try:
                HeartRate_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                "%Y-%m-%d %H:%M:%S")
            except ValueError:
                HeartRate_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                "%Y-%m-%d")
            try:
                HeartRate_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                               "%Y-%m-%d %H:%M:%S")
            except ValueError:
                HeartRate_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                               "%Y-%m-%d")
            print(HeartRate_MonthTem)
            HeartRate_DataList1.sort(key=lambda x: x[0])
            HeartRate_DataList2.sort(key=lambda x: x[0], reverse=True)
            for t, data in HeartRate_DataList1:
                print(t, data)
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                if str(date_tem.date()) in HeartRate_DayDic:
                    HeartRate_DayDic[str(date_tem.date())].append(data)
                else:
                    HeartRate_DayDic[str(date_tem.date())] = [data]
            for time, value in HeartRate_DayDic.items():
                average = sum(value) / len(value)
                HeartRate_DataList5.append([time, average])
            for t, data in HeartRate_DataList5:
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                if date_tem > HeartRate_MonthTem:
                    HeartRate_DataList3.append([t, data])
                if date_tem > HeartRate_YearTem:
                    HeartRate_DataList4.append([t, data])
            print(HeartRate_YearDic, HeartRate_MonthDic, HeartRate_DayDic)
            print(HeartRate_DataList3, HeartRate_DataList4, HeartRate_DataList5)
        HeartRate_DataList1 = json.dumps(HeartRate_DataList1)
        HeartRate_DataList3 = json.dumps(HeartRate_DataList3)
        HeartRate_DataList4 = json.dumps(HeartRate_DataList4)
        #HeartRate_DataList5 = json.dumps(HeartRate_DataList5)

    Temperature_TimeList = []
    Temperature_DataList = []
    Temperature_YearDic = {}
    Temperature_MonthDic = {}
    Temperature_DayDic = {}
    Temperature_DataList1 = []
    Temperature_DataList2 = []
    # one month
    Temperature_DataList3 = []
    # one years
    Temperature_DataList4 = []
    # all
    Temperature_DataList5 = []

    if len(Temperature) > 0:

        for i in Temperature:
            print("Temperature Test-----------------")
            if i.effectiveDateTime != None:
                Temperature_TimeList.append(i.effectiveDateTime.isostring)

                Temperature_DataList.append(float(i.valueQuantity.value))

        if Temperature_TimeList != []:
            for i in range(len(Temperature_TimeList)):
                Temperature_DataList1.append([Temperature_TimeList[i], Temperature_DataList[i]])
                Temperature_DataList1.reverse()
                Temperature_DataList2.append([Temperature_TimeList[i], str(Temperature_DataList[i])])
            try:
                date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                try:
                    date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%d")
            try:
                Temperature_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                  "%Y-%m-%d %H:%M:%S")
            except ValueError:
                Temperature_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                  "%Y-%m-%d")
            try:
                Temperature_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                 "%Y-%m-%d %H:%M:%S")
            except ValueError:
                Temperature_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                 "%Y-%m-%d")
            print(Temperature_MonthTem)
            Temperature_DataList1.sort(key=lambda x: x[0])
            Temperature_DataList2.sort(key=lambda x: x[0], reverse=True)
            for t, data in Temperature_DataList1:
                print(t, data)
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                if str(date_tem.date()) in Temperature_DayDic:
                    Temperature_DayDic[str(date_tem.date())].append(data)
                else:
                    Temperature_DayDic[str(date_tem.date())] = [data]
            for time, value in Temperature_DayDic.items():
                average = sum(value) / len(value)
                Temperature_DataList5.append([time, average])
            for t, data in Temperature_DataList5:
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                if date_tem > Temperature_MonthTem:
                    Temperature_DataList3.append([t, data])
                if date_tem > Temperature_YearTem:
                    Temperature_DataList4.append([t, data])
            print(Temperature_YearDic, Temperature_MonthDic, Temperature_DayDic)
            print(Temperature_DataList3, Temperature_DataList4, Temperature_DataList5)
        Temperature_DataList1 = json.dumps(Temperature_DataList1)
        Temperature_DataList3 = json.dumps(Temperature_DataList3)
        Temperature_DataList4 = json.dumps(Temperature_DataList4)
        #Temperature_DataList5 = json.dumps(Temperature_DataList5)
    BloodPressure_TimeList = []
    # lower
    DiastolicBloodPressure_DataList = []
    DiastolicBloodPressure_YearDic = {}
    DiastolicBloodPressure_MonthDic = {}
    DiastolicBloodPressure_DayDic = {}
    # higher
    SystolicBloodPressure_DataList = []
    SystolicBloodPressure_YearDic = {}
    SystolicBloodPressure_MonthDic = {}
    SystolicBloodPressure_DayDic = {}
    SystolicBloodPressure_DataList1 = []
    # SystolicBloodPressure_DataList2 = []
    DiastolicBloodPressure_DataList1 = []
    # DiastolicBloodPressure_DataList2 = []
    BloodPressure_DataList2 = []
    BloodPressure_DataList3 = []


    # one month
    SystolicBloodPressure_DataList3 = []
    # one years
    SystolicBloodPressure_DataList4 = []
    # all
    SystolicBloodPressure_DataList5 = []
    # one month
    DiastolicBloodPressure_DataList3 = []
    # one years
    DiastolicBloodPressure_DataList4 = []
    # all
    DiastolicBloodPressure_DataList5 = []

    if len(BloodPressure) > 0:

        for i in BloodPressure:
            print("BloodPressure Test-----------------")
            if i.effectiveDateTime != None:
                BloodPressure_TimeList.append(i.effectiveDateTime.isostring)
                for o in i.component:
                    code_List = o.code.coding
                    for code in code_List:
                        if code.code == "8480-6" or code.code == "271649006" or code.code == "bp-s":
                            SystolicBloodPressure_DataList.append(float(o.valueQuantity.value))
                            print("8480-6")
                        if code.code == "8462-4":
                            DiastolicBloodPressure_DataList.append(float(o.valueQuantity.value))
                            print("8462-4")
                    print(o.valueQuantity.value)

        if BloodPressure_TimeList != []:
            for i in range(len(BloodPressure_TimeList)):
                print(BloodPressure_TimeList)
                print(SystolicBloodPressure_DataList)
                SystolicBloodPressure_DataList1.append(
                    [BloodPressure_TimeList[i], SystolicBloodPressure_DataList[i]])
                SystolicBloodPressure_DataList1.reverse()

                DiastolicBloodPressure_DataList1.append(
                    [BloodPressure_TimeList[i], DiastolicBloodPressure_DataList[i]])
                DiastolicBloodPressure_DataList1.reverse()

                BloodPressure_DataList2.append([BloodPressure_TimeList[i], str(SystolicBloodPressure_DataList[i]),
                                                str(DiastolicBloodPressure_DataList[i])])

            try:
                date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                try:
                    date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%d")
            try:
                BloodPressure_MonthTem = datetime.datetime.strptime(
                    str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                BloodPressure_MonthTem = datetime.datetime.strptime(
                    str((date_tem.date() - relativedelta(months=1))),
                    "%Y-%m-%d")
            try:
                BloodPressure_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                   "%Y-%m-%d %H:%M:%S")
            except ValueError:
                BloodPressure_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                   "%Y-%m-%d")
            print(BloodPressure_MonthTem)
            SystolicBloodPressure_DataList1.sort(key=lambda x: x[0])
            BloodPressure_DataList2.sort(key=lambda x: x[0], reverse=True)
            for t, data in SystolicBloodPressure_DataList1:
                print(t, data)
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                if str(date_tem.date()) in SystolicBloodPressure_DayDic:
                    SystolicBloodPressure_DayDic[str(date_tem.date())].append(data)
                else:
                    SystolicBloodPressure_DayDic[str(date_tem.date())] = [data]
            for time, value in SystolicBloodPressure_DayDic.items():
                average = sum(value) / len(value)
                SystolicBloodPressure_DataList5.append([time, average])
            for t, data in SystolicBloodPressure_DataList5:
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                if date_tem > BloodPressure_MonthTem:
                    SystolicBloodPressure_DataList3.append([t, data])
                if date_tem > BloodPressure_YearTem:
                    SystolicBloodPressure_DataList4.append([t, data])
            DiastolicBloodPressure_DataList1.sort(key=lambda x: x[0])
            BloodPressure_DataList2.sort(key=lambda x: x[0], reverse=True)
            for t, data in DiastolicBloodPressure_DataList1:
                print(t, data)
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                if str(date_tem.date()) in DiastolicBloodPressure_DayDic:
                    DiastolicBloodPressure_DayDic[str(date_tem.date())].append(data)
                else:
                    DiastolicBloodPressure_DayDic[str(date_tem.date())] = [data]
            for time, value in DiastolicBloodPressure_DayDic.items():
                average = sum(value) / len(value)
                DiastolicBloodPressure_DataList5.append([time, average])
            for t, data in DiastolicBloodPressure_DataList5:
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                if date_tem > BloodPressure_MonthTem:
                    DiastolicBloodPressure_DataList3.append([t, data])
                if date_tem > BloodPressure_YearTem:
                    DiastolicBloodPressure_DataList4.append([t, data])
            # print(BloodPressure_YearDic, BloodPressure_MonthDic, BloodPressure_DayDic)
            # print(BloodPressure_DataList3,BloodPressure_DataList4,BloodPressure_DataList5)

            # BloodPressure_DataList1 = json.dumps(BloodPressure_DataList1)

        for i in range(len(SystolicBloodPressure_DataList5)):

            tem = []
            tem.append(SystolicBloodPressure_DataList5[i][0])
            tem.append(SystolicBloodPressure_DataList5[i][1])
            tem.append(DiastolicBloodPressure_DataList5[i][1])
            BloodPressure_DataList3.append(tem)
        SystolicBloodPressure_DataList3 = json.dumps(SystolicBloodPressure_DataList3)
        SystolicBloodPressure_DataList4 = json.dumps(SystolicBloodPressure_DataList4)
        SystolicBloodPressure_DataList5 = json.dumps(SystolicBloodPressure_DataList5)

        DiastolicBloodPressure_DataList3 = json.dumps(DiastolicBloodPressure_DataList3)
        DiastolicBloodPressure_DataList4 = json.dumps(DiastolicBloodPressure_DataList4)
        DiastolicBloodPressure_DataList5 = json.dumps(DiastolicBloodPressure_DataList5)
    Respiration_TimeList = []
    Respiration_DataList = []
    Respiration_YearDic = {}
    Respiration_MonthDic = {}
    Respiration_DayDic = {}
    Respiration_DataList1 = []
    Respiration_DataList2 = []
    # one month
    Respiration_DataList3 = []
    # one years
    Respiration_DataList4 = []
    # all
    Respiration_DataList5 = []

    if len(Respiration) > 0:

        for i in Respiration:
            print("Respiration Test-----------------")
            if i.effectiveDateTime != None:
                Respiration_TimeList.append(i.effectiveDateTime.isostring)

                Respiration_DataList.append(float(i.valueQuantity.value))

        if Respiration_TimeList != []:
            for i in range(len(Respiration_TimeList)):
                Respiration_DataList1.append([Respiration_TimeList[i], Respiration_DataList[i]])
                Respiration_DataList1.reverse()
                Respiration_DataList2.append([Respiration_TimeList[i], str(Respiration_DataList[i])])
            try:
                date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                try:
                    date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%d")
            try:
                Respiration_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                  "%Y-%m-%d %H:%M:%S")
            except ValueError:
                Respiration_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                  "%Y-%m-%d")
            try:
                Respiration_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                 "%Y-%m-%d %H:%M:%S")
            except ValueError:
                Respiration_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                 "%Y-%m-%d")
            print(Respiration_MonthTem)
            Respiration_DataList1.sort(key=lambda x: x[0])
            Respiration_DataList2.sort(key=lambda x: x[0], reverse=True)
            for t, data in Respiration_DataList1:
                print(t, data)
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                if str(date_tem.date()) in Respiration_DayDic:
                    Respiration_DayDic[str(date_tem.date())].append(data)
                else:
                    Respiration_DayDic[str(date_tem.date())] = [data]
            for time, value in Respiration_DayDic.items():
                average = sum(value) / len(value)
                Respiration_DataList5.append([time, average])
            for t, data in Respiration_DataList5:
                try:
                    date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                if date_tem > Respiration_MonthTem:
                    Respiration_DataList3.append([t, data])
                if date_tem > Respiration_YearTem:
                    Respiration_DataList4.append([t, data])
            print(Respiration_YearDic, Respiration_MonthDic, Respiration_DayDic)
            print(Respiration_DataList3, Respiration_DataList4, Respiration_DataList5)
        Respiration_DataList1 = json.dumps(Respiration_DataList1)
        Respiration_DataList3 = json.dumps(Respiration_DataList3)
        Respiration_DataList4 = json.dumps(Respiration_DataList4)
        #Respiration_DataList5 = json.dumps(Respiration_DataList5)

    print(Temperature_DataList5)
    print(HeartRate_DataList5)
    print(Respiration_DataList5)
    print(BloodPressure_DataList3)
    t_Tem = []
    t_TemperatureTem = []
    t_HeartRateTem = []
    t_RespirationTem = []
    t_BloodPressureTem = []
    if len(Temperature_DataList5) > 0:
        for t, data in Temperature_DataList5:
            t_Tem.append(t)
            t_TemperatureTem.append(t)
        for t, data in HeartRate_DataList5:
            if t not in t_Tem:
                t_Tem.append(t)
            t_HeartRateTem.append(t)
        for t, data in Respiration_DataList5:
            if t not in t_Tem:
                t_Tem.append(t)
            t_RespirationTem.append(t)
        for t, data1, data2 in BloodPressure_DataList3:
            if t not in t_Tem:
                t_Tem.append(t)
            t_BloodPressureTem.append(t)


    t_Tem = sorted(t_Tem, key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"), reverse=True)
    for t in t_Tem:
        for t_1, data_1 in Temperature_DataList5:
            if t in t_TemperatureTem:
                if t_1 == t:
                    Sign_Tem.append(t)
                    Sign_Tem.append(data_1)
            else:
                break
        for t_2, data_2 in HeartRate_DataList5:
            if t in t_HeartRateTem:
                if t_2 == t:
                    Sign_Tem.append(data_2)
            else:
                break
        for t_3, data_3 in Respiration_DataList5:
            if t in t_RespirationTem:
                if t_3 == t:
                    Sign_Tem.append(data_3)
            else:
                break
        for t_4, data_4, data_5 in BloodPressure_DataList3:
            if t in t_BloodPressureTem:
                if t_4 == t:
                    tem = str(data_4) + "/" + str(data_5)
                    Sign_Tem.append(tem)
            else:
                break

        print(Sign_Tem)
        VitalSigns_DataList1.append(Sign_Tem)
        Sign_Tem = []
    Temperature_DataList5 = json.dumps(Temperature_DataList5)
    HeartRate_DataList5 = json.dumps(HeartRate_DataList5)
    Respiration_DataList5 = json.dumps(Respiration_DataList5)
    print("###############vital signs##############")
    print(VitalSigns_DataList1)
    PulseRate_Data1 = HeartRate_DataList3
    PulseRate_Data2 = HeartRate_DataList4
    PulseRate_Data3 = HeartRate_DataList5
    BloodPressureUp_Data1 = SystolicBloodPressure_DataList3
    BloodPressureUp_Data2 = SystolicBloodPressure_DataList4
    BloodPressureUp_Data3 = SystolicBloodPressure_DataList5
    BloodPressureDown_Data1 = DiastolicBloodPressure_DataList3
    BloodPressureDown_Data2 = DiastolicBloodPressure_DataList4
    BloodPressureDown_Data3 = DiastolicBloodPressure_DataList5
    Respiration_Data1 = Respiration_DataList3
    Respiration_Data2 = Respiration_DataList4
    Respiration_Data3 = Respiration_DataList5
    Temperature_Data1 = Temperature_DataList3
    Temperature_Data2 = Temperature_DataList4
    Temperature_Data3 = Temperature_DataList5
    #################################Allergy######################################
    #不能使用encounter的id进行搜索allergyintorlerance资源
    Allergy_List = allergyintolerance.AllergyIntolerance.where(
        {'patient': NHINumber, '_sort': '-date'}).perform(smart.server)
    if Allergy_List.entry != None:
        Allergy_List = fetch_all_pages(Allergy_List)
        #Allergy_List = [a.resource for a in Allergy_List.entry]
        Allergy_List_1 = []
        Allergies_DataList1 = []
        print("#####################Allergy##################")
        if len(Allergy_List) > 0:
            Allergy_List_1 = Allergy_List

            for allergy in Allergy_List_1:
                tem = []

                print(allergy.id)
                print(allergy.code.coding)
                tem.append(allergy.code.coding[0].display)
                try:
                    date_tem = datetime.datetime.strptime(allergy.recordedDate.isostring, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(allergy.recordedDate.isostring, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(allergy.recordedDate.isostring, "%Y-%m-%d")
                tem.append(str(date_tem.date()))
                tem.append(allergy.criticality)
                Str_Tem = ""
                if allergy.reaction:
                    Reaction = allergy.reaction

                    for reaction in Reaction:
                        if reaction.manifestation:
                            for c in reaction.manifestation:
                                for d in c.coding:
                                    if Str_Tem == "":
                                        Str_Tem = d.display
                                    else:
                                        Str_Tem += ", " + d.display
                print("REACTION####################")
                print(Str_Tem)
                tem.append(Str_Tem)
                Str_Tem = ""
                if allergy.note:
                    for n in allergy.note:
                        if Str_Tem == "":
                            Str_Tem = n.text
                        else:
                            Str_Tem += " " + n.text
                    tem.append(Str_Tem)
                else:
                    tem.append("None")
                Allergies_DataList1.append(tem)
    #################################Medication###################################
    MedicationRequestTem_List = []
    Medication_List = []
    Medications_DataList = []
    MedicationTem_List = []
    Medications_DataList1 = []
    MedicationRequest_List = medicationrequest.MedicationRequest.where(
        {'encounter': En_id, '_include': 'MedicationRequest:medication', '_sort': '-date'}).perform(smart.server)
    if MedicationRequest_List.entry != None:
        MedicationRequest_List = fetch_all_pages(MedicationRequest_List)
        #MedicationRequest_List = [c.resource for c in MedicationRequest_List.entry]
        #MedicationRequest_List.pop(0)
        if len(MedicationRequest_List) > 0:
            for MR in MedicationRequest_List:
                if MR.resource_type == "MedicationRequest":
                    MedicationRequestTem_List.append(MR)
                if MR.resource_type == "Medication":
                    Medication_List.append(MR)
            for i in range(len(MedicationRequestTem_List)):
                if len(Medication_List)>0:
                    MedicationTem_List.append(Medication_List[i].code.coding[0].display)
                else:
                    MedicationTem_List.append(MedicationRequestTem_List[i].medicationCodeableConcept.coding[0].display)
                if MedicationRequestTem_List[i].dosageInstruction[0]:

                    Me = MedicationRequestTem_List[i].dosageInstruction[0]
                    if Me.doseAndRate:
                        #Dose_Str = str(Me.doseAndRate[0].doseQuantity.value) + " " + str(Me.doseAndRate[0].doseQuantity.unit)
                        if Me.doseAndRate[0].doseQuantity.value:
                            value_tem = str(Me.doseAndRate[0].doseQuantity.value)
                            if Me.doseAndRate[0].doseQuantity.unit:
                                unit_tem = str(Me.doseAndRate[0].doseQuantity.unit)
                                Dose_Str = value_tem + " " + unit_tem
                            else:
                                Dose_Str = value_tem
                    else:
                        Dose_Str = "None"
                    if Me.timing:
                        Fre_Str = str(Me.timing.repeat.frequency) + "/" + str(Me.timing.repeat.period)  + \
                              str(Me.timing.repeat.periodUnit)
                    else:
                        Fre_Str = "None"
                    if Me.route:
                        Route = Me.route.coding[0].display
                    else:
                        Route = "None"
                else:
                    Dose_Str = "None"
                    Fre_Str = "None"
                    Route = "None"
                if MedicationRequestTem_List[i].dispenseRequest:
                    try:
                        Start = datetime.datetime.strptime(
                            MedicationRequestTem_List[i].dispenseRequest.validityPeriod.start.isostring,
                            "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            Start = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.start.isostring,
                                "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            Start = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.start.isostring, "%Y-%m-%d")
                    Start = str(Start.date())
                    try:
                        End = datetime.datetime.strptime(
                            MedicationRequestTem_List[i].dispenseRequest.validityPeriod.end.isostring,
                            "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            End = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.end.isostring,
                                "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            End = datetime.datetime.strptime(
                                MedicationRequestTem_List[i].dispenseRequest.validityPeriod.end.isostring, "%Y-%m-%d")
                    End = str(End.date())
                else:
                    Start = "None"
                    End = "None"
                MedicationTem_List.append(Dose_Str)
                MedicationTem_List.append(Route)
                MedicationTem_List.append(Fre_Str)
                MedicationTem_List.append(Start)
                MedicationTem_List.append(End)
                Medications_DataList1.append(MedicationTem_List)
                MedicationTem_List = []
    #################################Lab###################################
    Lab_List = []
    Value_List = []
    Imaging_List = []
    Critical_List = []
    Laboratory_DataList2 = []
    Imaging_DataList1 = []
    Imaging_DataList2 = []
    DiagnosticReport_List = diagnosticreport.DiagnosticReport.where(
        {'encounter:Encounter': En_id, '_include': 'DiagnosticReport:result', '_sort': '-date'}).perform(smart.server)
    if DiagnosticReport_List.entry != None:
        DiagnosticReport_List = fetch_all_pages(DiagnosticReport_List)
        #DiagnosticReport_List = [c.resource for c in DiagnosticReport_List.entry]
        #MedicationRequest_List.pop(0)
        if len(DiagnosticReport_List) > 0:
            for DR in DiagnosticReport_List:
                if DR.resource_type == "DiagnosticReport":
                    if DR.category:

                        if DR.category[0].coding[0].code == "LP29684-5":
                            Imaging_List.append(DR)
                        elif DR.category[0].coding[0].code == "LAB":
                            Lab_List.append(DR)
                if DR.resource_type == "Observation":
                    Value_List.append(DR)
            print("######################CriticalValue################")
            print(len(Value_List))
            for Ob in Value_List:
                if Ob.interpretation:
                    tem = []
                    Critical_ID = ""
                    print(Ob.id)
                    if Ob.interpretation[0].coding[0].code == "LL":
                        print("LL")
                        #可能需要修改
                        Item = Ob.code.text
                        Result = str(Ob.valueQuantity.value) + " " + Ob.valueQuantity.unit
                        Abnormal = "↓"
                        Range = str(Ob.referenceRange[0].low.value) + "-" + str(Ob.referenceRange[0].high.value) + \
                                " " + str(Ob.referenceRange[0].high.unit)
                        Critical_ID = Ob.id
                        tem.append(Item)
                        tem.append(Result)
                        tem.append(Abnormal)
                        tem.append(Range)
                    if Ob.interpretation[0].coding[0].code == "HH":
                        print("HH")
                        Item = Ob.code.text
                        Result = str(Ob.valueQuantity.value) + " " + Ob.valueQuantity.unit
                        Abnormal = "↑"
                        Range = str(Ob.referenceRange[0].low.value) + "-" + str(Ob.referenceRange[0].high.value) + \
                                " " + str(Ob.referenceRange[0].high.unit)
                        Critical_ID = Ob.id
                        tem.append(Item)
                        tem.append(Result)
                        tem.append(Abnormal)
                        tem.append(Range)
                    for lab in Lab_List:
                        Report_List = [r.reference.split('/')[-1] for r in lab.result]
                        print(Report_List)
                        if Critical_ID in Report_List:
                            Link = lab.id
                            tem.append(Link)
                            Critical_List.append(tem)
            Laboratory_DataList1 = Critical_List
            print(Lab_List)
            print("###################")
            for lab in Lab_List:

                Lab_DataList = []
                Name = lab.code.text
                Lab_DataList.append(Name)
                Lab_DataList.append(lab.id)
                Laboratory_DataList2.append(Lab_DataList)
            for image in Imaging_List:
                Imaging_DataList_1 = []
                Imaging_DataList_2 = []
                Conclusion = "None"
                Name = image.code.coding[0].display
                #Conclusion = image.
                Imaging_DataList_1.append(Conclusion)
                Imaging_DataList_1.append(Name)
                Imaging_DataList_1.append(image.id)
                Imaging_DataList1.append(Imaging_DataList_1)
                Imaging_DataList_2.append(Name)
                Imaging_DataList_2.append(image.id)
                Imaging_DataList2.append(Imaging_DataList_2)


    return render(request, 'Visit.html', locals())
@log_Ation('Imaging file')
def ImagingFile(request, FileCode):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    RecordType = "Imaging"
    DataType = request.session['DataType']
    NHINumber = request.session['NHINumber']
    Encounter = request.session['Encounter']
    smart = client.FHIRClient(settings=settings)
    Lab = diagnosticreport.DiagnosticReport.where({'_id': FileCode, '_include': 'DiagnosticReport:media',
                                                   '_sort': '-date'}).perform(smart.server)
    request.session['RecordType'] = "Imaging"

    PDF_List = []
    Imaging_List = []
    PDF_DataList = ""
    Imaging_DataList = []
    Lab = fetch_all_pages(Lab)
    #Lab = [lab.resource for lab in Lab.entry]
    for i in Lab:
        if i.resource_type == "DiagnosticReport":
            PDF_List.append(i)
        elif i.resource_type == "Media":
            Imaging_List.append(i)
    if Lab[0].presentedForm is not None:
        PDF_DataList = Lab[0].presentedForm[0].data

    for i in Imaging_List:
        Imaging_DataList.append(i.content.data)
    return render(request, 'ImagingFile.html', locals())
@log_Ation('Laboratory file')
def LaboratoryFile(request, FileCode):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    RecordType = "Laboratory"
    DataType = request.session['DataType']
    NHINumber = request.session['NHINumber']
    Encounter = request.session['Encounter']
    smart = client.FHIRClient(settings=settings)
    Lab = diagnosticreport.DiagnosticReport.where({'_id': FileCode,
                                                   '_sort': '-date'}).perform(smart.server)
    request.session['RecordType'] = "Laboratory"

    PDF_DataList = ""
    Lab = [lab.resource for lab in Lab.entry]
    Code = Lab[0].code.coding[0].code
    if Lab[0].presentedForm is not None:
        PDF_DataList = Lab[0].presentedForm[0].data
    Lab = diagnosticreport.DiagnosticReport.where({'_id': FileCode, '_include': 'DiagnosticReport:result',
                                                   '_sort': '-date'}).perform(smart.server)
    Lab = [lab.resource for lab in Lab.entry]
    Laboratory_List = []
    for i in Lab:
        if i.resource_type == "Observation":
            Laboratory_List.append(i)
    Observation_Data = defaultdict(list)
    for i in Laboratory_List:
        Item_Name = i.code.text
        Time = i.effectiveDateTime.isostring
        try:
            date_tem = datetime.datetime.strptime(Time, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            date_tem = datetime.datetime.strptime(Time, "%Y-%m-%d %H:%M:%S")
        Time = date_tem.strftime("%Y-%m-%d %H:%M:%S")
        #Time = datetime.datetime.strptime(Time, "%Y-%m-%d %H:%M:%S")
        Value = i.valueQuantity.value
        Unit = i.valueQuantity.unit
        Keys = Item_Name + "(" + Unit + ")"
        Observation_Data[Keys].append([Time, Value])
    Legend_Data = list(Observation_Data.keys())
    Observation_Data = json.dumps(Observation_Data)
    #检查报告数据集
    ReportDatas=[]
    for item in Laboratory_List:
        ReferenceRange=''
        AbnormalFlag=''
        if item.referenceRange is not None:
            try:
                ReferenceRange=str(item.referenceRange[0].low.value)+" - "+str(item.referenceRange[0].high.value)+"  "+item.valueQuantity.unit
                if item.valueQuantity.value<item.referenceRange[0].low.value:
                    AbnormalFlag='↓'
                elif item.valueQuantity.value>item.referenceRange[0].high.value:
                    AbnormalFlag='↑'
                else:
                    AbnormalFlag="normal"
            except:
                print()
        data={
            'ItemName':item.code.text,
            'LabResult':str(item.valueQuantity.value) +" "+ item.valueQuantity.unit,
            'ReferenceRange': ReferenceRange,
            'AbnormalFlag':AbnormalFlag
        }
        ReportDatas.append(data)
    """Lab = diagnosticreport.DiagnosticReport.where({'patient': '12892'}).perform(smart.server)
    Imaging_DataList1 = []
    Imaging_DataList2 = []
    Lab_TimeList = []
    Binary_List1 = []
    Lab_Item = []
    Lab = [lab.resource for lab in Lab.entry]
    for i in Lab:
        if i.presentedForm and i.issued:
            Lab_TimeList.append(i.issued)
            Lab_Item.append(i.code.text)
            for o in i.presentedForm:
                Binary_List1.append(o.url)
    Binary_List = []
    for i in range(len(Binary_List1)):
        Binary_ID = Binary_List1[i].split('/')[-1]
        Binary = binary.Binary.read(Binary_ID, smart.server)
        data = Binary.data
        Binary_List.append(data)
    Lab_DataList = []
    for i in range(len(Lab_TimeList)):
        Lab_DataList.append([Lab_Item[i], Lab_TimeList[i], Binary_List[i]])"""

    return render(request, 'LaboratoryFile.html', locals())
@log_Ation('Auditable records')
def AuditableRecords(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Action_List = []
    user_name = request.session['user_id']
    user = models.User.objects.get(username=user_name)
    actions = models.ActionLog.objects.filter(user=user).order_by('-timestamp')
    if len(actions) > 1:
        for i in actions:
            """try:
                date_tem = datetime.datetime.strptime(i.timestamp, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                date_tem = datetime.datetime.strptime(i.timestamp, "%Y-%m-%d %H:%M:%S")"""
            Time = i.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            Action_List.append([Time, user_name, i.action])


    return render(request, 'AuditableRecords.html', locals())


@log_Ation('Weight record Vital Sign')
def WeightRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Weight"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Weight = observation.Observation.where({'patient': NHINumber, 'code': '29463-7', '_sort': '-date'}).perform(
        smart.server)
    Weight_tem = []
    Weight_TimeList = []
    Weight_DataList = []
    Weight_YearDic = {}
    Weight_MonthDic = {}
    Weight_DayDic = {}
    Weight_DataList1 = []
    Weight_DataList2 = []
    # one month
    Weight_DataList3 = []
    # one years
    Weight_DataList4 = []
    # all
    Weight_DataList5 = []
    if Weight.entry != None:
        Weight = fetch_all_pages(Weight)
        # Weight = [ob.resource for ob in Weight.entry]
        if len(Weight) > 0:
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Weight:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        Weight_tem.append(i)
                else:
                    Weight_tem.append(i)
            Weight = Weight_tem
            for i in Weight:
                print("Weight Test-----------------")
                if i.effectiveDateTime != None:
                    Weight_TimeList.append(i.effectiveDateTime.isostring)
                    # Height_DataList.append(str(i.valueQuantity.value) + " " + i.valueQuantity.unit)
                    Weight_DataList.append(float(i.valueQuantity.value))

            if Weight_TimeList != []:
                for i in range(len(Weight_TimeList)):
                    # Height_TimeList[i] = Height_TimeList[i][:-1]
                    # Height_TimeList[i] = Height_TimeList[i][:10] + " " + Height_TimeList[i][11:]
                    Weight_DataList1.append([Weight_TimeList[i], Weight_DataList[i]])
                    Weight_DataList1.reverse()
                    Weight_DataList2.append([Weight_TimeList[i], str(Weight_DataList[i])])

                try:
                    date_tem = datetime.datetime.strptime(Weight_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Weight_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Weight_TimeList[0], "%Y-%m-%d")
                try:
                    Weight_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Weight_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Weight_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Weight_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Weight_MonthTem)
                Weight_DataList1.sort(key=lambda x: x[0])
                Weight_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Weight_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Weight_DayDic:
                        Weight_DayDic[str(date_tem.date())].append(data)
                    else:
                        Weight_DayDic[str(date_tem.date())] = [data]
                for time, value in Weight_DayDic.items():
                    average = sum(value) / len(value)
                    Weight_DataList5.append([time, average])
                for t, data in Weight_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Weight_MonthTem:
                        Weight_DataList3.append([t, data])
                    if date_tem > Weight_YearTem:
                        Weight_DataList4.append([t, data])
                print(Weight_YearDic, Weight_MonthDic, Weight_DayDic)
                print(Weight_DataList3, Weight_DataList4, Weight_DataList5)
            Weight_DataList1 = json.dumps(Weight_DataList1)
            Weight_DataList3 = json.dumps(Weight_DataList3)
            Weight_DataList4 = json.dumps(Weight_DataList4)
            Weight_DataList5 = json.dumps(Weight_DataList5)
    return render(request, 'Weight_Record_VitalSign.html', locals())


@log_Ation('Height record Vital Sign')
def HeightRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }

    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Height"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Height = observation.Observation.where({'patient': NHINumber, 'code': '8302-2', '_sort': '-date'}).perform(
        smart.server)
    Height_TimeList = []
    Height_DataList = []
    Height_YearDic = {}
    Height_MonthDic = {}
    Height_DayDic = {}
    Height_DataList1 = []
    Height_DataList2 = []
    # one month
    Height_DataList3 = []
    # one years
    Height_DataList4 = []
    # all
    Height_DataList5 = []
    if Height.entry != None:
        Height = fetch_all_pages(Height)
        # Height = [ob.resource for ob in Height.entry]
        Height_tem = []
        if len(Height) > 0:
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Height:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        Height_tem.append(i)
                else:
                    Height_tem.append(i)
            Height = Height_tem

            for i in Height:
                print("Height Test-----------------")
                if i.effectiveDateTime != None:
                    Height_TimeList.append(i.effectiveDateTime.isostring)
                    # Height_DataList.append(str(i.valueQuantity.value) + " " + i.valueQuantity.unit)
                    Height_DataList.append(float(i.valueQuantity.value))

            if Height_TimeList != []:
                for i in range(len(Height_TimeList)):
                    # Height_TimeList[i] = Height_TimeList[i][:-1]
                    # Height_TimeList[i] = Height_TimeList[i][:10] + " " + Height_TimeList[i][11:]
                    Height_DataList1.append([Height_TimeList[i], Height_DataList[i]])
                    Height_DataList1.reverse()
                    Height_DataList2.append([Height_TimeList[i], str(Height_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Height_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Height_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Height_TimeList[0], "%Y-%m-%d")
                try:
                    Height_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Height_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                 "%Y-%m-%d")
                try:
                    Height_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Height_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                "%Y-%m-%d")
                print(Height_MonthTem)
                Height_DataList1.sort(key=lambda x: x[0])
                Height_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Height_DataList1:
                    print(t, data)

                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Height_DayDic:
                        Height_DayDic[str(date_tem.date())].append(data)
                    else:
                        Height_DayDic[str(date_tem.date())] = [data]
                for time, value in Height_DayDic.items():
                    average = sum(value) / len(value)
                    Height_DataList5.append([time, average])
                for t, data in Height_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Height_MonthTem:
                        Height_DataList3.append([t, data])
                    if date_tem > Height_YearTem:
                        Height_DataList4.append([t, data])
                print(Height_YearDic, Height_MonthDic, Height_DayDic)
                print(Height_DataList3, Height_DataList4, Height_DataList5)
            Height_DataList1 = json.dumps(Height_DataList1)
            Height_DataList3 = json.dumps(Height_DataList3)
            Height_DataList4 = json.dumps(Height_DataList4)
            Height_DataList5 = json.dumps(Height_DataList5)
    return render(request, 'Height_Record_VitalSign.html', locals())


@log_Ation('Temperature record Vital Sign')
def TemperatureRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Temperature"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Temperature = observation.Observation.where({'patient': NHINumber, 'code': '8310-5', '_sort': '-date'}).perform(
        smart.server)
    Temperature_TimeList = []
    Temperature_DataList = []
    Temperature_YearDic = {}
    Temperature_MonthDic = {}
    Temperature_DayDic = {}
    Temperature_DataList1 = []
    Temperature_DataList2 = []
    # one month
    Temperature_DataList3 = []
    # one years
    Temperature_DataList4 = []
    # all
    Temperature_DataList5 = []
    if Temperature.entry != None:
        Temperature = fetch_all_pages(Temperature)
        # Temperature = [ob.resource for ob in Temperature.entry]
        if len(Temperature) > 0:
            Temperature_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Temperature:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        Temperature_tem.append(i)
                else:
                    Temperature_tem.append(i)
            Temperature = Temperature_tem

            for i in Temperature:
                print("Temperature Test-----------------")
                if i.effectiveDateTime != None:
                    Temperature_TimeList.append(i.effectiveDateTime.isostring)

                    Temperature_DataList.append(float(i.valueQuantity.value))

            if Temperature_TimeList != []:
                for i in range(len(Temperature_TimeList)):
                    Temperature_DataList1.append([Temperature_TimeList[i], Temperature_DataList[i]])
                    Temperature_DataList1.reverse()
                    Temperature_DataList2.append([Temperature_TimeList[i], str(Temperature_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Temperature_TimeList[0], "%Y-%m-%d")
                try:
                    Temperature_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                      "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Temperature_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                      "%Y-%m-%d")
                try:
                    Temperature_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                     "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Temperature_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                     "%Y-%m-%d")
                print(Temperature_MonthTem)
                Temperature_DataList1.sort(key=lambda x: x[0])
                Temperature_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Temperature_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Temperature_DayDic:
                        Temperature_DayDic[str(date_tem.date())].append(data)
                    else:
                        Temperature_DayDic[str(date_tem.date())] = [data]
                for time, value in Temperature_DayDic.items():
                    average = sum(value) / len(value)
                    Temperature_DataList5.append([time, average])
                for t, data in Temperature_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Temperature_MonthTem:
                        Temperature_DataList3.append([t, data])
                    if date_tem > Temperature_YearTem:
                        Temperature_DataList4.append([t, data])
                print(Temperature_YearDic, Temperature_MonthDic, Temperature_DayDic)
                print(Temperature_DataList3, Temperature_DataList4, Temperature_DataList5)
            Temperature_DataList1 = json.dumps(Temperature_DataList1)
            Temperature_DataList3 = json.dumps(Temperature_DataList3)
            Temperature_DataList4 = json.dumps(Temperature_DataList4)
            Temperature_DataList5 = json.dumps(Temperature_DataList5)
    return render(request, 'Temperature_Record_VitalSign.html', locals())


@log_Ation('Steps record Vital Sign')
def StepsRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Steps"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Steps = observation.Observation.where({'patient': NHINumber, 'code': '41950-7', '_sort': '-date'}).perform(
        smart.server)
    Steps_TimeList = []
    Steps_DataList = []
    Steps_YearDic = {}
    Steps_MonthDic = {}
    Steps_DayDic = {}
    Steps_DataList1 = []
    Steps_DataList2 = []
    # one month
    Steps_DataList3 = []
    # one years
    Steps_DataList4 = []
    # all
    Steps_DataList5 = []
    if Steps.entry != None:
        Steps = fetch_all_pages(Steps)
        # Steps = [ob.resource for ob in Steps.entry]
        if len(Steps) > 0:
            Steps_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Steps:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        Steps_tem.append(i)
                else:
                    Steps_tem.append(i)
            Steps = Steps_tem
            for i in Steps:
                print("Steps Test-----------------")
                if i.effectiveDateTime != None:
                    Steps_TimeList.append(i.effectiveDateTime.isostring)

                    Steps_DataList.append(float(i.valueQuantity.value))

            if Steps_TimeList != []:
                for i in range(len(Steps_TimeList)):
                    Steps_DataList1.append([Steps_TimeList[i], Steps_DataList[i]])
                    Steps_DataList1.reverse()
                    Steps_DataList2.append([Steps_TimeList[i], str(Steps_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Steps_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Steps_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Steps_TimeList[0], "%Y-%m-%d")
                try:
                    Steps_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Steps_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                "%Y-%m-%d")
                try:
                    Steps_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                               "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Steps_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                               "%Y-%m-%d")
                print(Steps_MonthTem)
                Steps_DataList1.sort(key=lambda x: x[0])
                Steps_DataList2.sort(key=lambda x: x[0], reverse=True)

                for t, data in Steps_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Steps_DayDic:
                        Steps_DayDic[str(date_tem.date())].append(data)
                    else:
                        Steps_DayDic[str(date_tem.date())] = [data]
                for time, value in Steps_DayDic.items():
                    average = sum(value) / len(value)
                    Steps_DataList5.append([time, average])
                for t, data in Steps_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Steps_MonthTem:
                        Steps_DataList3.append([t, data])
                    if date_tem > Steps_YearTem:
                        Steps_DataList4.append([t, data])
                print(Steps_YearDic, Steps_MonthDic, Steps_DayDic)
                print(Steps_DataList3, Steps_DataList4, Steps_DataList5)
            Steps_DataList1 = json.dumps(Steps_DataList1)
            Steps_DataList3 = json.dumps(Steps_DataList3)
            Steps_DataList4 = json.dumps(Steps_DataList4)
            Steps_DataList5 = json.dumps(Steps_DataList5)
    return render(request, 'Steps_Record_VitalSign.html', locals())


@log_Ation('BMI record Vital Sign')
def BMIRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["BMI"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    BMI = observation.Observation.where({'patient': NHINumber, 'code': '39156-5', '_sort': '-date'}).perform(
        smart.server)
    BMI_TimeList = []
    BMI_DataList = []
    BMI_YearDic = {}
    BMI_MonthDic = {}
    BMI_DayDic = {}
    BMI_DataList1 = []
    BMI_DataList2 = []
    # one month
    BMI_DataList3 = []
    # one years
    BMI_DataList4 = []
    # all
    BMI_DataList5 = []
    if BMI.entry != None:
        BMI = fetch_all_pages(BMI)
        # BMI = [ob.resource for ob in BMI.entry]
        if len(BMI) > 0:
            BMI_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in BMI:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        BMI_tem.append(i)
                else:
                    BMI_tem.append(i)
            BMI = BMI_tem
            for i in BMI:
                print("BMI Test-----------------")
                if i.effectiveDateTime != None:
                    BMI_TimeList.append(i.effectiveDateTime.isostring)

                    BMI_DataList.append(float(i.valueQuantity.value))

            if BMI_TimeList != []:
                for i in range(len(BMI_TimeList)):
                    BMI_DataList1.append([BMI_TimeList[i], BMI_DataList[i]])
                    BMI_DataList1.reverse()
                    BMI_DataList2.append([BMI_TimeList[i], str(BMI_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(BMI_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(BMI_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(BMI_TimeList[0], "%Y-%m-%d")
                try:
                    BMI_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                              "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BMI_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                              "%Y-%m-%d")
                try:
                    BMI_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                             "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BMI_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                             "%Y-%m-%d")
                print(BMI_MonthTem)
                BMI_DataList1.sort(key=lambda x: x[0])
                BMI_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in BMI_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in BMI_DayDic:
                        BMI_DayDic[str(date_tem.date())].append(data)
                    else:
                        BMI_DayDic[str(date_tem.date())] = [data]
                for time, value in BMI_DayDic.items():
                    average = sum(value) / len(value)
                    BMI_DataList5.append([time, average])
                for t, data in BMI_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > BMI_MonthTem:
                        BMI_DataList3.append([t, data])
                    if date_tem > BMI_YearTem:
                        BMI_DataList4.append([t, data])
                print(BMI_YearDic, BMI_MonthDic, BMI_DayDic)
                print(BMI_DataList3, BMI_DataList4, BMI_DataList5)
            BMI_DataList1 = json.dumps(BMI_DataList1)
            BMI_DataList3 = json.dumps(BMI_DataList3)
            BMI_DataList4 = json.dumps(BMI_DataList4)
            BMI_DataList5 = json.dumps(BMI_DataList5)
    return render(request, 'BMI_Record_VitalSign.html', locals())


@log_Ation('Blood pressure record Vital Sign')
def BloodPressureRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    # higher lower
    Legend_Data = ["Systolic Blood Pressure", "Diastolic Blood Pressure"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    """if BP.entry != None:
        BP = [ob.resource for ob in BP.entry]
        if len(BP) > 0:
            BP_Last = str(str(BP[0].component[0].valueQuantity.value) + "/" + str(BP[0].component[1].valueQuantity.value))
            if len(BP) > 1:
                BP_Trend = str(BP[0].component[0].valueQuantity.value - BP[1].component[0].valueQuantity.value) + "/" + str(BP[0].component[1].valueQuantity.value - BP[1].component[1].valueQuantity.value)
            else:
                BP_Trend = "None"
        else:
            BP_Last = "None"
    else:
        BP_Last = "None"
        BP_Trend = "None"
        """
    NHINumber = request.session['NHINumber']
    BloodPressure = observation.Observation.where({'patient': NHINumber, 'code': '85354-9', '_sort': '-date'}).perform(
        smart.server)
    BloodPressure_TimeList = []
    # lower
    DiastolicBloodPressure_DataList = []
    DiastolicBloodPressure_YearDic = {}
    DiastolicBloodPressure_MonthDic = {}
    DiastolicBloodPressure_DayDic = {}
    # higher
    SystolicBloodPressure_DataList = []
    SystolicBloodPressure_YearDic = {}
    SystolicBloodPressure_MonthDic = {}
    SystolicBloodPressure_DayDic = {}
    SystolicBloodPressure_DataList1 = []
    # SystolicBloodPressure_DataList2 = []
    DiastolicBloodPressure_DataList1 = []
    # DiastolicBloodPressure_DataList2 = []
    BloodPressure_DataList2 = []

    # one month
    SystolicBloodPressure_DataList3 = []
    # one years
    SystolicBloodPressure_DataList4 = []
    # all
    SystolicBloodPressure_DataList5 = []
    # one month
    DiastolicBloodPressure_DataList3 = []
    # one years
    DiastolicBloodPressure_DataList4 = []
    # all
    DiastolicBloodPressure_DataList5 = []
    if BloodPressure.entry != None:
        BloodPressure = fetch_all_pages(BloodPressure)
        # BloodPressure = [ob.resource for ob in BloodPressure.entry]
        if len(BloodPressure) > 0:
            BloodPressure_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in BloodPressure:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        BloodPressure_tem.append(i)
                else:
                    BloodPressure_tem.append(i)
            BloodPressure = BloodPressure_tem
            for i in BloodPressure:
                print("BloodPressure Test-----------------")
                if i.effectiveDateTime != None:
                    BloodPressure_TimeList.append(i.effectiveDateTime.isostring)
                    for o in i.component:
                        code_List = o.code.coding
                        for code in code_List:
                            if code.code == "8480-6" or code.code == "271649006" or code.code == "bp-s":
                                SystolicBloodPressure_DataList.append(float(o.valueQuantity.value))
                                print("8480-6")
                            if code.code == "8462-4":
                                DiastolicBloodPressure_DataList.append(float(o.valueQuantity.value))
                                print("8462-4")
                        print(o.valueQuantity.value)

            if BloodPressure_TimeList != []:
                for i in range(len(BloodPressure_TimeList)):
                    print(BloodPressure_TimeList)
                    print(SystolicBloodPressure_DataList)
                    SystolicBloodPressure_DataList1.append(
                        [BloodPressure_TimeList[i], SystolicBloodPressure_DataList[i]])
                    SystolicBloodPressure_DataList1.reverse()

                    DiastolicBloodPressure_DataList1.append(
                        [BloodPressure_TimeList[i], DiastolicBloodPressure_DataList[i]])
                    DiastolicBloodPressure_DataList1.reverse()

                    BloodPressure_DataList2.append([BloodPressure_TimeList[i], str(SystolicBloodPressure_DataList[i]),
                                                    str(DiastolicBloodPressure_DataList[i])])

                try:
                    date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(BloodPressure_TimeList[0], "%Y-%m-%d")
                try:
                    BloodPressure_MonthTem = datetime.datetime.strptime(
                        str((date_tem.date() - relativedelta(months=1))), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BloodPressure_MonthTem = datetime.datetime.strptime(
                        str((date_tem.date() - relativedelta(months=1))),
                        "%Y-%m-%d")
                try:
                    BloodPressure_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                       "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    BloodPressure_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                       "%Y-%m-%d")
                print(BloodPressure_MonthTem)
                SystolicBloodPressure_DataList1.sort(key=lambda x: x[0])
                BloodPressure_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in SystolicBloodPressure_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if str(date_tem.date()) in SystolicBloodPressure_DayDic:
                        SystolicBloodPressure_DayDic[str(date_tem.date())].append(data)
                    else:
                        SystolicBloodPressure_DayDic[str(date_tem.date())] = [data]
                for time, value in SystolicBloodPressure_DayDic.items():
                    average = sum(value) / len(value)
                    SystolicBloodPressure_DataList5.append([time, average])
                for t, data in SystolicBloodPressure_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > BloodPressure_MonthTem:
                        SystolicBloodPressure_DataList3.append([t, data])
                    if date_tem > BloodPressure_YearTem:
                        SystolicBloodPressure_DataList4.append([t, data])
                DiastolicBloodPressure_DataList1.sort(key=lambda x: x[0])
                BloodPressure_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in DiastolicBloodPressure_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if str(date_tem.date()) in DiastolicBloodPressure_DayDic:
                        DiastolicBloodPressure_DayDic[str(date_tem.date())].append(data)
                    else:
                        DiastolicBloodPressure_DayDic[str(date_tem.date())] = [data]
                for time, value in DiastolicBloodPressure_DayDic.items():
                    average = sum(value) / len(value)
                    DiastolicBloodPressure_DataList5.append([time, average])
                for t, data in DiastolicBloodPressure_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > BloodPressure_MonthTem:
                        DiastolicBloodPressure_DataList3.append([t, data])
                    if date_tem > BloodPressure_YearTem:
                        DiastolicBloodPressure_DataList4.append([t, data])
                # print(BloodPressure_YearDic, BloodPressure_MonthDic, BloodPressure_DayDic)
                # print(BloodPressure_DataList3,BloodPressure_DataList4,BloodPressure_DataList5)

                # BloodPressure_DataList1 = json.dumps(BloodPressure_DataList1)
            SystolicBloodPressure_DataList3 = json.dumps(SystolicBloodPressure_DataList3)
            SystolicBloodPressure_DataList4 = json.dumps(SystolicBloodPressure_DataList4)
            SystolicBloodPressure_DataList5 = json.dumps(SystolicBloodPressure_DataList5)

            DiastolicBloodPressure_DataList3 = json.dumps(DiastolicBloodPressure_DataList3)
            DiastolicBloodPressure_DataList4 = json.dumps(DiastolicBloodPressure_DataList4)
            DiastolicBloodPressure_DataList5 = json.dumps(DiastolicBloodPressure_DataList5)
    return render(request, 'BloodPressure_Record_VitalSign.html', locals())


@log_Ation('Heart rate record Vital Sign')
def HeartRateRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["HeartRate"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    HeartRate = observation.Observation.where({'patient': NHINumber, 'code': '8867-4', '_sort': '-date'}).perform(
        smart.server)
    HeartRate_TimeList = []
    HeartRate_DataList = []
    HeartRate_YearDic = {}
    HeartRate_MonthDic = {}
    HeartRate_DayDic = {}
    HeartRate_DataList1 = []
    HeartRate_DataList2 = []
    # one month
    HeartRate_DataList3 = []
    # one years
    HeartRate_DataList4 = []
    # all
    HeartRate_DataList5 = []
    if HeartRate.entry != None:
        HeartRate = fetch_all_pages(HeartRate)
        # HeartRate = [ob.resource for ob in HeartRate.entry]
        if len(HeartRate) > 0:
            HeartRate_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in HeartRate:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        HeartRate_tem.append(i)
                else:
                    HeartRate_tem.append(i)
            HeartRate = HeartRate_tem
            for i in HeartRate:
                print("HeartRate Test-----------------")
                if i.effectiveDateTime != None:
                    HeartRate_TimeList.append(i.effectiveDateTime.isostring)

                    HeartRate_DataList.append(float(i.valueQuantity.value))

            if HeartRate_TimeList != []:
                for i in range(len(HeartRate_TimeList)):
                    HeartRate_DataList1.append([HeartRate_TimeList[i], HeartRate_DataList[i]])
                    HeartRate_DataList1.reverse()
                    HeartRate_DataList2.append([HeartRate_TimeList[i], str(HeartRate_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(HeartRate_TimeList[0], "%Y-%m-%d")
                try:
                    HeartRate_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                    "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    HeartRate_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                    "%Y-%m-%d")
                try:
                    HeartRate_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                   "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    HeartRate_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                   "%Y-%m-%d")
                print(HeartRate_MonthTem)
                HeartRate_DataList1.sort(key=lambda x: x[0])
                HeartRate_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in HeartRate_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in HeartRate_DayDic:
                        HeartRate_DayDic[str(date_tem.date())].append(data)
                    else:
                        HeartRate_DayDic[str(date_tem.date())] = [data]
                for time, value in HeartRate_DayDic.items():
                    average = sum(value) / len(value)
                    HeartRate_DataList5.append([time, average])
                for t, data in HeartRate_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > HeartRate_MonthTem:
                        HeartRate_DataList3.append([t, data])
                    if date_tem > HeartRate_YearTem:
                        HeartRate_DataList4.append([t, data])
                print(HeartRate_YearDic, HeartRate_MonthDic, HeartRate_DayDic)
                print(HeartRate_DataList3, HeartRate_DataList4, HeartRate_DataList5)
            HeartRate_DataList1 = json.dumps(HeartRate_DataList1)
            HeartRate_DataList3 = json.dumps(HeartRate_DataList3)
            HeartRate_DataList4 = json.dumps(HeartRate_DataList4)
            HeartRate_DataList5 = json.dumps(HeartRate_DataList5)
    return render(request, 'HeartRate_Record_VitalSign.html', locals())


@log_Ation('Respiration record Vital Sign')
def RespirationRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Respiration"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Respiration = observation.Observation.where({'patient': NHINumber, 'code': '9279-1', '_sort': '-date'}).perform(
        smart.server)
    Respiration_TimeList = []
    Respiration_DataList = []
    Respiration_YearDic = {}
    Respiration_MonthDic = {}
    Respiration_DayDic = {}
    Respiration_DataList1 = []
    Respiration_DataList2 = []
    # one month
    Respiration_DataList3 = []
    # one years
    Respiration_DataList4 = []
    # all
    Respiration_DataList5 = []
    if Respiration.entry != None:
        Respiration = fetch_all_pages(Respiration)
        # Respiration = [ob.resource for ob in Respiration.entry]
        if len(Respiration) > 0:
            Respiration_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Respiration:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        Respiration_tem.append(i)
                else:
                    Respiration_tem.append(i)
            Respiration = Respiration_tem
            for i in Respiration:
                print("Respiration Test-----------------")
                if i.effectiveDateTime != None:
                    Respiration_TimeList.append(i.effectiveDateTime.isostring)

                    Respiration_DataList.append(float(i.valueQuantity.value))

            if Respiration_TimeList != []:
                for i in range(len(Respiration_TimeList)):
                    Respiration_DataList1.append([Respiration_TimeList[i], Respiration_DataList[i]])
                    Respiration_DataList1.reverse()
                    Respiration_DataList2.append([Respiration_TimeList[i], str(Respiration_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Respiration_TimeList[0], "%Y-%m-%d")
                try:
                    Respiration_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                      "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Respiration_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                      "%Y-%m-%d")
                try:
                    Respiration_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                     "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Respiration_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                     "%Y-%m-%d")
                print(Respiration_MonthTem)
                Respiration_DataList1.sort(key=lambda x: x[0])
                Respiration_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Respiration_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Respiration_DayDic:
                        Respiration_DayDic[str(date_tem.date())].append(data)
                    else:
                        Respiration_DayDic[str(date_tem.date())] = [data]
                for time, value in Respiration_DayDic.items():
                    average = sum(value) / len(value)
                    Respiration_DataList5.append([time, average])
                for t, data in Respiration_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Respiration_MonthTem:
                        Respiration_DataList3.append([t, data])
                    if date_tem > Respiration_YearTem:
                        Respiration_DataList4.append([t, data])
                print(Respiration_YearDic, Respiration_MonthDic, Respiration_DayDic)
                print(Respiration_DataList3, Respiration_DataList4, Respiration_DataList5)
            Respiration_DataList1 = json.dumps(Respiration_DataList1)
            Respiration_DataList3 = json.dumps(Respiration_DataList3)
            Respiration_DataList4 = json.dumps(Respiration_DataList4)
            Respiration_DataList5 = json.dumps(Respiration_DataList5)
    return render(request, 'Respiration_Record_VitalSign.html', locals())


@log_Ation('Smoking record Vital Sign')
def SmokingRecordVitalSign(request):
    if not request.session.get('is_login', None):
        return redirect('/PHR/login/')
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'https://server.fire.ly',
    }
    username = request.session['user_id']
    user = models.User.objects.get(username=username)
    request.user = username
    Legend_Data = ["Smoking"]
    Legend_Data = json.dumps(Legend_Data)
    smart = client.FHIRClient(settings=settings)
    NHINumber = request.session['NHINumber']
    Smoking = observation.Observation.where({'patient': NHINumber, 'code': '63773-6', '_sort': '-date'}).perform(
        smart.server)
    Smoking_TimeList = []
    Smoking_DataList = []
    Smoking_YearDic = {}
    Smoking_MonthDic = {}
    Smoking_DayDic = {}
    Smoking_DataList1 = []
    Smoking_DataList2 = []
    # one month
    Smoking_DataList3 = []
    # one years
    Smoking_DataList4 = []
    # all
    Smoking_DataList5 = []
    if Smoking.entry != None:
        Smoking = fetch_all_pages(Smoking)
        # Smoking = [ob.resource for ob in Smoking.entry]
        if len(Smoking) > 0:
            Smoking_tem = []
            p_id = request.session['patient_id']
            patient = models.Patient.objects.filter(cid=p_id)
            if len(patient) > 1:
                patient = patient.get(name=request.session['patient_name'])
            else:
                patient = patient[0]
            organization_id = patient.organization_id

            for i in Smoking:
                if i.performer:
                    if organization_id != i.performer[0].reference.spilt('/')[-1]:
                        Smoking_tem.append(i)
                else:
                    Smoking_tem.append(i)
            Smoking = Smoking_tem
            for i in Smoking:
                print("Smoking Test-----------------")
                if i.effectiveDateTime != None:
                    Smoking_TimeList.append(i.effectiveDateTime.isostring)

                    Smoking_DataList.append(float(i.valueQuantity.value))

            if Smoking_TimeList != []:
                for i in range(len(Smoking_TimeList)):
                    Smoking_DataList1.append([Smoking_TimeList[i], Smoking_DataList[i]])
                    Smoking_DataList1.reverse()
                    Smoking_DataList2.append([Smoking_TimeList[i], str(Smoking_DataList[i])])
                try:
                    date_tem = datetime.datetime.strptime(Smoking_TimeList[0], "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_tem = datetime.datetime.strptime(Smoking_TimeList[0], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        date_tem = datetime.datetime.strptime(Smoking_TimeList[0], "%Y-%m-%d")
                try:
                    Smoking_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                  "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Smoking_MonthTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(months=1))),
                                                                  "%Y-%m-%d")
                try:
                    Smoking_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                 "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    Smoking_YearTem = datetime.datetime.strptime(str((date_tem.date() - relativedelta(years=1))),
                                                                 "%Y-%m-%d")
                print(Smoking_MonthTem)
                Smoking_DataList1.sort(key=lambda x: x[0])
                Smoking_DataList2.sort(key=lambda x: x[0], reverse=True)
                for t, data in Smoking_DataList1:
                    print(t, data)
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")

                    if str(date_tem.date()) in Smoking_DayDic:
                        Smoking_DayDic[str(date_tem.date())].append(data)
                    else:
                        Smoking_DayDic[str(date_tem.date())] = [data]
                for time, value in Smoking_DayDic.items():
                    average = sum(value) / len(value)
                    Smoking_DataList5.append([time, average])
                for t, data in Smoking_DataList5:
                    try:
                        date_tem = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date_tem = datetime.datetime.strptime(t, "%Y-%m-%d")
                    if date_tem > Smoking_MonthTem:
                        Smoking_DataList3.append([t, data])
                    if date_tem > Smoking_YearTem:
                        Smoking_DataList4.append([t, data])
                print(Smoking_YearDic, Smoking_MonthDic, Smoking_DayDic)
                print(Smoking_DataList3, Smoking_DataList4, Smoking_DataList5)
            Smoking_DataList1 = json.dumps(Smoking_DataList1)
            Smoking_DataList3 = json.dumps(Smoking_DataList3)
            Smoking_DataList4 = json.dumps(Smoking_DataList4)
            Smoking_DataList5 = json.dumps(Smoking_DataList5)
    return render(request, 'Smoking_Record_VitalSign.html', locals())