from fhirclient import client
from fhirclient.models.patient import Patient
import fhirclient.models.humanname as hn
from fhirclient.models import fhirdate, bundle as b, meta, resource, fhirabstractresource, observation, address
from fhirclient.models import patient, contactpoint, period, codeableconcept, coding, quantity, fhirreference
from fhirclient.models import medicationrequest, dosage, extension, duration, timing, ratio, medication, bodystructure
from fhirclient.models import device, allergyintolerance, diagnosticreport, imagingstudy, attachment, binary, media, encounter
import time
import base64

def test_Drug(patient):
    drug = medicationrequest.MedicationRequest()
    reference3 = fhirreference.FHIRReference()
    # reference3.type = "Patient"
    reference3.reference = "Patient/" + patient.id
    drug.subject = reference3
    drug.status = "active"
    drug.intent = "order"


    drug.authoredOn = fhirdate.FHIRDate('2016-07-01')
    contain1 = medication.Medication()
    ingredient1 = medication.MedicationIngredient()
    extension1 = extension.Extension()
    extension1.url = "http://jpfhir.jp/fhir/core/Extension/StructureDefinition/JP_Medication_Ingredient_DrugNo"
    extension1.valueInteger = 1
    ingredient1.extension = [extension1]
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '100558502'
    coding1.system = "urn:oid:1.2.392.100495.20.2.74"
    coding1.display = "ホリゾン注射液１０ｍｇ"
    code1.coding = [coding1]
    code1.text = "ホリゾン注射液１０ｍｇ"
    ingredient1.itemCodeableConcept = code1
    ratio1 = ratio.Ratio()
    extension2 = extension.Extension()
    extension2.url = "http://jpfhir.jp/fhir/core/Extension/StructureDefinition/JP_Medication_Strength_StrengthType"
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = '1'
    coding2.system = "urn:oid:1.2.392.100495.20.2.22"
    coding2.display = "製剤量"
    code2.coding = [coding2]
    code2.text = "製剤量"
    extension2.valueCodeableConcept = code2
    ratio1.extension = [extension2]
    quantity1 = quantity.Quantity()
    quantity1.value = 1
    quantity1.unit = "アンプル"
    quantity1.system = "urn:oid:1.2.392.100495.20.2.101"
    quantity1.code = "AMP"
    ratio1.numerator = quantity1
    quantity2 = quantity.Quantity()
    quantity2.value = 1
    quantity2.unit = "回"
    quantity2.system = "urn:oid:1.2.392.100495.20.2.101"
    quantity2.code = "KAI"
    ratio1.denominator = quantity2
    ingredient1.strength = ratio1
    contain1.ingredient = [ingredient1]
    contain1.id = "b9aeb80b-76ba-4bfd-80e5-25e9a9f8b91a"


    reference2 = fhirreference.FHIRReference()
    # reference2.type = "Medication"
    reference2.reference = "#b9aeb80b-76ba-4bfd-80e5-25e9a9f8b91a"
    drug.medicationReference = reference2
    drug.contained = [contain1]
    return drug

def create_ImagingStudy(patient):
    imaging = imagingstudy.ImagingStudy()
    series = imagingstudy.ImagingStudySeries()
    instance1 = imagingstudy.ImagingStudySeriesInstance()
    #imaging.series =

def create_Media(patient):
    with open('../test.png', 'rb') as f:
        data = f.read()
    data = base64.b64encode(data).decode()
    media1 = media.Media()
    attachment1 = attachment.Attachment()
    attachment1.contentType = "image/png"
    attachment1.url = "Binary/ea1bdeaf-c20d-490a-9ffa-3f07eb8495b7"
    attachment1.data = data
    media1.content = attachment1
    reference1 = fhirreference.FHIRReference()
    reference1.reference = "Patient/" + patient.id
    reference1.display = "Patient"
    media1.subject = reference1
    media1.createdDateTime = fhirdate.FHIRDate('2023-01-01T10:00:00+08:00')
    media1.status = "in-progress"
    return media1

