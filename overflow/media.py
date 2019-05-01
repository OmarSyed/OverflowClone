from .models import Media, QuestionMedia, CommentMedia
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
                savefile = Media.objects.create(file_id=file_id, file_name=binary.name) 
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
            metadata = Media.objects.get(file_id = media_id)
            file_type = metadata.file_name.split('.')[1]
            #print(metadata.file_name) 
            #print(file_type)
            response_type = None
            if file_type == 'jpg' or file_type == 'jpeg' or file_type == 'png':
                response_type = 'image/'
            else:
                response_type = 'video/'
        #print('response type: ' + response_type)
            response_header = None
            if file_type == 'mp4':
                response_header = 'mp4'
            elif file_type == 'mov':
                response_header = 'quicktime'
            elif file_type == 'avi':
                response_header = 'x-msvideo'
            elif file_type == 'wmv':
                response_header = 'x-ms-wmv'
            elif file_type == 'flv':
                response_header = 'x-flv' 
            elif file_type == '3gp':
                response_header = '3gpp' 
            else:
                response_header = file_type
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
                response = HttpResponse(content, content_type=response_type+response_header)
                return response
            except Exception as e:
                print(e) 
                return HttpResponse(status=401)
        else:
            return HttpResponse(status=401) 

