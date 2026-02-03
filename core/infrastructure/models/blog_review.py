from django.db import models
from django.contrib.auth import get_user_model
from .blog_post import BlogPost


class BlogReview(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = self.first_name or (self.user.username if self.user else "Guest")
        return f"{name} - {self.post.title}"