def create_Binary(patient):
    with open('../test.png', 'rb') as f:
        data = f.read()
    data = base64.b64encode(data).decode()
    binary1 = binary.Binary()
    #image/jpeg
    #binary1.contentType = 'application/pdf'
    binary1.contentType = 'image/png'
    binary1.data = data
    reference1 = fhirreference.FHIRReference()
    #binaryID: 812b10a0-53a5-44f0-9563-bfe830e9a591 including securityContext 好像没用
    reference1.reference = "DiagnosticReport/d3723d18-f68d-4660-b560-21ec6890170f"
    reference1.type = "DiagnosticReport"
    binary1.securityContext = reference1
    response1 = binary1.create(smart.server)
    if response1:
        print(f"Create binary success, id: {response1['id']}")
def create_Lab(patient):
    lab = diagnosticreport.DiagnosticReport()
    lab.status = "final"
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '38269-7'
    coding1.system = "http://loinc.org"
    coding1.display = "DXA BONE DENSITOMETRY"
    code1.coding = [coding1]
    code1.text = "DXA BONE DENSITOMETRY"
    lab.code = code1
    reference1 = fhirreference.FHIRReference()
    reference1.reference = "Patient/" + patient.id
    lab.subject = reference1
    lab.effectiveDateTime = fhirdate.FHIRDate('2008-07-01')
    lab.issued = fhirdate.FHIRDate('2008-07-02T09:23:00+10:00')
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = '391040000'
    coding2.system = "http://snomed.info/sct"
    coding2.display = "At risk of osteoporotic fracture"
    code2.coding = [coding2]
    code2.text = "At risk of osteoporotic fracture"
    lab.conclusionCode = [code2]
    #entire report
    attachment1 = attachment.Attachment()
    attachment1.contentType = "image/jpeg"
    #attachment1.data = "ea1bdeaf-c20d-490a-9ffa-3f07eb8495b7"
    attachment1.url = "Binary/ea1bdeaf-c20d-490a-9ffa-3f07eb8495b7"
    lab.presentedForm = [attachment1]

    # key image 指向 media对象
    media1 = diagnosticreport.DiagnosticReportMedia()
    reference2 = fhirreference.FHIRReference()
    reference2.reference = "Media/f4c50d2b-8b5c-4257-9c38-fc7ad09ad978"
    reference2.type = "Media"
    media1.link = reference2
    lab.media = [media1]
    print(lab.as_json())
    return lab


def create_Allergy(patient):
    allergy1 = allergyintolerance.AllergyIntolerance()
    allergy1.category = ["food"]
    allergy1.criticality = "low"
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = 'J7F7111190'
    coding1.system = "http://jpfhir.jp/fhir/CodeSystem/***"
    coding1.display = "さば類"
    code1.coding = [coding1]
    code1.text = "ゴマサバ"
    allergy1.code = code1
    reference1 = fhirreference.FHIRReference()
    reference1.reference = "Patient/" + patient.id
    reference1.display = "Patient"
    allergy1.patient = reference1
    allergy1.onsetDateTime = fhirdate.FHIRDate('2020-01-01')
    allergy1.recordedDate = fhirdate.FHIRDate('2020-01-01')
    reaction1 = allergyintolerance.AllergyIntoleranceReaction()
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = '***'
    coding2.system = "http://jpfhir.jp/fhir/CodeSystem/***"
    coding2.display = "蕁麻疹"
    code2.coding = [coding2]
    code2.text = "じん麻疹"
    reaction1.manifestation = [code2]
    reaction1.severity = "mild"
    allergy1.reaction = [reaction1]
    code3 = codeableconcept.CodeableConcept()
    coding3 = coding.Coding()
    coding3.code = "active"
    coding3.system = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
    coding3.display = "Active"
    code3.coding = [coding3]
    allergy1.clinicalStatus = code3
    code4 = codeableconcept.CodeableConcept()
    coding4 = coding.Coding()
    coding4.code = "confirmed"
    coding4.system = "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"
    code4.coding = [coding4]
    allergy1.verificationStatus = code4
    print(allergy1.as_json())
    return allergy1

