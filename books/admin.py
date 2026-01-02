from django.contrib import admin
from .models import Book, Author, Category

# Register your models here.
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name','bio')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'stock', 'published_year', 'rating')
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ('authors', 'categories')
    search_fields = ('title', 'authors__name')
    exclude = ('search_vector',)

    def image_preview(self, obj):
        if obj.cover_image:
            return f'<img src="{obj.cover_image.url}" width="50" height="70" style="object-fit: cover;" />'
        return "No Image"
    
    image_preview.allow_tags = True
    image_preview.short_description = 'Cover'