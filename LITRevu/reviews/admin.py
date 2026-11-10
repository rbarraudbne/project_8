from django.contrib import admin

from .models import Review, Ticket, UserFollows


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'time_created')
    list_filter = ('user',)
    search_fields = ('title', 'description')
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
