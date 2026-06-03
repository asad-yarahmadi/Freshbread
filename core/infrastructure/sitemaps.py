from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from core.infrastructure.models import Product, BlogPost


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'index',
            'menu',
            'about',
            'contact',
            'gallery',
            'prpo',
            'tms',
            'stuff',
            'releases_list',
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    """Sitemap for product pages"""
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        # Return all products (available and unavailable, since they are still viewable)
        return Product.objects.all()

    def location(self, obj):
        return reverse('food_de', kwargs={'slug': obj.slug})


class BlogPostSitemap(Sitemap):
    """Sitemap for blog posts"""
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        # Only published blog posts
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('blog_details', kwargs={'slug': obj.slug})
