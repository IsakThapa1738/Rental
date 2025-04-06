from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
# from .forms import SignUpForm
from django.template import loader
from user.models import *
from datetime import *
import re
import os
from django.contrib import messages
from django.db.models import Q


def index(request):
    template = loader.get_template('index.html')
    context = {}

    room = Room.objects.all()
    if bool(room):
        n = len(room)
        nslide = n // 3 + (n % 3 > 0)
        rooms = [room, range(1, nslide), n]
        context.update({'room': rooms})
    house = House.objects.all()
    if bool(house):
        n = len(house)
        nslide = n // 3 + (n % 3 > 0)
        houses = [house, range(1, nslide), n]
        context.update({'house': houses})
    return HttpResponse(template.render(context, request))


def home(request):
    template = loader.get_template('home.html')
    context = {}
    context.update({'result': ''})
    context.update({'msg': 'Search your query'})
    return HttpResponse(template.render(context, request))


def search(request):
    template = loader.get_template('home.html')
    context = {}
    if request.method == 'GET':
        typ = request.GET['type']
        q = request.GET['q']
        context.update({'type': typ})
        context.update({'q':q})
        results={}
        if typ == 'House' and (bool(House.objects.filter(location=q)) or bool(House.objects.filter(city=q))):
            results = House.objects.filter(location=q)
            results = results | House.objects.filter(city=q)
        elif typ == 'Apartment'  and (bool(Room.objects.filter(location=q)) or bool(House.objects.filter(city=q))):
            results = Room.objects.filter(location=q)
            results = results | Room.objects.filter(city=q)

        
        if bool(results)== False:
            print("messages")
            messages.success(request, "No matching results for your query..")

        result = [results, len(results)]
        context.update({'result': result})

    return HttpResponse(template.render(context, request))


def about(request):
    template = loader.get_template('about.html')
    context = {}

    room = Room.objects.all()
    if bool(room):
        context.update({'room': room})
    house = House.objects.all()
    if bool(house):
        context.update({'house': house})
    return HttpResponse(template.render(context, request))


def contact(request):
    template = loader.get_template('contact.html')
    context = {}

    if request.method == 'POST':
        subject = request.POST['subject']
        email = request.POST['email']
        body = request.POST['body']
        regex = r'^[a-z0-9]+[\\._]?[a-z0-9]+[@]\\w+[.]\\w{2,3}$'
        if re.search(regex, email):
            pass
        else:
            template = loader.get_template('register.html')
            context.update({'msg': 'invalid email'})
            return HttpResponse(template.render(context, request))
        contact = Contact(subject=subject, email=email, body=body)
        contact.save()
        context.update({'msg': 'msg send to admin'})
        return HttpResponse(template.render(context, request))
    else:
        context.update({'msg': ''})
        return HttpResponse(template.render(context, request))


def descr(request):
    template = loader.get_template('desc.html')
    context = {}
    if request.method == 'GET':
        id = request.GET['id']
        try:
            room = Room.objects.get(room_id=id)
            context.update({'val': room})
            context.update({'type': 'Apartment'})
            user = User.objects.get(email=room.user_email)
        except:
            house = House.objects.get(house_id=id)
            context.update({'val': house})
            context.update({'type': 'House'})
            user = User.objects.get(email=house.user_email)
    context.update({'user': user})
    return HttpResponse(template.render(context, request))


# def loginpage(request):
#     return render(request, 'login.html', {'msg': ''})


