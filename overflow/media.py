from .models import Account, Media, QuestionMedia, CommentMedia
from django.utils.crypto import get_random_string
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import ftplib
from django.core.files.storage import default_storage
from django.core.files.base import File 

@csrf_exempt
def addMedia(request):
    data = {}
    if request.method == 'POST':
        if 'username' in request.session:
            try:
                account = Account.objects.get(username=request.session['username']) 
                file_id = get_random_string(length=12)
                binary = request.FILES['content'] 
                file_name_type = binary.name.split(".")
                file_type = file_name_type[1] 
                path = default_storage.save('/var/www/overflow/OverflowClone/static/'+file_id+'.'+file_type, File(binary.file)) 
                new_file = open(path, 'rb')  
        # login to ftp serer
                server = ftplib.FTP('152.44.32.64')
                server.login('user1', 'omarsyed123')
        # upload the file
                server.storbinary("STOR "+binary.name, new_file, 1024) 
                server.close() 
                new_file.close() 
        # delete the file in memory 
                default_storage.delete(path) 
                savefile = Media.objects.create(file_id=file_id, file_name=binary.name, uploader=account) 
                return JsonResponse({'status':'OK', 'id':file_id, 'error':''})
            except Exception as e:
                print(e) 
                return JsonResponse({'status':'error', 'id':'', 'error':'error uploading file'}, status=405)
        else:
            data['status'] = 'error'
            data['id'] = ''
            data['error'] = 'Not logged in'
            return JsonResponse(data, status=401) 

@csrf_exempt
def getMedia(request, media_id):
    if request.method == 'GET':
        if 'username' in request.session:
            account = Account.objects.get(username=request.session['username']) 
            metadata = Media.objects.filter(file_id = media_id, uploader=account)
            if not metadata:
                return HttpResponse(status=404)
            #print(metadata.file_name) 
            #print(file_type)
            try:
            #print('file header: ' + response_header) 
                server = ftplib.FTP('152.44.32.64')
                server.login('user1', 'omarsyed123')
                path = '/var/www/overflow/OverflowClone/static/'+metadata.file_name
            #print('line 70')
                new_file = open(path, mode='wb')
            #print('line 72')
                server.retrbinary('RETR '+ metadata.file_name, new_file.write) 
            #print('line 74')
                new_file.close() 
            #print('line 76') 
                new_file = open(path, mode='rb') 
            #print('line 78') 
                content = new_file.read() 
                new_file.close() 
            #print('line 80') 
                default_storage.delete(path)
            #print('line 82')
            #print('Content-type: '+ response_type+response_header)
                server.close() 
                response = HttpResponse(content)
                return response
            except Exception as e:
                print(e) 
                return HttpResponse(status=401)
        else:
            return HttpResponse(status=401) 

