from django.urls import re_path
from .views import (
  ProductsView,
  ProductDetailView,
  CreateProductView,
  UpdateProductView,
  DeleteProductView,
  DeleteProductsByIdsView,
  ImportProductsView,
  ExportProductsView,
  MostSoldProductsView,
  MostRatedProductsView,
  ProductCategoryView,
)

urlpatterns = [
  re_path(r'^products/?$', ProductsView.as_view(), name='products-list'),
  re_path(r'^products/(?P<pk>\d+)/?$', ProductDetailView.as_view(), name='product-detail'),
  re_path(r'^products/create/?$', CreateProductView.as_view(), name='product-create'),
  re_path(r'^products/(?P<pk>\d+)/update/?$', UpdateProductView.as_view(), name='product-update'),
  re_path(r'^products/(?P<pk>\d+)/delete/?$', DeleteProductView.as_view(), name='product-delete'),
  re_path(r'^products/delete/?$', DeleteProductsByIdsView.as_view(), name='product-delete'),
  re_path(r'^products/import-excel/?$', ImportProductsView.as_view(), name='product-import'),
  re_path(r'^products/export-excel/?$', ExportProductsView.as_view(), name='product-export'),
  re_path(r'^products/most-sold/?$', MostSoldProductsView.as_view(), name='product-most-sold'),
  re_path(r'^products/most-rated/?$', MostRatedProductsView.as_view(), name='product-most-rated'),
  re_path(r'^products/category/(?P<category_id>\d+)/?$', ProductCategoryView.as_view(), name='product-category'),
]