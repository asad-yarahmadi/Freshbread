import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.html import strip_tags


class BlogPost(models.Model):
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="blog_posts")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField()
    seo_keywords = models.CharField(max_length=300, blank=True)
    tags = models.CharField(max_length=300, blank=True)
    cover_list = models.ImageField(upload_to="blog/list/")
    cover_single = models.ImageField(upload_to="blog/single/")
    is_published = models.BooleanField(default=True)
    likes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            if not base:
                from django.utils.crypto import get_random_string
                base = f"post-{get_random_string(8)}"
            candidate = base
            i = 1
            while BlogPost.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{i}"
                i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def tag_list(self):
        return [t.strip() for t in self.tags.split() if t.strip()]

    @property
    def excerpt(self):
        text = strip_tags(self.content or "")
        parts = [p.strip() for p in text.split('.') if p.strip()]
        preview = '. '.join(parts[:6])
        if preview and not preview.endswith('.'):
            preview += '.'
        return preview

    def __str__(self):
        return self.title


class UserBlogView(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)
    viewed_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='user_views')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='blog_views')
    reading_duration_seconds = models.PositiveIntegerField(default=0)
    reached_end = models.BooleanField(default=False)
    is_valid_view = models.BooleanField(default=False)

    class Meta:
        db_table = 'infrastructure_userblogview'
        ordering = ['-viewed_at']
        unique_together = [('user', 'post')]

    def __str__(self):
        return f"{self.user.username} - {self.post.title}"