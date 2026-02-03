"""
Interface Layer: Order Adapter
اتصال لایه interface به application layer برای سفارش‌ها
"""
import logging
from typing import Dict, Any, Optional, List

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from ...application.services.order_service import OrderService, OrderException
from ...application.dto.order_dto import (
    OrderDTO,
    OrderSummaryDTO,
    OrderManagementDTO,
    OrderStatisticsDTO,
    OrderResponseDTO
)

logger = logging.getLogger(__name__)


class OrderAdapter:
    """
    Adapter برای اتصال views به سرویس سفارش‌ها
    """

    @staticmethod
    @login_required
    def profile_view(request: HttpRequest) -> HttpResponse:
        """
        View پروفایل کاربر با نمایش سفارش‌ها
        
        Args:
            request: درخواست HTTP
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            orders = OrderService.get_user_orders(request.user)
            return render(request, "freshbread/pf.html", {"orders": orders})
            
        except OrderException as e:
            messages.error(request, str(e))
            return render(request, "freshbread/pf.html", {"orders": []})
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در نمایش پروفایل: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
            return render(request, "freshbread/pf.html", {"orders": []})

    @staticmethod
    @login_required
    def edit_profile_view(request: HttpRequest) -> HttpResponse:
        """
        View ویرایش پروفایل
        
        Args:
            request: درخواست HTTP
        
        Returns:
            HttpResponse: پاسخ
        """
        return render(request, "freshbread/pfe.html")

    @staticmethod
    @login_required
    def order_detail_view(request: HttpRequest, order_code: str) -> HttpResponse:
        """
        View جزئیات سفارش
        
        Args:
            request: درخواست HTTP
            order_code: کد سفارش
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            result = OrderService.get_order_details(order_code, request.user)
            return render(request, "order_detail.html", {"order": result})
            
        except OrderException as e:
            messages.error(request, str(e))
            return redirect('profile')
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در نمایش جزئیات سفارش: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
            return redirect('profile')

    @staticmethod
    @user_passes_test(lambda u: u.is_staff)
    def manage_orders_view(request: HttpRequest) -> HttpResponse:
        """
        View مدیریت سفارش‌ها
        
        Args:
            request: درخواست HTTP
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            if request.method == 'POST':
                action = request.POST.get('action')
                order_id = request.POST.get('order_id')
                
                if not order_id:
                    messages.error(request, "شناسه سفارش مشخص نشده")
                    return redirect('manage_orders')
                
                order_id = int(order_id)
                
                if action == 'update_status':
                    new_status = request.POST.get('new_status')
                    if not new_status:
                        messages.error(request, "وضعیت جدید مشخص نشده")
                        return redirect('manage_orders')
                    
                    result = OrderService.update_order_status(order_id, new_status)
                    messages.success(request, result['message'])
                    
                elif action == 'cancel':
                    result = OrderService.cancel_order(order_id)
                    messages.success(request, result['message'])
                    
                elif action == 'delete':
                    result = OrderService.delete_order(order_id)
                    messages.success(request, result['message'])
                    
                else:
                    messages.error(request, "عملیات نامعتبر")
                
                return redirect('manage_orders')
            
            # GET request - نمایش لیست سفارش‌ها
            orders = OrderService.get_all_orders()
            stats = OrderService.get_order_statistics()
            
            # تبدیل به DTOها
            orders_dto = [OrderManagementDTO.from_model(order) for order in orders]
            stats_dto = OrderStatisticsDTO.from_stats(stats)
            
            context = {
                'orders': orders_dto,
                'stats': stats_dto
            }
            
            return render(request, 'freshbread/order_manage.html', context)
            
        except OrderException as e:
            messages.error(request, str(e))
            return redirect('manage_orders')
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در مدیریت سفارش‌ها: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
            return redirect('manage_orders')

    @staticmethod
    def update_order_status_view(request: HttpRequest, order_id: int, new_status: str) -> HttpResponse:
        """
        View بروزرسانی وضعیت سفارش
        
        Args:
            request: درخواست HTTP
            order_id: شناسه سفارش
            new_status: وضعیت جدید
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            result = OrderService.update_order_status(order_id, new_status)
            messages.success(request, result['message'])
            
        except OrderException as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در بروزرسانی وضعیت سفارش: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
        
        return redirect('manage_orders')

    @staticmethod
    def cancel_order_view(request: HttpRequest, order_id: int) -> HttpResponse:
        """
        View لغو سفارش
        
        Args:
            request: درخواست HTTP
            order_id: شناسه سفارش
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            result = OrderService.cancel_order(order_id)
            messages.success(request, result['message'])
            
        except OrderException as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در لغو سفارش: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
        
        return redirect('manage_orders')

    @staticmethod
    def order_info_view(request: HttpRequest, order_id: int) -> HttpResponse:
        """
        View اطلاعات سفارش
        
        Args:
            request: درخواست HTTP
            order_id: شناسه سفارش
        
        Returns:
            HttpResponse: پاسخ
        """
        try:
            # گرفتن سفارش از repository
            from ...infrastructure.repositories.order_repository import OrderRepository
            order = OrderRepository.get_order_by_id(order_id)
            if not order:
                messages.error(request, "سفارش پیدا نشد")
                return redirect('manage_orders')
            
            return render(request, 'freshbread/order/order_info.html', {'order': order})
            
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در نمایش اطلاعات سفارش: {str(e)}")
            messages.error(request, "خطای غیرمنتظره رخ داد")
            return redirect('manage_orders')

    @staticmethod
    def api_get_user_orders(request: HttpRequest) -> JsonResponse:
        """
        API برای گرفتن سفارش‌های کاربر
        
        Args:
            request: درخواست HTTP
        
        Returns:
            JsonResponse: پاسخ JSON
        """
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            orders = OrderService.get_user_orders(request.user)
            
            return JsonResponse({
                'success': True,
                'orders': orders
            })
            
        except OrderException as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در API سفارش‌های کاربر: {str(e)}")
            return JsonResponse({'success': False, 'error': 'خطای غیرمنتظره رخ داد'}, status=500)

    @staticmethod
    @user_passes_test(lambda u: u.is_staff)
    def api_update_order_status(request: HttpRequest, order_id: int) -> JsonResponse:
        """
        API برای بروزرسانی وضعیت سفارش
        
        Args:
            request: درخواست HTTP
            order_id: شناسه سفارش
        
        Returns:
            JsonResponse: پاسخ JSON
        """
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            import json
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if not new_status:
                return JsonResponse({'success': False, 'error': 'Status is required'}, status=400)
            
            result = OrderService.update_order_status(order_id, new_status)
            
            response_dto = OrderResponseDTO.success_response(
                message=result['message'],
                order_id=result['order_id'],
                order_code=result['order_code']
            )
            
            return JsonResponse({
                'success': response_dto.success,
                'message': response_dto.message,
                'order_id': response_dto.order_id,
                'order_code': response_dto.order_code
            })
            
        except OrderException as e:
            response_dto = OrderResponseDTO.error_response(str(e))
            return JsonResponse({
                'success': response_dto.success,
                'message': response_dto.message
            }, status=400)
        except Exception as e:
            logger.exception(f"خطای غیرمنتظره در API بروزرسانی وضعیت: {str(e)}")
            response_dto = OrderResponseDTO.error_response("خطای غیرمنتظره رخ داد")
            return JsonResponse({
                'success': response_dto.success,
                'message': response_dto.message
            }, status=500)