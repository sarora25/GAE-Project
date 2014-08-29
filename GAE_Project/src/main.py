
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.blobstore import BlobInfo

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


DEFAULT_GUESTBOOK_NAME = 'default_name'
DEFAULT_FILELIST_NAME = 'default_filelist'



# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)

def filelist_key(filelist_name=DEFAULT_FILELIST_NAME):
    return db.Key('Filelist', filelist_name)	

class Greeting(ndb.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
	

class File(db.Model):
    """ All pictures that a User has uploaded """
    blob = blobstore.BlobReferenceProperty(required=True)
    user = db.UserProperty()	


class MainPage(webapp2.RequestHandler):

    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class Guestbook(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

class FileUpload(webapp2.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload_image')
        self.response.out.write('<html><body>')
        self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
        self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit" 
#name="submit" value="Submit"> </form></body></html>""")


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        user = users.get_current_user()
        blob_info = upload_files[0]
        file = File(blob = blob_info.key(), user = user)
        file.put()
        self.redirect('/list')
		
                
class ListHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        files = File.all().filter('user =', user)
        template_values = {
			'files': files,
            'user': user,
        }

        template = JINJA_ENVIRONMENT.get_template('list.html')
        self.response.write(template.render(template_values))	
	    
		
class ImageHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        files = []
        for file in File.all().filter('user =', user):
            filename = file.blob.filename
            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png") or filename.endswith(".gif"):
                files.append(file)
             
        template_values = {
            'files': files,
            'user': user,
        }

        template = JINJA_ENVIRONMENT.get_template('images.html')
        self.response.write(template.render(template_values))	
	   
		
class AudioHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        files = []
        for file in File.all().filter('user =', user):
            filename = file.blob.filename
            if filename.endswith(".wav") or filename.endswith(".aif") or filename.endswith(".au") or filename.endswith(".mp3"):
                files.append(file)
	
        template_values = {
            'files': files,
            'user': user,
        }		
			
        template = JINJA_ENVIRONMENT.get_template('audio.html')
        self.response.write(template.render(template_values))	

class VideoHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        files = []
        for file in File.all().filter('user =', user):
            filename = file.blob.filename
            if filename.endswith(".asf") or filename.endswith(".mpeg") or filename.endswith(".wmv") or filename.endswith(".MPG"):
                files.append(file)
	
        template_values = {
            'files': files,
            'user': user,
        }		
			
        template = JINJA_ENVIRONMENT.get_template('video.html')
        self.response.write(template.render(template_values))		
			

class ViewHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self):
		user = users.get_current_user()
		upload_key_str = self.request.params.get('key')
		upload = None
		if upload_key_str:
			upload = db.get(upload_key_str)
		
		if (not user or not upload):
			self.error(404)
			return
			
		self.send_blob(upload.blob)

class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self):
		user = users.get_current_user()
		upload_key_str = self.request.params.get('key')
		upload = None
		if upload_key_str:
			upload = db.get(upload_key_str)
		
		if (not user or not upload):
			self.error(404)
			return
			
		self.send_blob(upload.blob, save_as =True)		
		
class DeleteHandler(webapp2.RequestHandler):
    def get(self):        
        user = users.get_current_user()
        delete_key_str = self.request.params.get('key')
        delete = None
        if delete_key_str:
            delete = db.get(delete_key_str)
            db.delete(delete)
			
        if (not user or not delete):
            self.error(404)
            return
			
        self.redirect('/list')
		
application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
	('/upload', FileUpload),
    ('/upload_image', UploadHandler),
    ('/list', ListHandler),
    ('/images', ImageHandler),
    ('/audio', AudioHandler),
    ('/video', VideoHandler),
	('/view',ViewHandler),
	('/download', DownloadHandler),
    ('/delete', DeleteHandler)
], debug=True)
