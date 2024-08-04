from django.db import models




types = [('employee','employee'),('visitor','visitor')]
class Student(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, null=False, blank=False)
    last_name = models.CharField(max_length=100, null=False, blank=False)
    parent_first_name = models.CharField(max_length=100, null=False, blank=False)
    parent_last_name = models.CharField(max_length=100, null=False, blank=False)
    parent_phone = models.CharField(max_length=20, null=False, blank=False)
    present = models.BooleanField(default=False)
    image = models.ImageField() 
    updated = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return f'<Student {self.first_name} {self.last_name}>'


class LastFace(models.Model):
    last_face = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.last_face

