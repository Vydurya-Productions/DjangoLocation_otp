import requests
from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import random
import os
from django.conf import settings



# Twilio configuration
account_sid = 'your_twilio_account_sid'  # Replace with your Twilio SID
auth_token = 'your_twilio_auth_token'    # Replace with your Twilio Auth Token
twilio_phone = 'your_twilio_phone_number'  # Replace with your Twilio phone number
client = Client(account_sid, auth_token)
# Store OTP temporarily (in production, use Redis or database)
otp_storage = {}
# Create your views here.
def index(request):
    if request.method == 'GET' and 'pincode' in request.GET:
        pincode = request.GET.get('pincode')
        if pincode and len(pincode) == 6 and pincode.isdigit():
            api_url = f"https://api.postalpincode.in/pincode/{pincode}"
            try:
                response = requests.get(api_url)
                data = response.json()
                if data[0]['Status'] == 'Success':
                    post_office = data[0]['PostOffice'][0]  # Take first result
                    state = post_office['State']
                    district = post_office['District']
                    return JsonResponse({
                        'state': state,
                        'city': district,
                        'status': 'success'
                    })
                else:
                    return JsonResponse({'status': 'error', 'message': 'Invalid pincode'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'error', 'message': 'Invalid pincode format'})
    return render(request, 'index.html')


def mobile(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if not phone or not phone.isdigit() or len(phone) != 10:
            return render(request, 'request_otp.html', {
                'error': 'Please enter a valid 10-digit phone number'
            })
        
        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        otp_storage[phone] = otp
        
        # Send OTP via Twilio
        try:
            message = client.messages.create(
                body=f'Your OTP is: {otp}',
                from_=twilio_phone,
                to=f'+91{phone}'  # Assuming Indian numbers; adjust country code as needed
            )
            return redirect(f'/otp/?phone={phone}')
        except TwilioRestException as e:
            return render(request, 'request_otp.html', {
                'error': f'Failed to send OTP: {str(e)}'
            })
    
    return render(request, 'request_otp.html')

def otp(request):
    phone = request.GET.get('phone')
    if not phone or phone not in otp_storage:
        return redirect('mobile')
    
    if request.method == 'POST':
        submitted_otp = ''.join([
            request.POST.get(f'otp_{i}', '') for i in range(6)
        ])
        
        if submitted_otp == otp_storage.get(phone):
            del otp_storage[phone]  # Clear OTP after successful verification
            return JsonResponse({'status': 'success', 'message': 'OTP verified successfully'})
        else:
            return render(request, 'otp.html', {
                'phone': phone,
                'error': 'Invalid OTP. Please try again.'
            })
    
    return render(request, 'otp.html', {'phone': phone})
