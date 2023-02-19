from decimal import Decimal
from random import choice, randint
from string import ascii_uppercase

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver

User = get_user_model()


def num_order() -> str:
    return f'{choice(ascii_uppercase)}{randint(100000000, 999999999)}'


class Currency(models.TextChoices):
    RUB = 'rub'
    USD = 'usd'


class Discount(models.Model):
    name = models.CharField('Скидка', max_length=200, unique=True, db_index=True)
    percent = models.DecimalField(
        'Скидка в %',
        max_digits=3,
        decimal_places=1,
        default=0,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Скидка'
        verbose_name_plural = 'Скидки'

    def __str__(self) -> str:
        return self.name[:50]


class Tax(models.Model):
    name = models.CharField('Налог', max_length=200, unique=True, db_index=True)
    percent = models.DecimalField(
        'Налог в %',
        max_digits=3,
        decimal_places=1,
        default=0,
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Налог'
        verbose_name_plural = 'Налоги'

    def __str__(self) -> str:
        return self.name[:50]


class Item(models.Model):
    name = models.CharField('Название', max_length=200, unique=True, db_index=True)
    description = models.TextField('Описание')
    price = models.DecimalField(
        'Цена без налогов и скидок',
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    currency = models.CharField(
        'Валюта',
        choices=Currency.choices,
        default=Currency.USD,
        max_length=3,
    )
    discount = models.ForeignKey(
        Discount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Скидка',
        related_name="items",
    )
    tax = models.ManyToManyField(
        Tax,
        blank=True,
        verbose_name='Налог',
        related_name="items",
    )
    tax_price = models.DecimalField(
        'Цена без скидки',
        null=True,
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    final_price = models.DecimalField(
        'Финальная цена',
        null=True,
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        ordering = ('name', )
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self) -> str:
        return self.name[:50]

    @staticmethod
    def item_tax(sender, instance, action, reverse, model, pk_set, **kwargs) -> None:
        if action in ('pre_add', 'pre_remove'):
            if not instance.tax_price:
                instance.tax_price = instance.price
            for tax_id in pk_set:
                tax = model.objects.get(id=tax_id).percent
                if action == 'pre_add':
                    instance.tax_price += instance.price / 100 * tax
                elif action == 'pre_remove':
                    instance.tax_price -= instance.price / 100 * tax

            instance.final_price = instance.tax_price
            if action == 'pre_add' and instance.discount:
                discount = instance.discount.percent
                instance.final_price -= instance.tax_price / 100 * discount
            instance.save()


class Order(models.Model):
    name = models.CharField(
        'Номер заказа',
        max_length=10,
        unique=True,
        db_index=True,
        default=num_order,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Покупатель',
        related_name='orders',
    )
    item = models.ManyToManyField(
        Item,
        verbose_name='Товар',
        through='AmountItem',
        related_name="orders",
    )
    price_rub = models.DecimalField(
        'Цена в рублях',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        default=0,
    )
    price_usd = models.DecimalField(
        'Цена в долларах',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        default=0,
    )
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    currency = models.CharField('Валюта', max_length=3)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created', )
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self) -> str:
        return self.name


class AmountItem(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name='Товар',
        related_name='amount_item',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name='Заказ',
        related_name='amount_item',
    )
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1, 'Не менее одного товара')],
        default=1,
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары заказа'
        constraints = (
            models.UniqueConstraint(
                fields=('item', 'order'),
                name='unique_item_order'
            ),
        )


m2m_changed.connect(receiver=Item.item_tax, sender=Item.tax.through)


@receiver(pre_save, sender=Item)
def item_discount(sender, instance, **kwargs) -> models.Model:
    if not instance.tax_price:
        instance.tax_price = instance.price
    instance.final_price = instance.tax_price
    if instance.discount:
        discount = instance.discount.percent
        instance.final_price -= instance.tax_price / 100 * discount
    return instance