def create_Drug(type, patient):
    drug = medicationrequest.MedicationRequest()
    reference3 = fhirreference.FHIRReference()
    #reference3.type = "Patient"
    reference3.reference = "Patient/" + patient.id
    drug.subject = reference3
    drug.status = "active"
    drug.intent = "order"
    if type == "IE":
        drug.authoredOn = fhirdate.FHIRDate('2016-07-01')
        code1 = codeableconcept.CodeableConcept()
        coding1 = coding.Coding()
        coding1.code = '103835401'
        coding1.system = "urn:oid:1.2.392.200119.4.403.1"
        coding1.display = "ムコダイン錠２５０ｍｇ"
        code1.coding = [coding1]
        code1.text = "ムコダイン錠２５０ｍｇ"
        drug.medicationCodeableConcept = code1
        dosage1 = dosage.Dosage()
        extension1 = extension.Extension()
        extension1.url = "http://jpfhir.jp/fhir/core/Extension/StructureDefinition/JP_MedicationRequest_DosageInstruction_PeriodOfUse"
        period1 = period.Period()
        period1.start = fhirdate.FHIRDate('2020-01-01')
        extension1.valuePeriod = period1

        extension2 = extension.Extension()
        extension2.url = "http://jpfhir.jp/fhir/core/Extension/StructureDefinition/JP_MedicationRequest_DosageInstruction_UsageDuration"
        duration1 = duration.Duration()
        duration1.value = 3
        duration1.unit = "日"
        duration1.system = "http://unitsofmeasure.org"
        duration1.code = "d"
        extension2.valueDuration = duration1
        dosage1.extension = [extension1, extension2]
        #timing
        timing1 = timing.Timing()
        code2 = codeableconcept.CodeableConcept()
        coding2 = coding.Coding()
        coding2.code = '1013044400000000'
        coding2.system = "urn:oid:1.2.392.200250.2.2.20.20"
        coding2.display = "内服・経口・１日３回朝昼夕食後"
        code2.coding = [coding2]
        code2.text = "内服・経口・１日３回朝昼夕食後"
        timing1.code = code2
        dosage1.timing = timing1
        #route
        code3 = codeableconcept.CodeableConcept()
        coding3 = coding.Coding()
        coding3.code = 'PO'
        coding3.system = "urn:oid:2.16.840.1.113883.3.1937.777.10.5.162"
        coding3.display = "口"
        code3.coding = [coding3]
        code3.text = "口"
        dosage1.route = code3
        #method
        code4 = codeableconcept.CodeableConcept()
        coding4 = coding.Coding()
        coding4.code = '10'
        coding4.system = "urn:oid:1.2.392.200250.2.2.20.40"
        coding4.display = "経口"
        code4.coding = [coding4]
        code4.text = "経口"
        dosage1.method = code4
        #dose and rate
        DDAR = dosage.DosageDoseAndRate()
        code5 = codeableconcept.CodeableConcept()
        coding5 = coding.Coding()
        coding5.code = '1'
        coding5.system = "urn:oid:1.2.392.100495.20.2.22"
        coding5.display = "製剤量"
        code5.coding = [coding5]
        code5.text = "製剤量"
        DDAR.type = code5
        quantity1 = quantity.Quantity()
        quantity1.value = 1
        quantity1.unit = "錠"
        quantity1.system ="urn:oid:1.2.392.100495.20.2.101"
        quantity1.code = "TAB"
        DDAR.doseQuantity = quantity1
        ratio1 = ratio.Ratio()
        quantity2 = quantity.Quantity()
        quantity2.value = 3
        quantity2.unit = "錠"
        quantity2.system = "urn:oid:1.2.392.100495.20.2.101"
        quantity2.code = "TAB"
        ratio1.numerator = quantity2
        quantity3 = quantity.Quantity()
        quantity3.value = 1
        quantity3.unit = "日"
        quantity3.system = "http://unitsofmeasure.org"
        quantity3.code = "d"
        ratio1.denominator = quantity3
        DDAR.rateRatio = ratio1
        dosage1.doseAndRate = [DDAR]
        drug.dosageInstruction = [dosage1]
        #dispense request
        dispense = medicationrequest.MedicationRequestDispenseRequest()
        quantity4 = quantity.Quantity()
        quantity4.value = 9
        quantity4.unit = "錠"
        quantity4.system = "urn:oid:1.2.392.100495.20.2.101"
        quantity4.code = "TAB"
        dispense.quantity = quantity4
        duration2 = duration.Duration()
        duration2.value = 3
        duration2.unit = "日"
        duration2.system = "http://unitsofmeasure.org"
        duration2.code = "d"
        dispense.expectedSupplyDuration = duration2
        drug.dispenseRequest = dispense
    elif type == "II":
        #medication
        contain1 = medication.Medication()
        ingredient1 = medication.MedicationIngredient()
        extension1 = extension.Extension()
        extension1.url = "http://jpfhir.jp/fhir/core/Extension/StructureDefinition/JP_Medication_Ingredient_DrugNo"
        extension1.valueInteger = 1
        ingredient1.extension = [extension1]
        code1 = codeableconcept.CodeableConcept()
        coding1 = coding.Coding()
        coding1.code = '100558502'
        coding1.system = "urn:oid:1.2.392.100495.20.2.74"
        coding1.display = "ホリゾン注射液１０ｍｇ"
        code1.coding = [coding1]
        code1.text = "ホリゾン注射液１０ｍｇ"
        ingredient1.itemCodeableConcept = code1
        ratio1 = ratio.Ratio()
        extension2 = extension.Extension()
        extension2.url = "http://jpfhir.jp/fhir/core/Extension/StructureDefinition/JP_Medication_Strength_StrengthType"
        code2 = codeableconcept.CodeableConcept()
        coding2 = coding.Coding()
        coding2.code = '1'
        coding2.system = "urn:oid:1.2.392.100495.20.2.22"
        coding2.display = "製剤量"
        code2.coding = [coding2]
        code2.text = "製剤量"
        extension2.valueCodeableConcept = code2
        ratio1.extension = [extension2]
        quantity1 = quantity.Quantity()
        quantity1.value = 1
        quantity1.unit = "アンプル"
        quantity1.system = "urn:oid:1.2.392.100495.20.2.101"
        quantity1.code = "AMP"
        ratio1.numerator = quantity1
        quantity2 = quantity.Quantity()
        quantity2.value = 1
        quantity2.unit = "回"
        quantity2.system = "urn:oid:1.2.392.100495.20.2.101"
        quantity2.code = "KAI"
        ratio1.denominator = quantity2
        ingredient1.strength = ratio1
        contain1.ingredient = [ingredient1]
        contain1.id = "b9aeb80b-76ba-4bfd-80e5-25e9a9f8b91a"
        """response1 = contain1.create(smart.server)
        if response1:
            print(f"Create medication success, id: {response1['id']}")"""
        #body structure
        contain2 = bodystructure.BodyStructure()
        code3 = codeableconcept.CodeableConcept()
        coding3 = coding.Coding()
        coding3.code = "ARM"
        coding3.system = "http://terminology.hl7.org/CodeSystem/v2-0550"
        coding3.display = "腕"
        code3.coding = [coding3]
        code3.text = "腕"
        contain2.location = code3
        code4 = codeableconcept.CodeableConcept()
        coding4 = coding.Coding()
        coding4.code = "L"
        coding4.system = "http://terminology.hl7.org/CodeSystem/v2-0495"
        coding4.display = "左"
        code4.coding = [coding4]
        code4.text = "左"
        contain2.locationQualifier = [code4]
        reference1 = fhirreference.FHIRReference()
        reference1.reference = "Patient/" + patient.id
        #reference1.type = "Patient"
        contain2.patient = reference1
        contain2.id = "98a03e65-404f-4804-906d-139785ca65e9"
        """response2 = contain2.create(smart.server)
        if response2:
            print(f"Create body structure success, id: {response2['id']}")"""
        # device
        contain3 = device.Device()
        code5 = codeableconcept.CodeableConcept()
        coding5 = coding.Coding()
        coding5.code = "01"
        coding5.system = "http://jpfhir.jp/medication/99ILL"
        coding5.display = "シリンジ"
        code5.coding = [coding5]
        code5.text = "シリンジ"
        contain3.type = code5
        contain3.id = "c32641b8-7e00-4efa-b95f-118c2162c3a8"
        """response3 = contain3.create(smart.server)
        if response3:
            print(f"Create device success, id: {response3['id']}")"""
        drug.contained = [contain1, contain2, contain3]

        code6 = codeableconcept.CodeableConcept()
        coding6 = coding.Coding()
        coding6.code = "I"
        coding6.system = "http://terminology.hl7.org/CodeSystem/v2-0482"
        coding6.display = "入院患者オーダ"
        code6.coding = [coding6]
        code6.text = "入院患者オーダ"
        code7 = codeableconcept.CodeableConcept()
        coding7 = coding.Coding()
        coding7.code = "IHP"
        coding7.system = "http://jpfhir.jp/Common/CodeSystem/merit9-category"
        coding7.display = "入院処方"
        code7.coding = [coding7]
        code7.text = "入院処方"
        code8 = codeableconcept.CodeableConcept()
        coding8 = coding.Coding()
        coding8.code = "FTP"
        coding8.system = "http://jpfhir.jp/Common/CodeSystem/JHSI0001"
        coding8.display = "定時処方"
        code8.coding = [coding8]
        code8.text = "定時処方"
        drug.category = [code6, code7, code8]
        reference2 = fhirreference.FHIRReference()

        #reference2.type = "Medication"
        #找出所有属于病人的，遍历找对应的
        reference2.reference = "#b9aeb80b-76ba-4bfd-80e5-25e9a9f8b91a"
        reference2.display = "ホリゾン注射液１０ｍｇ"
        drug.medicationReference = reference2
        drug.authoredOn = fhirdate.FHIRDate('2016-07-01')
        dosage1 = dosage.Dosage()
        extension3 = extension.Extension()
        extension3.url = "http://jpfhir.jp/fhir/core/Extension/StructureDefinition/JP_MedicationRequest_DosageInstruction_Device"
        reference4 = fhirreference.FHIRReference()
        #reference4.type = "Device"
        reference4.reference = "#c32641b8-7e00-4efa-b95f-118c2162c3a8"
        extension3.valueReference = reference4
        dosage1.extension = [extension3]
        code9 = codeableconcept.CodeableConcept()
        coding9 = coding.Coding()
        coding9.code = "1"
        coding9.system = "urn:oid:1.2.392.200250.2.2.20.45"
        coding9.display = "ワンショット"
        code9.coding = [coding9]
        code9.text = "ワンショット"
        dosage1.additionalInstruction = [code9]
        timing1 = timing.Timing()
        repeat1 = timing.TimingRepeat()
        period1 = period.Period()
        period1.start = fhirdate.FHIRDate('2016-07-01T10:00:00+09:00')
        repeat1.boundsPeriod = period1
        timing1.repeat = repeat1
        dosage1.timing = timing1
        code10 = codeableconcept.CodeableConcept()
        extension4 = extension.Extension()
        extension4.url = "http://hl7.org/fhir/StructureDefinition/bodySite"
        reference5 = fhirreference.FHIRReference()
        reference5.reference = "#98a03e65-404f-4804-906d-139785ca65e9"
        #reference5.type = "BodyStructure"
        extension4.valueReference = reference5
        code10.extension = [extension4]
        dosage1.site = code10
        code11 = codeableconcept.CodeableConcept()
        coding11 = coding.Coding()
        coding11.code = "IV"
        coding11.system = "urn:oid:2.16.840.1.113883.3.1937.777.10.5.162"
        coding11.display = "静脈内"
        code11.coding = [coding11]
        code11.text = "静脈内"
        dosage1.route = code11
        code12 = codeableconcept.CodeableConcept()
        coding12 = coding.Coding()
        coding12.code = "30"
        coding12.system = "urn:oid:1.2.392.200250.2.2.20.40"
        coding12.display = "静脈注射"
        code12.coding = [coding12]
        code12.text = "静脈注射"
        dosage1.method = code12
        DDAR = dosage.DosageDoseAndRate()
        quantity3 = quantity.Quantity()
        quantity3.value = 2.0
        quantity3.unit = "mL"
        quantity3.system = "http://unitsofmeasure.org"
        quantity3.code = "mL"
        DDAR.doseQuantity = quantity3
        dosage1.doseAndRate = [DDAR]
        drug.dosageInstruction = [dosage1]
    return drug


