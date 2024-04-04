from django.db import models
import datetime
from django.utils import timezone


class User(models.Model):
    #ID = (('Doctor', "Doctor"), ('Patient', "Patient"))
    u_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=256)
    c_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    def set_list(self, info, element):
        #add new patient
        if info == "pid":
            if self.pid_data != "":
                self.pid_data = self.pid_data + "," + element
            else:
                self.pid_data = element
    def get_list(self, info):
        if info == "pid":
            if self.pid_data != "":
                return self.pid_data.split(",")
            else:
                None
    class Meta:
        ordering = ["-c_time"]
        verbose_name = "Users"


class Patient(models.Model):
    p_id = models.AutoField(primary_key=True)
    cid = models.ForeignKey(to='User', to_field="u_id", related_name="patient", on_delete=models.CASCADE, default=None)
    add_time = models.CharField(max_length=30, null=True)
    name = models.CharField(max_length=200)
    cc_time = models.DateTimeField(auto_now=True)
    phoneNumber = models.CharField(max_length=200, default="")
    NHINumber = models.CharField(max_length=200, default="")
    organization_id = models.TextField(max_length=200, default="")

    def __str__(self):
        return self.name



    class Meta:
        ordering = ["-cc_time"]
        verbose_name = "Patients"

class ActionLog(models.Model):
    user = models.ForeignKey(to='User', to_field="u_id", on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} - {self.user.u_id if self.user else 'None'} - {self.user if self.user else 'Anonymous'} - {self.action}"
    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Action Log"


#class HealthRecord(models.Model):

# Create your models here.
