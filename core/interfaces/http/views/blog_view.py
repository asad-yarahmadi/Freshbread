from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from core.infrastructure.models import BlogPost, BlogReview
import os
import requests

def blog_details(request, slug):
    from django.utils import timezone
    from django.db.models import F
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    viewed_posts = request.session.get('viewed_posts', [])
    if post.pk not in viewed_posts:
        BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
        viewed_posts.append(post.pk)
        request.session['viewed_posts'] = viewed_posts
        post.refresh_from_db(fields=['views_count'])
    today = timezone.now().date()
    recent = BlogPost.objects.filter(is_published=True, created_at__date=today).exclude(pk=post.pk)[:4]
    popular = BlogPost.objects.filter(is_published=True).exclude(pk=post.pk).order_by('-views_count', '-likes_count')[:6]
    liked_posts = request.session.get('liked_posts', [])
    is_liked = post.pk in liked_posts
    reviews = BlogReview.objects.filter(post=post, is_approved=True)
    avg = 0
    if reviews.exists():
        avg = round(sum(r.rating for r in reviews) / reviews.count(), 1)
    return render(request, 'freshbread/blog/blog_details.html', {"post": post, "recent": recent, "popular": popular, "reviews": reviews, "avg": avg, "is_liked": is_liked})

def blog(request):
    q = request.GET.get("q", "").strip()
    posts = BlogPost.objects.filter(is_published=True)
    if q:
        if q.startswith('#'):
            tag = q[1:]
            posts = posts.filter(tags__icontains=tag)
        else:
            posts = posts.filter(Q(title__icontains=q) | Q(seo_keywords__icontains=q))
    posts = posts.order_by('-likes_count', '-views_count', '-created_at')
    return render(request, 'freshbread/blog/blog.html', {"posts": posts, "q": q})


import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.application.services.content_moderation import moderate_text
from core.infrastructure.models import BlogPost, BlogReview
 



@login_required
def blog_add(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        seo_keywords = request.POST.get("seo_keywords", "").strip()
        tags = request.POST.get("tags", "").strip()
        cover_list = request.FILES.get("cover_list")
        cover_single = request.FILES.get("cover_single")

        # ---- validation ----
        if not title or not content or not cover_list or not cover_single:
            messages.error(request, "Title, content, and both images are required.")
            return redirect("blog_add")

        # ---- AI moderation ----
        api_key = os.environ.get("OPENAI_API_KEY")
        moderation_error = moderate_text(api_key, content)
        if moderation_error:
            messages.warning(request, moderation_error)
            # continue anyway

        # ---- save post ----
        post = BlogPost.objects.create(
            author=request.user,
            title=title,
            content=content,
            seo_keywords=seo_keywords,
            tags=tags,
            cover_list=cover_list,
            cover_single=cover_single,
        )

        messages.success(request, "Blog submitted successfully and is under review.")
        return redirect("blog_manage")

    return render(request, "freshbread/blog/blog_add.html")


def blog_like(request, slug):
    from django.views.decorators.http import require_POST
    from django.db.models import F
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    if request.method != 'POST':
        return redirect('blog_details', slug=slug)
    liked_posts = request.session.get('liked_posts', [])
    if post.pk in liked_posts:
        BlogPost.objects.filter(pk=post.pk, likes_count__gt=0).update(likes_count=F('likes_count') - 1)
        liked_posts = [pid for pid in liked_posts if pid != post.pk]
        request.session['liked_posts'] = liked_posts
        toggled_like = False
    else:
        BlogPost.objects.filter(pk=post.pk).update(likes_count=F('likes_count') + 1)
        liked_posts.append(post.pk)
        request.session['liked_posts'] = liked_posts
        toggled_like = True
    from django.http import JsonResponse
    post.refresh_from_db(fields=['likes_count'])
    return JsonResponse({'liked': toggled_like, 'likes': post.likes_count})


@login_required
def blog_manage(request):
    posts = BlogPost.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'freshbread/blog/blog_manage.html', {"posts": posts})
    # return render(request, 'freshbread/ecommerce/coming_soon.html')


@login_required
def blog_edit(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, author=request.user)
    if request.method == "POST":
        post.title = request.POST.get("title", post.title)
        post.content = request.POST.get("content", post.content)
        post.seo_keywords = request.POST.get("seo_keywords", post.seo_keywords)
        post.tags = request.POST.get("tags", post.tags)
        if request.FILES.get("cover_list"):
            post.cover_list = request.FILES["cover_list"]
        if request.FILES.get("cover_single"):
            post.cover_single = request.FILES["cover_single"]

        api_key = os.environ.get("OPENAI_API_KEY")
        issues = _moderate_content(api_key, post.content, post.cover_list, post.cover_single)
        if issues:
            messages.error(request, issues)
            return redirect("blog_edit", slug=post.slug)

        post.save()
        messages.success(request, "Blog updated.")
        return redirect("blog_manage")
    return render(request, 'freshbread/blog/blog_edit.html', {"post": post})



@login_required
def blog_delete(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, author=request.user)
    post.delete()
    messages.success(request, "Blog deleted.")
    return redirect("blog_manage")


def _moderate_content(api_key, text, img1, img2):
    try:
        t = (text or "")[:10000].lower()
        kw = [
            "porn", "sexual", "sex", "nudity", "nsfw", "explicit",
            "rape", "child", "underage", "incest", "bestiality",
            "slur", "hate", "kill", "murder", "suicide", "self-harm", "fuck"
        ]
        if any(k in t for k in kw):
            return "Text violates policy."
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {"model": "omni-moderation-latest", "input": (text or "")[:10000]}
            r = requests.post("https://api.openai.com/v1/moderations", json=data, headers=headers, timeout=10)
            if r.status_code < 400:
                res = r.json()
                flg = False
                cats = {}
                try:
                    flg = res.get("results", [{}])[0].get("flagged", False)
                    cats = res.get("results", [{}])[0].get("categories", {})
                except Exception:
                    flg = False
                if flg:
                    bad = [k for k, v in cats.items() if v]
                    return f"Text violates policy: {', '.join(bad) if bad else ''}"
        return None
    except Exception:
        return "Content moderation failed."


def blog_add_review(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    if request.method == 'POST':
        rating = int(request.POST.get('rating', '5') or '5')
        comment = (request.POST.get('comment', '') or '').strip()
        first_name = request.POST.get('first_name') or (request.user.first_name if request.user.is_authenticated else '')
        last_name = request.POST.get('last_name') or (request.user.last_name if request.user.is_authenticated else '')
        email = request.POST.get('email') or (request.user.email if request.user.is_authenticated else None)
        if rating < 1 or rating > 5:
            rating = 5
        if not comment:
            messages.error(request, 'Please write a review comment.')
            return redirect('blog_details', slug=post.slug)

        rv = BlogReview(post=post, user=request.user if request.user.is_authenticated else None,
                        first_name=first_name or (request.user.username if request.user.is_authenticated else 'Guest'),
                        last_name=last_name or '', email=email, rating=rating, comment=comment,
                        is_approved=False)
        rv.save()
        messages.success(request, 'Your review was submitted and will appear after approval.')
    return redirect('blog_details', slug=post.slug)