def register(request):
    if request.method == 'GET':
        return render(request, 'register.html', {'msg': ''})

    name = request.POST['name']
    email = request.POST['email']
    location = request.POST['location']
    city = request.POST['city']
    state = request.POST['state']
    phone = request.POST['phone']
    pas = request.POST['pass']
    cpas = request.POST['cpass']
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if re.search(regex, email):
        pass
    else:
        template = loader.get_template('register.html')
        context = {'msg': 'invalid email'}
        return HttpResponse(template.render(context, request))

    if len(str(phone)) != 10:
        template = loader.get_template('register.html')
        context = {'msg': 'invalid phone number'}
        return HttpResponse(template.render(context, request))

    if pas != cpas:
        template = loader.get_template('register.html')
        context = {'msg': 'password did not matched'}
        return HttpResponse(template.render(context, request))
    already = User.objects.filter(email=email)
    if bool(already):
        template = loader.get_template('register.html')
        context = {'msg': 'email already registered'}
        return HttpResponse(template.render(context, request))
    
    user = User.objects.create_user(
        name=name,
        email=email,
        location=location,
        city=city,
        state=state,
        number=phone,
        password=pas,
        )
    user.save()
    login(request, user)
    return redirect("/profile/")

@login_required(login_url='/login')
def profile(request):
    report = Contact.objects.filter(email=request.user.email)
    room = Room.objects.filter(user_email=request.user)
    house = House.objects.filter(user_email=request.user)
    roomcnt = room.count()
    housecnt = house.count()
    reportcnt = report.count()
    rooms = []
    houses = []
    if bool(room):
        n = len(room)
        nslide = n // 3 + (n % 3 > 0)
        rooms = [room, range(1, nslide), n]
    if bool(house):
        n = len(house)
        nslide = n // 3 + (n % 3 > 0)
        houses = [house, range(1, nslide), n]
        
    context = {
        'user': request.user,
        'report': report,
        'reportno': reportcnt,
        'roomno': roomcnt,
        'houseno': housecnt
    }
    context.update({'room': rooms})
    context.update({'house': houses})    
    return render(request, 'profile.html', context=context)


@login_required(login_url='/login')
def post(request):
    if request.method == "GET":
        context = {'user': request.user}
        return render(request, 'post.html', context)
    elif request.method == "POST":
        try:
            dimention = request.POST['dimention']
            location = request.POST['location'].lower()
            city = request.POST['city'].lower()
            state = request.POST['state'].lower()
            cost = request.POST['cost']
            hall = request.POST['hall'].lower()
            kitchen = request.POST['kitchen'].lower()
            balcany = request.POST['balcany'].lower()
            bedroom = request.POST['bedroom']
            ac = request.POST['AC'].lower()
            desc = request.POST['desc'].upper()
            img = request.FILES['img']
            user_obj = User.objects.filter(email=request.user.email)[0]
            bedroom = int(bedroom)
            cost = int(cost)
            room = Room.objects.create(
                user_email=user_obj,
                dimention=dimention,
                location=location,
                city=city,
                state=state,
                cost=cost,
                hall=hall,
                kitchen=kitchen,
                balcany=balcany,
                bedrooms=bedroom,
                AC=ac,
                desc=desc,
                img=img,
            )
            messages.success(request, 'submitted successfully..')
            return render(request, 'post.html')
        except Exception as e:
            return HttpResponse(status=500)


@login_required(login_url='/login')
def posth(request):
    if request.method == "GET":
        context = {'user': request.user}
        return render(request, 'posth.html', context)
    else:
        try:
            area = request.POST['area']
            floor = request.POST['floor']
            location = request.POST['location'].lower()
            city = request.POST['city'].lower()
            state = request.POST['state'].lower()
            cost = request.POST['cost']
            hall = request.POST['hall'].lower()
            kitchen = request.POST['kitchen'].lower()
            balcany = request.POST['balcany'].lower()
            bedroom = request.POST['bedroom']
            ac = request.POST['AC'].lower()
            desc = request.POST['desc'].upper()
            img = request.FILES['img']
            bedroom = int(bedroom)
            cost = int(cost)
            user_obj = User.objects.filter(email=request.user.email)[0]
            house = House.objects.create(
                user_email=user_obj,
                location=location,
                city=city,
                state=state,
                cost=cost,
                hall=hall,
                kitchen=kitchen,
                balcany=balcany,
                bedrooms=bedroom,
                area=area,
                floor=floor,
                AC=ac,
                desc=desc,
                img=img,
            )
            messages.success(request, 'submitted successfully..')
            return render(request, 'posth.html')
        except Exception as e:
            print()
            print(e)
            print()
            return HttpResponse(status=500)

