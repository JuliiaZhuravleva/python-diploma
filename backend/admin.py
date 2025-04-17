from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import (
    User, Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Contact, Order, OrderItem, ConfirmEmailToken
)

# Регистрация базовых моделей
admin.site.register(Parameter)
admin.site.register(ConfirmEmailToken)


# Настройка админки для User
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'type', 'is_active', 'is_staff')
    list_filter = ('type', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'company', 'position')}),
        (_('User type'), {'fields': ('type',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'type', 'is_active', 'is_staff'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


admin.site.register(User, UserAdmin)


# Настройка админки для Shop
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'state')
    list_filter = ('state',)
    search_fields = ('name',)

    def get_queryset(self, request):
        # Ограничение списка магазинов для не-суперпользователей
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


# Настройка админки для Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_shops')
    search_fields = ('name',)
    filter_horizontal = ('shops',)

    def get_shops(self, obj):
        return ", ".join([shop.name for shop in obj.shops.all()])

    get_shops.short_description = 'Магазины'


# Настройка админки для Product
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)


# Инлайн для ProductParameter
class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 0


# Настройка админки для ProductInfo
@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'quantity', 'price', 'price_rrc')
    list_filter = ('shop', 'product__category')
    search_fields = ('product__name', 'model')
    inlines = [ProductParameterInline]

    def get_queryset(self, request):
        # Ограничение списка товаров для не-суперпользователей
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'shop'):
            return qs.filter(shop=request.user.shop)
        return qs.none()


# Инлайн для OrderItem
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_product_name', 'quantity', 'get_price')

    def get_product_name(self, obj):
        return obj.product_info.product.name

    get_product_name.short_description = 'Товар'

    def get_price(self, obj):
        return obj.product_info.price

    get_price.short_description = 'Цена'

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Настройка админки для Contact
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'house', 'phone')
    list_filter = ('city', 'is_deleted')
    search_fields = ('user__email', 'city', 'street', 'phone')


# Настройка админки для Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'get_total')
    list_filter = ('state', 'dt')
    search_fields = ('id', 'user__email')
    readonly_fields = ('user', 'dt', 'contact')
    inlines = [OrderItemInline]
    date_hierarchy = 'dt'

    def get_total(self, obj):
        return obj.get_total_cost()

    get_total.short_description = 'Сумма заказа'

    actions = ['mark_as_confirmed', 'mark_as_assembled', 'mark_as_sent', 'mark_as_delivered', 'mark_as_canceled']

    def mark_as_confirmed(self, request, queryset):
        queryset.update(state='confirmed')

    mark_as_confirmed.short_description = "Отметить как подтвержденные"

    def mark_as_assembled(self, request, queryset):
        queryset.update(state='assembled')

    mark_as_assembled.short_description = "Отметить как собранные"

    def mark_as_sent(self, request, queryset):
        queryset.update(state='sent')

    mark_as_sent.short_description = "Отметить как отправленные"

    def mark_as_delivered(self, request, queryset):
        queryset.update(state='delivered')

    mark_as_delivered.short_description = "Отметить как доставленные"

    def mark_as_canceled(self, request, queryset):
        queryset.update(state='canceled')

    mark_as_canceled.short_description = "Отметить как отмененные"

    def get_queryset(self, request):
        # Исключаем корзины из списка заказов
        return super().get_queryset(request).exclude(state='basket')

    def get_readonly_fields(self, request, obj=None):
        # Для администратора все поля доступны для редактирования
        if request.user.is_superuser:
            return self.readonly_fields
        # Для остальных пользователей больше полей только для чтения
        return self.readonly_fields + ('state',)