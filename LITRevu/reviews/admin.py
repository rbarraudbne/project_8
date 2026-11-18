from django.contrib import admin

from .models import Review, Ticket, UserFollows


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'user', 'is_request', 'time_created')
    list_filter = ('is_request', 'user')
    search_fields = ('title', 'author', 'description')
    readonly_fields = ('time_created',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('headline', 'ticket', 'rating', 'user', 'time_created')
    list_filter = ('rating', 'user')
    search_fields = ('headline', 'body')
    readonly_fields = ('time_created',)


@admin.register(UserFollows)
class UserFollowsAdmin(admin.ModelAdmin):
    list_display = ('user', 'followed_user')
    search_fields = ('user__username', 'followed_user__username')
