
from operator import add, sub
from typing import Callable, Union

import stripe
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import (HttpRequest, HttpResponsePermanentRedirect,
                         HttpResponseRedirect, JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView
from pay.models import AmountItem, Currency, Item, Order
from pay.utils import local_env, translate_price
from payment.settings import STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY

if not STRIPE_PUBLIC_KEY and not STRIPE_SECRET_KEY:
    STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY = local_env()

stripe.api_key = STRIPE_SECRET_KEY
TypeObject = Union[HttpResponseRedirect, HttpResponsePermanentRedirect, HttpRequest]


class ItemDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о товаре."""
    model = Item
    template_name = 'item.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs: dict) -> dict:
        contex = super(ItemDetailView, self).get_context_data(**kwargs)
        obj = AmountItem.objects.filter(
            item_id=contex['item'].id,
            order__user=self.request.user,
            order__completed=False,
        )
        contex.update({'count_cart': obj[0].amount if obj else False})
        return contex


class IndexListView(ListView):
    """Список товаров и поиск по названию."""
    model = Item
    paginate_by = 15
    template_name = 'index.html'
    context_object_name = 'page_obj'

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super(IndexListView, self).get_context_data(**kwargs)

        if name := self.request.GET.get('search'):
            object_list = self.model.objects.filter(name__icontains=name)
        else:
            object_list = self.model.objects.prefetch_related('tax').all()

        paginator = Paginator(object_list, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            file_exams = paginator.page(page)
        except PageNotAnInteger:
            file_exams = paginator.page(1)
        except EmptyPage:
            file_exams = paginator.page(paginator.num_pages)

        context[self.context_object_name] = file_exams
        return context


class OrderListView(LoginRequiredMixin, ListView):
    """Список заказов."""
    model = Order
    template_name = 'order_list.html'
    context_object_name = 'page_obj'

    def get_context_data(self, **kwargs: dict) -> dict:
        contex = super(OrderListView, self).get_context_data(**kwargs)
        contex.update({'STRIPE_PUBLIC_KEY': STRIPE_PUBLIC_KEY})
        return contex


class AddItemView(LoginRequiredMixin, View):
    """
    Добавляет и удаляет товар из заказа, создает заказ если нет активного заказа.
    Считает стоймость товаров и записывает их в итоговую сумму заказа, каждый со своей валютой.
    Возвращает на страницу с которой пришел пользователь.
    """
    def _total_price(self, order: Order, amount: AmountItem, operator: Callable) -> None:
        if amount.item.currency == 'rub':
            order.price_rub = operator(order.price_rub, amount.item.final_price)
            order.save(update_fields=['price_rub'])
        else:
            order.price_usd = operator(order.price_usd, amount.item.final_price)
            order.save(update_fields=['price_usd'])

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpResponseRedirect:
        if 'add' in request.path.split('/'):
            order = Order.objects.get_or_create(user=request.user, completed=False)[0]
            amount = AmountItem.objects.get_or_create(order_id=order.id, item_id=kwargs['pk'])
            if not amount[1]:
                amount[0].amount = amount[0].amount + 1
                amount[0].save(update_fields=['amount'])
            self._total_price(order, amount[0], add)

        elif 'remove' in request.path.split('/'):
            order = get_object_or_404(Order, user=request.user, completed=False)
            amount = get_object_or_404(AmountItem, order_id=order.id, item_id=kwargs['pk'])
            if amount.amount > 1:
                amount.amount = amount.amount - 1
                amount.save(update_fields=['amount'])
                self._total_price(order, amount, sub)
            else:
                self._total_price(order, amount, sub)
                amount.delete()

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class OrderView(LoginRequiredMixin, View):
    """
    Выдает страницу активного заказа или выполненого если переход идет со списка заказов.
    Считает общую стоймость заказа в каждой валюте.
    """
    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> TypeObject:
        if order_id := request.GET.get('order_id', None):
            amount = AmountItem.objects.prefetch_related('order').filter(order__id=order_id)
        else:
            amount = (
                AmountItem.objects.prefetch_related('order')
                .filter(order__user=request.user, order__completed=False)
            )
        if not amount:
            return redirect("pay:index")

        price_rub, price_usd = translate_price(amount[0].order.price_rub, amount[0].order.price_usd)
        context = {
            'page_obj': amount,
            'currency_obj': [
                {'currency': Currency.RUB, 'total_price': price_rub},
                {'currency': Currency.USD, 'total_price': price_usd},
            ],
            'STRIPE_PUBLIC_KEY': STRIPE_PUBLIC_KEY,
        }
        if order_id:
            return render(request, 'order_detail.html', context)
        return render(request, 'order.html', context)


class StripeView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> JsonResponse:
        """Выполняет заказ в указаной валюте."""
        order = get_object_or_404(Order, id=kwargs['pk'])
        url_path = request.build_absolute_uri('/')
        currency = request.GET.get('currency', 'rub')

        if currency == 'rub':
            total_price, _ = translate_price(order.price_rub, order.price_usd, 'rub')
        else:
            _, total_price = translate_price(order.price_rub, order.price_usd, 'usd')
        if total_price and total_price > 0:
            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': currency,
                                'unit_amount': int(total_price * 100),
                                'product_data': {
                                    'name': order.name,
                                },
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url=f'{url_path}success/',
                    cancel_url=f'{url_path}cancel/'
                )
                Order.objects.filter(id=kwargs['pk']).update(
                    currency=currency, completed=True
                )
                return JsonResponse({
                    'id': session.id
                })

            except Exception as e:
                return JsonResponse({'error': str(e)})
        return JsonResponse({'error': 'Цена меньше 0.01'})
