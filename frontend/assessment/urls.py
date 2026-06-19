from django.urls import path

from assessment import views

urlpatterns = [
    path("", views.lookup_view, name="lookup"),
    path("manual/", views.manual_inputs_view, name="manual_inputs"),
    path("results/", views.results_view, name="results"),
    path("download/<str:file_format>/", views.download_view, name="download"),
    path("history/", views.history_view, name="history"),
    path("history/<int:pk>/", views.saved_lookup_detail_view, name="saved_lookup_detail"),
    path("history/<int:pk>/download/<str:file_format>/", views.download_saved_view, name="download_saved"),
    path("compare/", views.compare_view, name="compare"),
    path("chat/", views.chat_view, name="chat"),
    path("new/", views.new_lookup_view, name="new_lookup"),
]