def deleter(request):
    if request.method == 'GET':
        id = request.GET['id']
        instance = Room.objects.get(room_id=id)
        instance.delete()
        messages.success(request, 'Appartment details deleted successfully..')
    return redirect('/profile')


def deleteh(request):
    if request.method == 'GET':
        id = request.GET['id']
        instance = House.objects.get(house_id=id)
        instance.delete()
        messages.success(request, 'House details deleted successfully..')
    return redirect('/profile')


def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    email = request.POST['email']
    password = request.POST['password']
    user = authenticate(request, email=email, password=password)

    if user is not None:
        login(request, user)
        return redirect("/")
    else:
        template = loader.get_template('login.html')
        context = {
            'msg': 'Email and password, you entered, did not matched.'
        }
        return HttpResponse(template.render(context, request))
    

from django.shortcuts import render, redirect, get_object_or_404
from user.models import Booking, Room, House
from user.forms import BookingForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def create_booking(request, property_type, property_id):
    # Get the property
    if property_type == 'room':
        property_obj = get_object_or_404(Room, pk=property_id)
        property_filter = Q(room=property_obj)
    elif property_type == 'house':
        property_obj = get_object_or_404(House, pk=property_id)
        property_filter = Q(house=property_obj)
    else:
        messages.error(request, "Invalid property type")
        return redirect('index')

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.property_type = property_type
            
            # Assign the correct property based on type
            if property_type == 'room':
                booking.room = property_obj
            else:
                booking.house = property_obj
            
            # Check for date conflicts using the correct filter
            conflicting_bookings = Booking.objects.filter(
                property_filter,
                check_in__lt=booking.check_out,
                check_out__gt=booking.check_in
            ).exclude(status__in=['rejected', 'cancelled'])
            
            if conflicting_bookings.exists():
                messages.error(request, "The property is not available for the selected dates")
            else:
                booking.save()
                messages.success(request, "Booking request sent to property owner")
                return redirect('booking_history')
    else:
        form = BookingForm()

    return render(request, 'booking/create.html', {
        'property': property_obj,
        'property_type': property_type,
        'form': form
    })

@login_required
def booking_history(request):
    """Show only bookings made by the current user"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'booking/history.html', {
        'bookings': bookings,
        'is_owner': False  # Indicates this is the guest's view
    })

@login_required
def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Verify permission
    if not booking.can_manage(request.user):
        messages.error(request, "You don't have permission to manage this booking")
        return redirect('booking_history')
    
    # Validate status
    if status not in ['approved', 'rejected']:
        messages.error(request, "Invalid status")
        return redirect('booking_history')
    
    # Update status
    booking.status = status
    booking.save()
    messages.success(request, f"Booking #{booking.id} has been {status}")
    
    return redirect('booking_history')



@login_required
def received_bookings(request):
    """Show only bookings for the current user's properties"""
    bookings = Booking.objects.filter(
        Q(room__user_email=request.user) | Q(house__user_email=request.user)
    ).order_by('-booking_date')
    return render(request, 'booking/received.html', {
        'bookings': bookings,
        'is_owner': True  # Indicates this is the owner's view
    })

@login_required
def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Verify the current user owns the property
    if not (booking.room and booking.room.user_email == request.user) and \
       not (booking.house and booking.house.user_email == request.user):
        messages.error(request, "You don't have permission to manage this booking")
        return redirect('received_bookings')
    
    if status in ['approved', 'rejected']:
        booking.status = status
        booking.save()
        messages.success(request, f"Booking has been {status}")
    
    return redirect('received_bookings')