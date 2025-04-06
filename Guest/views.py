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
    # Use render shortcut instead of loader
    # template = loader.get_template('home.html')
    context = {}

    if request.method == 'GET':
        # --- Get all potential filter parameters ---
        typ = request.GET.get('type', '') # House or Apartment
        q = request.GET.get('q', '').strip() # Location query (city, location, state)
        keywords = request.GET.get('keywords', '').strip()
        min_cost = request.GET.get('min_cost', '')
        max_cost = request.GET.get('max_cost', '')
        bedrooms = request.GET.get('bedrooms', '')
        # Amenities - treat presence of param as 'yes' if using checkboxes without value="yes"
        # Or check value if using value="yes" e.g., request.GET.get('ac') == 'yes'
        ac = request.GET.get('ac', '') # Expecting 'yes' if checked
        kitchen = request.GET.get('kitchen', '') # Expecting 'yes'
        hall = request.GET.get('hall', '') # Expecting 'yes'
        balcony = request.GET.get('balcony', '') # Expecting 'yes' (Note: model field is 'balcany')
        sort_by = request.GET.get('sort_by', '') # e.g., 'price_asc', 'price_desc', 'date_new'

        # --- Pass parameters back to context for form repopulation ---
        context.update({
            'type': typ,
            'q': q,
            'keywords': keywords,
            'min_cost': min_cost,
            'max_cost': max_cost,
            'bedrooms': bedrooms,
            'ac': ac,
            'kitchen': kitchen,
            'hall': hall,
            'balcony': balcony,
            'sort_by': sort_by,
        })

        results_queryset = None

        # --- Apply filters based on type ---
        if typ == 'House':
            results_queryset = House.objects.all()
            model_name = "House"

            # Location Filter (City, Location, State) - Case Insensitive Contains
            if q:
                results_queryset = results_queryset.filter(
                    Q(location__icontains=q) |
                    Q(city__icontains=q) |
                    Q(state__icontains=q)
                )

            # Keyword Filter (Description) - Case Insensitive Contains
            if keywords:
                results_queryset = results_queryset.filter(desc__icontains=keywords)

            # Price Filter
            try:
                if min_cost:
                    results_queryset = results_queryset.filter(cost__gte=int(min_cost))
                if max_cost:
                    results_queryset = results_queryset.filter(cost__lte=int(max_cost))
            except ValueError:
                messages.error(request, "Invalid price value entered.")
                # Decide if you want to stop or continue without price filter
                # results_queryset = House.objects.none() # Option: show no results on bad input

            # Bedroom Filter (Minimum number)
            try:
                if bedrooms:
                    results_queryset = results_queryset.filter(bedrooms__gte=int(bedrooms))
            except ValueError:
                 messages.error(request, "Invalid bedroom value entered.")
                 # results_queryset = House.objects.none()

            # Amenity Filters (Case Insensitive Exact Match for 'yes'/'no' fields)
            if ac == 'yes':
                 # Assuming your model stores 'yes' or 'no'. Adjust if different.
                results_queryset = results_queryset.filter(AC__iexact='yes')
            if kitchen == 'yes':
                 # Assuming your model stores an integer for kitchens in House? If so:
                 # results_queryset = results_queryset.filter(kitchen__gte=1)
                 # If it's CharField 'yes'/'no' like Room:
                 messages.warning(request, "Kitchen filter might behave unexpectedly for Houses based on model definition (IntegerField).")
                 # Adjust logic based on how you store House kitchen info. Let's assume CharField for now:
                 results_queryset = results_queryset.filter(kitchen__iexact='yes') # MODIFY IF NEEDED
            if hall == 'yes':
                results_queryset = results_queryset.filter(hall__iexact='yes')
            if balcony == 'yes':
                # Use the actual field name from your model
                results_queryset = results_queryset.filter(balcany__iexact='yes') # Field name is 'balcany'

        elif typ == 'Apartment': # Corresponds to Room model
            results_queryset = Room.objects.all()
            model_name = "Apartment"

            # Location Filter (City, Location, State)
            if q:
                results_queryset = results_queryset.filter(
                    Q(location__icontains=q) |
                    Q(city__icontains=q) |
                    Q(state__icontains=q)
                )

            # Keyword Filter (Description)
            if keywords:
                results_queryset = results_queryset.filter(desc__icontains=keywords)

            # Price Filter
            try:
                if min_cost:
                    results_queryset = results_queryset.filter(cost__gte=int(min_cost))
                if max_cost:
                    results_queryset = results_queryset.filter(cost__lte=int(max_cost))
            except ValueError:
                messages.error(request, "Invalid price value entered.")
                # results_queryset = Room.objects.none()

            # Bedroom Filter
            try:
                if bedrooms:
                    results_queryset = results_queryset.filter(bedrooms__gte=int(bedrooms))
            except ValueError:
                 messages.error(request, "Invalid bedroom value entered.")
                 # results_queryset = Room.objects.none()

            # Amenity Filters
            if ac == 'yes':
                results_queryset = results_queryset.filter(AC__iexact='yes')
            if kitchen == 'yes':
                results_queryset = results_queryset.filter(kitchen__iexact='yes')
            if hall == 'yes':
                results_queryset = results_queryset.filter(hall__iexact='yes')
            if balcony == 'yes':
                # Use the actual field name from your model
                results_queryset = results_queryset.filter(balcany__iexact='yes') # Field name is 'balcany'

        else:
             # No valid type selected, or initial search page load without type
             if typ: # Only show error if a type was actually submitted
                 messages.error(request, "Please select a valid property type (House or Apartment).")
             results_queryset = None # Show no results unless a type is selected


        # --- Apply Sorting ---
        if results_queryset is not None:
            if sort_by == 'price_asc':
                results_queryset = results_queryset.order_by('cost')
            elif sort_by == 'price_desc':
                results_queryset = results_queryset.order_by('-cost')
            elif sort_by == 'date_new':
                results_queryset = results_queryset.order_by('-date')
            else:
                 # Default sort (maybe newest first?)
                 results_queryset = results_queryset.order_by('-date') # Example default

        # --- Prepare results for template ---
        final_results = []
        if results_queryset is not None:
            final_results = list(results_queryset) # Evaluate queryset
            if not final_results and (q or keywords or min_cost or max_cost or bedrooms or ac or kitchen or hall or balcony):
                # Only show 'no results' if filters were actually applied
                 messages.info(request, f"No matching {model_name}s found for your criteria.")
        elif typ: # If a type was selected but no results_queryset was created (e.g. invalid type)
            pass # Error message already handled


        result_list = [final_results, len(final_results)]
        context.update({'result': result_list})

    # If not GET, or initial load before search
    else:
         context.update({'result': [[], 0]}) # Empty result list
         # Optional: Add a default message for the initial page load if desired
         # context.update({'msg': 'Search for properties using the filters.'})


    # Use the render shortcut
    return render(request, 'home.html', context)



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