def create_BloodPressure(value1, value2, patient):
    BP = observation.Observation()
    BP.status = "registered"
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
    subject1.reference = "Patient/" + patient.id
    BP.subject = subject1
    return BP

def create_BodyHeight(value, patient, date):
    height = observation.Observation()
    height.status = "registered"
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
    subject1.reference = "Patient/" + patient.id
    height.subject = subject1
    return height

def create_PulseRate(value, patient):
    PR = observation.Observation()
    PR.status = "registered"
    code1 = codeableconcept.CodeableConcept()
    coding1 = coding.Coding()
    coding1.code = '8867-4'
    coding1.system = "http://loinc.org"
    coding1.display = "Heart rate"
    code1.text = "Heart rate"
    code1.coding = [coding1]
    PR.code = code1
    code2 = codeableconcept.CodeableConcept()
    coding2 = coding.Coding()
    coding2.code = 'vital-signs'
    coding2.display = 'vital-signs'
    coding2.system = "http://hl7.org/fhir/ValueSet/observation-category"
    code2.coding = [coding2]
    PR.category = [code2]
    quantity1 = quantity.Quantity()
    quantity1.value = value
    quantity1.unit = 'beats/minute'
    quantity1.system = "http://unitsofmeasure.org"
    quantity1.code = '/min'
    PR.valueQuantity = quantity1
    subject1 = fhirreference.FHIRReference()
    subject1.reference = "Patient/" + patient.id
    PR.subject = subject1
    return PR

