from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField

class Content(models.Model):
    content = RichTextUploadingField()