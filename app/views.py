
### 2. app/views.py
from django.shortcuts import render
from app.models import MorningBrief

def digest_view(request, username):
    data = MorningBrief.objects.filter(owner=username).order_by('-id')
    return render(request, 'kpi/digest_template.html', {'data': data, 'username': username})