def create_RespiratoryRate(value, patient):
    RR = observation.Observation()
    RR.status = "registered"
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
    subject1.reference = "Patient/" + patient.id
    RR.subject = subject1
    return RR

def create_Patient():
    patient = Patient()
    name = hn.HumanName()
    name.given = ['Chu']
    name.family = 'Parker'
    patient.name = [name]
    patient.birthDate = fhirdate.FHIRDate('1999-01-01')
    patient.gender = 'male'
    patient.active = True
    phone = contactpoint.ContactPoint()
    period1 = period.Period()
    period1.start = fhirdate.FHIRDate('2020-01-01')
    phone.period = period1
    phone.system = "phone"
    phone.rank = 1
    phone.use = "mobile"
    phone.value = "13700009999"
    #p1.telecom = [phone]
    patient.telecom = [phone]
    patient_address = address.Address()
    patient_address.use = 'home'
    patient_address.line = ['123 Main St']
    patient_address.city = 'Anytown'
    patient_address.state = 'CA'
    patient_address.postalCode = '12345'
    patient_address.country = 'USA'
    #p1.address = [patient_address]
    patient.address = [patient_address]
    return patient
"""settings = {
    'app_id': 'my_web_app',
    'api_base': 'https://server.fire.ly',
    'patient': 'example_patient_id',
    'secret': 'my_web_app_secret'
}"""
# patient and secret are not needed
settings = {
    'app_id': 'my_web_app',
    'api_base': 'https://server.fire.ly',
}
"""settings = {
    'app_id': 'my_web_app',
    'api_base': 'http://hapi.fhir.org/baseR5/',
}"""
smart = client.FHIRClient(settings=settings)
"""
# 创建一个Patient资源
patient = Patient()
name = hn.HumanName()
name.given = ['Chu']
name.family = 'Parker'
patient.name = [name]
patient.birthDate = fhirdate.FHIRDate('1999-01-01')
patient.gender = 'male'
patient.active = True

phone = contactpoint.ContactPoint()
period = period.Period()
period.start = fhirdate.FHIRDate('2020-01-01')
phone.period = period
phone.system = "phone"
phone.rank = 1
phone.use = "mobile"
phone.value = "13700009999"
p1.telecom = [phone]
response = p1.update(smart.server)
if response:
    print("Success")

# 将Patient资源上传到FHIR服务器
response = patient.create(smart.server)
if response:
    print(f"Created patient with id: {response['id']}")
else:
    print("Failed to create patient")
    #########

    """
