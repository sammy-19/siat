from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, ContactInfo
from admin_panel.models import AboutSection
from django.core.mail import send_mail
from django.conf import settings
from .forms import EnrollmentForm, ContactForm


def home(request):
    short_courses = Course.objects.filter(category='short_certificate')[:3]  # Top 3 short certs
    diploma_courses = Course.objects.filter(category='diploma')[:3]  # Top 3 diplomas
    context = {
        'short_courses': short_courses,
        'diploma_courses': diploma_courses,
        'site_name': 'Sunrise Institute of Applied Sciences and Technology',
        'site_description': 'SUNRISE INSTITUTE OF APPLIED SCIENCES AND TECHNOLOGY and its board value and embrace diversity, equality and inclusion as fundamental to our mission to educate students for career success within a context of global citizenship and social justice. We recognize that historical and persistent inequalities and barriers to equitable participation exist and are well documented in society and within the college.',
        'keywords': 'online courses, applied sciences, technology education, SIAT Zambia, sunrise institute, short certificate courses, diploma programs, diversity equity inclusion education, global citizenship, social justice training',
        'meta_description': 'Discover short certificate and diploma courses at SIAT for career advancement in business, IT, and more. Embrace diversity and excellence in education.',
    }
    return render(request, 'home.html', context)

def about(request):
    sections = AboutSection.objects.all()
    context = {
        'sections': sections,
        'site_description': 'Learn about our vision, mission, and commitment to quality education at SIAT.',
        'keywords': 'SIAT vision, mission, applied sciences institute',
    }
    return render(request, 'about.html', context)

def courses(request):
    short_courses = Course.objects.filter(category='short_certificate')
    diploma_courses = Course.objects.filter(category='diploma')
    context = {
        'short_courses': short_courses,
        'diploma_courses': diploma_courses,
        'meta_description': 'Explore Short Certificate and Diploma courses at SIAT to boost your career in business, IT, and more.',
        'meta_keywords': 'short certificate courses, diploma courses, online learning SIAT, sunrise institute, sunrise-institute.net, education courses',
    }
    return render(request, 'courses.html', context)

def enroll(request, course_slug=None):
    course = None
    if course_slug:
        course = get_object_or_404(Course, slug=course_slug)
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            application = form.save(commit=False)
            if course:
                application.course = course
            application.save()
            # Send email with all details
            subject = f"New Enrollment: {application.course.title}"
            message = (
                f"Applicant: {application.full_name}\nEmail: {application.email}\nPhone: {application.phone}\n"
                f"Gender: {application.get_gender_display()}\nDOB: {application.date_of_birth}\n"
                f"Highest Qual: {application.highest_qualification}\nEdu Background: {application.education_background}\n"
                f"Next of Kin: {application.next_of_kin_name} ({application.next_of_kin_relationship}, {application.next_of_kin_contact})\n"
                f"ID Type: {application.get_identity_type_display()}\nID Number: {application.identity_number}\n"
                f"Disability: {application.get_disability_status_display()}\nDetails: {application.disability_details}\n"
                f"ID Doc: {application.identity_document.url if application.identity_document else 'None'}\n"
                f"Results: {application.secondary_results.url if application.secondary_results else 'None'}\n"
                f"Message: {application.message}"
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
            return redirect('thank_you')
    else:
        initial = {'course': course} if course else {}
        form = EnrollmentForm(initial=initial)
    context = {
        'form': form,
        'course': course,
        'meta_description': 'Apply online to SIAT courses. Secure form for personal, education, and document submission.',
        'meta_keywords': 'SIAT enrollment form, online college application, diploma registration',
    }
    return render(request, 'enroll.html', context)

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    return render(request, 'course_detail.html', {'course': course})

def thank_you(request):
    return render(request, 'thank_you.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            message = form.save()  # Save to Neon DB
            # Send email
            email_subject = f"New Contact: {message.subject}"
            email_message = f"From: {message.name} ({message.email})\nMessage: {message.message}"
            send_mail(email_subject, email_message, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
            return redirect('contact')  # Or thank you page
    else:
        form = ContactForm()
    
    info = {
        'phone': '+260 076 251632',
        'email': 'sunriseinstituteofapplied21@gmail.com',
        'address': 'Sunrise Institute, Monze, Zambia',  # Placeholder from PDF/phone
    }
    context = {
        'info': info,
        'form': form,
        'meta_description': 'Contact Sunrise Institute of Applied Sciences and Technology for inquiries on online courses, admissions, and more. Reach us via phone, email, or visit our address.',
        'meta_keywords': 'SIAT contact, sunrise institute Zambia, applied sciences inquiries, technology education support, diversity equity education contact',
    }
    return render(request, 'contact.html', context)