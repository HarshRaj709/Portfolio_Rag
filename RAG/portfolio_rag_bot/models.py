from django.db import models
from pgvector.django import VectorField


class Document(models.Model):
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    embedding = VectorField(dimensions=384)

    def __str__(self):
        return self.content[:50]