"""p1 = patient.Patient.read('12892', smart.server)
print("##########Patient##########")
print(smart.human_name(p1.name[0]))
print(smart.human_name(p1.name[1]))

c_time = time.ctime()
age = str(int(c_time[-4:]) - int(p1.birthDate.isostring[0:4]))
print(p1.gender, p1.birthDate.isostring, age, p1.address)
#print(p1.telecom[0].system, p1.telecom[0].use, p1.telecom[0].value)

weight = observation.Observation.where({'patient': '12892', 'code': '29463-7'}).perform(smart.server)
HR = observation.Observation.where({'patient': '12892', 'code': '8867-4'}).perform(smart.server)
BodyTem = observation.Observation.where({'patient': '12892', 'code': '8310-5'}).perform(smart.server)
BP = observation.Observation.where({'patient': '12892', 'code': '85354-9'}).perform(smart.server)
Height = observation.Observation.where({'patient': '12892', 'code': '8302-2'}).perform(smart.server)
RR = observation.Observation.where({'patient': '12892', 'code': '9279-1'}).perform(smart.server)"""

#drug1 = test_Drug(p1)
#create_Binary(p1)
#lab = create_Drug("II", p1)
#lab.id = "ebd2db35-2cb2-4fc3-bafa-cd2830fe97d4"
#p1 = create_BodyHeight(175, p1)
#p1.id = "12892"
#p1 = create_Patient()
#p1.id = "12892"
"""e1 = encounter.Encounter.read('ff791bc8-b77c-4876-8ecf-1142657bf141', smart.server)
print(e1.period.start.isostring)
print(e1.period.end.isostring)
print(e1.class_fhir.code)
print(e1.serviceProvider.display)
for i in e1.diagnosis:
    id = i.condition.reference
    id = id.split("/")
    print(id)
    print(id[-1], i.rank)"""
