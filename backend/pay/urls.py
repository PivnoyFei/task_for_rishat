from django.urls import path
from pay import views

app_name = 'pay'

urlpatterns = [
    path('', views.IndexListView.as_view(), name='index'),
    path('order/<str:username>/', views.OrderView.as_view(), name='order'),
    path('order_list/<str:username>/', views.OrderListView.as_view(), name='order_list'),
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='item'),
    path('buy/<int:pk>/', views.StripeView.as_view(), name='buy'),
    path('item/<int:pk>/add/', views.AddItemView.as_view(), name='add_item'),
    path('item/<int:pk>/remove/', views.AddItemView.as_view(), name='remove_item'),
]
