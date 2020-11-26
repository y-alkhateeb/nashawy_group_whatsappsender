from django.db import models


class DrPhoneNumber(models.Model):
    phone_number = models.CharField(primary_key=True, max_length=15)
    number_of_message_sent = models.IntegerField(default=0)
    have_whatsapp = models.BooleanField()
    note = models.CharField(max_length=200)

    def __str__(self):
        return self.phone_number + " - " + str(self.number_of_message_sent) + " messages has been sent." + self.note


class SystemSetting(models.Model):
    last_index_sent = models.IntegerField(default=0)
    type_sent = models.IntegerField(default=0)
    last_phone_number = models.CharField(max_length=15, default="0")
    last_date_of_sent = models.DateTimeField()

    def __str__(self):
        return str(self.last_index_sent) + " - " + self.last_phone_number + " - " + str(self.last_date_of_sent)


class SystemReporting(models.Model):
    total_success_sent = models.IntegerField(default=0)
    total_failure_sent = models.IntegerField(default=0)
    date_of_reporting = models.DateTimeField()

    def __str__(self):
        return str(self.total_success_sent) + " - " + str(self.total_failure_sent) + " - " + str(self.date_of_reporting)