NHINumber = 'baede442-d962-45f1-8958-0cb838540ecf'
p1 = Patient.read(NHINumber, smart.server)
print(p1.telecom[0].system)
print(p1.telecom[0].value)
print(p1.telecom[1].value)
date = time.strftime("%Y-%m-%dT%H:%M:%S%z")
date = date[:-2] + ":" + date[-2:]
print(date)
#response = p1.update(smart.server)
#response = p1.create(smart.server)
#https://server.fire.ly/Condition/ba984427-026f-4177-b1a3-9af7fcb04e57 2
#https://server.fire.ly/Condition/b0ec7d3e-e517-408c-a1ec-46dba3e6b2bf 1

#if response:
#    print(f"Created success, id: {response['id']}")
"""BP = create_BP(107, 60, p1)

response = BP.create(smart.server)
if response:
    print(f"Created patient with id: {response['id']}")
else:
    print("Failed to create patient")"""
"""RR = [ob.resource for ob in RR.entry]
for i in RR:
    print(i.code.text)
    print(i.meta.lastUpdated.isostring)
    print(str(i.valueQuantity.value) + i.valueQuantity.unit)
HR = [ob.resource for ob in HR.entry]
for i in HR:
    print(i.code.text)
    print(i.meta.lastUpdated.isostring)
    print(str(i.valueQuantity.value) + i.valueQuantity.unit)
Height = [ob.resource for ob in Height.entry]
for i in Height:
    print(i.code.text)
    print(i.meta.lastUpdated.isostring)
    print(str(i.valueQuantity.value) + i.valueQuantity.unit)

BP = [ob.resource for ob in BP.entry]
for i in BP:
    print(i.meta.lastUpdated.isostring)
    print(i.code.text)
    for y in i.component:
        for o in y.code.coding:
            print(o.display)
        print(str(y.valueQuantity.value) + y.valueQuantity.unit)
BodyTem = [ob.resource for ob in BodyTem.entry]
for i in BodyTem:
    print(i.code.text)
    print(i.meta.lastUpdated.isostring)
    print(str(i.valueQuantity.value) + i.valueQuantity.unit)
weight = [ob.resource for ob in weight.entry]
for i in weight:
    #print(i.as_json())
    print(i.code.text)
    print(i.meta.lastUpdated.isostring)
    print(str(i.valueQuantity.value)+i.valueQuantity.unit)





"""
print("########")
"""settings = {
        'app_id': 'phr',
        'api_base': 'https://server.fire.ly'
    }
    smart = client.FHIRClient(settings=settings)

    patient = p.Patient()
    patient.id = '12895'
    #patient.meta = meta.Meta()
    #patient.meta.versionId = '1'
    name = hn.HumanName()
    name.given = ['Peter']
    name.family = 'Parker'
    patient.name = [name]
    patient.gender = 'male'
    patient.birthDate = fhirdate.FHIRDate('1999-01-01')
    #bundle = Bundle()
    #entry = BundleEntry()
    #entry.resource = patient
    #bundle.entry = [entry]
    bundle = Bundle()

    bundle.type = 'transaction'

    entry = BundleEntry()
    entry.resource = patient
    bundle.entry = [entry]
    #patient.create(smart.server)
    #response = smart.server.request('POST', 'Bundle', bundle.as_json())
    response = fhirabstractresource.FHIRAbstractResource.create(patient.as_json(), "Patient", smart.server)
    print(response.json())




    headers = {
        'Content-Type': 'application/fhir+json'
    }
    #url = "https://server.fire.ly" + "/Patient/" + patient.id
    #url = "https://server.fire.ly" + "/Bundle"
    #print(url)
    print(bundle.as_json())
    print(smart.server.base_uri)
    #response = requests.post(url='https://server.fire.ly', data=bundle.as_json(), headers=headers)
    print(response)
    if response.status_code >= 400:
        print('HTTP %d: %s' % (response.status_code, response.text))
        error = response.json().get('issue', [{}])[0].get('diagnostics', None)
        if error:
            print('Error##########: %s' % error)
    else:
        print('Resource created successfully!')
        print(response.json())
    #response = bundle.create(smart.server)
    #response = smart.resources('Bundle', bundle).post()
    #p2 = patient.update(smart.server)

    p1 = p.Patient.read('12892', smart.server)

    #ob1 = ob.Observation.read_from('/Observation?patient=12892&code=8867-4', smart.server)
    ob2 = ob.Observation.where({'patient': '12892', 'code': '8867-4'}).perform(smart.server)
    tests = [ob.resource for ob in ob2.entry]
    for test in tests:
        if test.code.text is not None:
            print(test.code.text)
        if test.valueQuantity is not None:
            print(str(test.valueQuantity.value) + test.valueQuantity.unit)

    print(test)
    print(ob2)

    print("########")
    print(smart.human_name(p1.name[0]))
    print(p1.birthDate.isostring)
    print("########")
    """
