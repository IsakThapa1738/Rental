from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import UserManager


# # Create your models here.

class UserManager(BaseUserManager):

    def create_user(self, email, name, location, city, state, number, password=None, is_admin=False, is_staff=False, is_active=True):
        if not email:
            raise ValueError('User must have an email')
        if not password:
            raise ValueError('User must have a password')
        if not name:
            raise ValueError('User must have a full name')

        user = self.model(email=self.normalize_email(email))
        user.name = name
        user.set_password(password)
        user.location = location
        user.city = city
        user.state = state
        user.number = number
        user.admin = is_admin
        user.staff = is_staff
        user.active = is_active
        user.save(using=self._db)
        return user

    def create_superuser(self,email, name, number, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email')
        if not password:
            raise ValueError('User must have a password')
        if not name:
            raise ValueError('User must have a full name')

        user = self.model(email=self.normalize_email(email))
        user.name = name
        user.number = number
        user.set_password(password)
        user.admin = True
        user.staff = True
        user.active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):

    email = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=25)
    password = models.CharField(max_length=100)
    location = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    number = models.IntegerField()
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)  # a admin user; non super-user
    admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'number']
    objects = UserManager()

    def __str__(self):
        return self.email

    @staticmethod
    def has_perm(perm, obj=None):
         # "Does the user have a specific permission?"
         # Simplest possible answer: Yes, always
        return True

    @staticmethod
    def has_module_perms(app_label):
         # "Does the user have permissions to view the app `app_label`?"
         # Simplest possible answer: Yes, always
         return True

    @property
    def is_staff(self):

        # "Is the user a member of staff?"

        return self.staff

    @property
    def is_admin(self):

        # "Is the user a admin member?"

        return self.admin

    @property
    def is_active(self):

        # "Is the user active?"

        return self.active


class Room(models.Model):

    room_id = models.AutoField(primary_key=True)
    user_email = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    dimention = models.CharField(max_length=100)
    location = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    cost = models.IntegerField()
    bedrooms = models.IntegerField()
    kitchen = models.CharField(max_length=3)
    hall = models.CharField(max_length=3)
    balcany = models.CharField(max_length=3)
    desc = models.CharField(max_length=200)
    AC = models.CharField(max_length=3)
    img = models.ImageField(upload_to='room_id/', height_field=None,
                            width_field=None, max_length=100)
    date = models.DateField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return str(self.room_id)


class House(models.Model):

    house_id = models.AutoField(primary_key=True)
    user_email = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    area = models.IntegerField()
    floor = models.IntegerField()
    location = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    cost = models.IntegerField()
    bedrooms = models.IntegerField()
    kitchen = models.IntegerField()
    hall = models.CharField(max_length=3)
    balcany = models.CharField(max_length=3)
    desc = models.CharField(max_length=200)
    AC = models.CharField(max_length=3)
    img = models.ImageField(upload_to='house_id/', height_field=None,
                            width_field=None, max_length=100)
    date = models.DateField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return str(self.house_id)


class Contact(models.Model):

    contact_id = models.AutoField(primary_key=True)
    subject = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    body = models.CharField(max_length=500)

    def __str__(self):
        return str(self.contact_id)
    


from django.db import models
from django.utils import timezone

# user/models.py - Update your Booking model

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class Booking(models.Model):

    notes = models.TextField(blank=True, null=True)

    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled by User'),
    )

    PROPERTY_TYPES = (
        ('room', 'Room'),
        ('house', 'House'),
    )

    # Booking information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made')
    property_type = models.CharField(max_length=10, choices=PROPERTY_TYPES)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name='bookings')
    house = models.ForeignKey(House, on_delete=models.CASCADE, null=True, blank=True, related_name='bookings')
    
    # Dates
    check_in = models.DateField()
    check_out = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    
    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.get_property_type_display()}"
    
    def get_property(self):
        return self.room if self.property_type == 'room' else self.house
    
    def get_owner(self):
        return self.get_property().user_email
    
    def can_manage(self, user):
        """Check if user can approve/reject this booking"""
        return user == self.get_owner()
    
    def get_duration(self):
        return (self.check_out - self.check_in).days

    def get_total_price(self):
        if self.property_type == 'room':
            return self.room.cost * self.get_duration()
        return self.house.cost * self.get_duration()

    def get_property_owner(self):
        if self.property_type == 'room':
            return self.room.user_email
        return self.house.user_email
    
    class Meta:
        ordering = ['-booking_date']