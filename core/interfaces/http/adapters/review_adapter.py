"""
Interface Layer: Review Adapter
اتصال لایه interface به application layer برای نظرات
"""
import logging
from typing import Dict, Any, Optional, List

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.uploadedfile import UploadedFile

from ...application.services.review_service import ReviewService, ReviewException
from ...application.dto.review_dto import (
    ReviewDTO,
    ReviewCreateDTO,
    ReviewStatsDTO,
    ReviewManagementDTO,
    ReviewResponseDTO
)

logger = logging.getLogger(__name__)


class ReviewAdapter:
    """
    Adapter برای اتصال views به سرویس نظرات
    """

    @staticmethod
    def add_review_view(request: HttpRequest, product_slug: str) -> HttpResponse:
        """
        View برای افزودن نظر جدید
        
        Args:
            request: درخواست HTTP
            product_slug: slug محصول
        
        Returns:
            HttpResponse: پاسخ
        """
        if request.method == 'POST':
            try:
                # گرفتن داده‌ها از فرم
                review_data = request.POST.dict()
                images = request.FILES.getlist('images') if 'images' in request.FILES else []
                
                # ایجاد نظر
                result = ReviewService.create_review(
                    product_slug=product_slug,
                    review_data=review_data,
                    images=images,
                    user=request.user if request.user.is_authenticated else None
                )
                
                messages.success(request, result['message'])
                return redirect('product_detail', slug=product_slug)
                
            except ReviewException as e:
                messages.error(request, str(e))
                return redirect('product_detail', slug=product_slug)
            except Exception as e:
                logger.exception(f"خطای غیرمنتظره در افزودن نظر: {str(e)}")
                messages.error(request, "خطای غیرمنتظره رخ داد")
                return redirect('product_detail', slug=product_slug)
        
        # GET request - نمایش فرم
        return redirect('product_detail', slug=product_slug)

    @staticmethod
    def get_product_reviews_view(request: HttpRequest, product_slug: str) -> HttpResponse:
        """
        View برای نمایش نظرات محصول
        
        Args:
            request: درخواست HTTP
            product_slug: slug محصول
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            # گرفتن نظرات محصول
            result = ReviewService.get_product_reviews(product_slug)
            
            # تبدیل به DTOها
            reviews_dto = [ReviewDTO.from_model(review) for review in result['reviews']]
            stats_dto = ReviewStatsDTO.from_stats(result['stats'])
            
            context = {
                'product': result['product'],
                'reviews': reviews_dto,
                'stats': stats_dto,
            }
            
            return render(request, 'reviews/product_reviews.html', context)
            
        except ReviewException as e:
            messages.error(request, str(e))
            return redirect('home')
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در نمایش نظرات: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
            return redirect('home')

    @staticmethod
    @user_passes_test(lambda u: u.is_staff)
    def review_management_view(request: HttpRequest) -> HttpResponse:
        """
        View مدیریت نظرات
        
        Args:
            request: درخواست HTTP
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            if request.method == 'POST':
                action = request.POST.get('action')
                review_id = request.POST.get('review_id')
                
                if not review_id:
                    messages.error(request, "شناسه نظر مشخص نشده")
                    return redirect('review_management')
                
                review_id = int(review_id)
                
                if action == 'approve':
                    result = ReviewService.approve_review(review_id)
                    messages.success(request, result['message'])
                elif action == 'reject':
                    result = ReviewService.reject_review(review_id)
                    messages.success(request, result['message'])
                elif action == 'delete':
                    result = ReviewService.delete_review(review_id)
                    messages.success(request, result['message'])
                elif action == 'ban_user':
                    result = ReviewService.ban_user_from_reviews(review_id)
                    messages.success(request, result['message'])
                else:
                    messages.error(request, "عملیات نامعتبر")
                
                return redirect('review_management')
            
            # GET request - نمایش لیست نظرات
            pending_reviews = ReviewService.get_pending_reviews()
            all_reviews = ReviewService.get_all_reviews(approved_only=False)
            
            # تبدیل به DTOها
            pending_dto = [ReviewManagementDTO.from_model(review) for review in pending_reviews]
            all_dto = [ReviewManagementDTO.from_model(review) for review in all_reviews]
            
            context = {
                'pending_reviews': pending_dto,
                'all_reviews': all_dto,
            }
            
            return render(request, 'reviews/review_management.html', context)
            
        except ReviewException as e:
            messages.error(request, str(e))
            return redirect('review_management')
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در مدیریت نظرات: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
            return redirect('review_management')

    @staticmethod
    @login_required
    def user_reviews_view(request: HttpRequest) -> HttpResponse:
        """
        View برای نمایش نظرات کاربر
        
        Args:
            request: درخواست HTTP
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            reviews = ReviewService.get_user_reviews(request.user)
            reviews_dto = [ReviewDTO.from_model(review) for review in reviews]
            
            context = {
                'reviews': reviews_dto,
            }
            
            return render(request, 'reviews/user_reviews.html', context)
            
        except ReviewException as e:
            messages.error(request, str(e))
            return redirect('profile')
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در نمایش نظرات کاربر: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
            return redirect('profile')

    @staticmethod
    def api_add_review(request: HttpRequest, product_slug: str) -> JsonResponse:
        """
        API endpoint برای افزودن نظر
        
        Args:
            request: درخواست HTTP
            product_slug: slug محصول
        
        Returns:
            JsonResponse: پاسخ JSON
        """
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            # گرفتن داده‌ها از JSON
            import json
            data = json.loads(request.body)
            images = request.FILES.getlist('images') if 'images' in request.FILES else []
            
            # ایجاد نظر
            result = ReviewService.create_review(
                product_slug=product_slug,
                review_data=data,
                images=images,
                user=request.user if request.user.is_authenticated else None
            )
            
            response_dto = ReviewResponseDTO.success_response(
                message=result['message'],
                review_id=result['review_id']
            )
            
            return JsonResponse({
                'success': response_dto.success,
                'message': response_dto.message,
                'review_id': response_dto.review_id
            })
            
        except ReviewException as e:
            response_dto = ReviewResponseDTO.error_response(str(e))
            return JsonResponse({
                'success': response_dto.success,
                'message': response_dto.message
            }, status=400)
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در API افزودن نظر: {str(e)}")
            response_dto = ReviewResponseDTO.error_response("خطای غیرمنتظره رخ داد")
            return JsonResponse({
                'success': response_dto.success,
                'message': response_dto.message
            }, status=500)

    @staticmethod
    def api_get_product_reviews(request: HttpRequest, product_slug: str) -> JsonResponse:
        """
        API endpoint برای گرفتن نظرات محصول
        
        Args:
            request: درخواست HTTP
            product_slug: slug محصول
        
        Returns:
            JsonResponse: پاسخ JSON
        """
        try:
            # گرفتن نظرات محصول
            result = ReviewService.get_product_reviews(product_slug)
            
            # تبدیل به DTOها
            reviews_dto = [ReviewDTO.from_model(review) for review in result['reviews']]
            stats_dto = ReviewStatsDTO.from_stats(result['stats'])
            
            return JsonResponse({
                'product': {
                    'id': result['product'].id,
                    'name': result['product'].name,
                    'slug': result['product'].slug
                },
                'reviews': [
                    {
                        'id': r.id,
                        'rating': r.rating,
                        'title': r.title,
                        'text': r.text,
                        'first_name': r.first_name,
                        'last_name': r.last_name,
                        'created_at': r.created_at.isoformat(),
                        'images': r.images
                    } for r in reviews_dto
                ],
                'stats': {
                    'total_reviews': stats_dto.total_reviews,
                    'average_rating': stats_dto.average_rating,
                    'rating_distribution': stats_dto.rating_distribution
                }
            })
            
        except ReviewException as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در API گرفتن نظرات: {str(e)}")
            return JsonResponse({'error': 'خطای غیرمنتظره رخ داد'}, status=500)