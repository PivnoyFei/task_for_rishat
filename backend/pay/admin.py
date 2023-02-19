from django.contrib import admin
from pay.models import AmountItem, Discount, Item, Order, Tax
from payment.settings import VALUE_DISPLAY


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'description', 'price', 'currency', 'tax_price', 'final_price'
    )
    readonly_fields = ('final_price', 'tax_price', )
    search_fields = ('name', )
    empty_value_display = VALUE_DISPLAY


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'percent', )
    search_fields = ('name', )
    empty_value_display = VALUE_DISPLAY


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'percent', )
    search_fields = ('name', )
    empty_value_display = VALUE_DISPLAY


class Itemline(admin.TabularInline):
    model = AmountItem
    extra = 10


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'user', 'price_rub', 'price_usd', 'created', 'currency',  'completed',
    )
    readonly_fields = (
        'name', 'user', 'price_rub', 'price_usd', 'created', 'currency', 'completed',
    )
    search_fields = ('name', )
    empty_value_display = VALUE_DISPLAY
