# pages/views/base.py

from django.views.generic import (
    TemplateView,
    DetailView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django_tables2 import SingleTableView

from ..mixins.views import FormMessagesMixin


class BaseTemplateView(TemplateView):
    """
    Base class for template views that adds a customizable page title to the context data. This
    class extends the standard TemplateView to allow for the inclusion of a page title, which can
    be set and accessed in the template.

    Attributes:
        page_title (str): The title of the page to be included in the context.

    Methods:
        get_context_data(**kwargs): Returns the context data, including the page title.
    """

    page_title = None

    def get_context_data(self, **kwargs):
        """
        This class-level attribute holds the title of the page to be included in the context data.
        It is intended to be overridden in subclasses to provide a specific title for each template
        view.

        Attributes:
            page_title (str): The title of the page to be included in the context.
        """

        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class BaseDetailView(DetailView):
    """
    Base class for detail views that adds a customizable page title to the context data. This class
    extends the standard DetailView to allow for the inclusion of a page title, which can be set
    and accessed in the template.

    Attributes:
        page_title (str): The title of the page to be included in the context.

    Methods:
        get_context_data(**kwargs): Returns the context data, including the page title.
    """

    page_title = None

    def get_context_data(self, **kwargs):
        """
        This class-level attribute holds the title of the page to be included in the context data.
        It is intended to be overridden in subclasses to provide a specific title for each template
        view.

        Attributes:
            page_title (str): The title of the page to be included in the context.
        """
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class BaseListView(ListView):
    """
    Base class for list views that supports pagination, customizable page titles, and filtering.
    This class extends the standard ListView to include features for managing the display of lists,
    including the ability to filter results based on query parameters.

    Attributes:
        paginate_by (int): The number of items to display per page.
        page_title (str): The title of the page to be included in the context.
        filterset_class (type): An optional class used for filtering the queryset.

    Methods:
        get_context_data(**kwargs): Returns the context data, including the page title and
            filterset if applicable.
        get_queryset(): Returns the filtered queryset if a filterset class is provided; otherwise,
            returns the default queryset.
    """

    paginate_by = 10
    page_title = None
    filterset_class = None

    def get_context_data(self, **kwargs):
        """
        Retrieves and returns the context data for the template, including the page title and an
        optional filterset. This method enhances the context by adding the page title and, if a
        filterset class is defined, initializes it with the current request parameters and the
        queryset.

        Args:
            self: The instance of the class.
            **kwargs: Additional keyword arguments to pass to the superclass method.

        Returns:
            dict: A dictionary containing the context data, including the page title and filterset
                if applicable.
        """

        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title

        if self.filterset_class:
            context["filterset"] = self.filterset_class(
                self.request.GET, queryset=self.get_queryset()
            )
        return context

    def get_queryset(self):
        """
        Retrieves the queryset for the view, applying filtering if a filterset class is defined.
        This method checks for the presence of a filterset class and, if available, returns the
        filtered queryset based on the current request parameters.

        Args:
            self: The instance of the class.

        Returns:
            QuerySet: The filtered queryset if a filterset class is provided; otherwise, the
                default queryset.
        """

        if self.filterset_class:
            return self.filterset_class(self.request.GET, super().get_queryset()).qs
        return super().get_queryset()


class BaseTableListView(SingleTableView):
    """
    Base class for views that display a table of data with pagination and optional filtering. This
    class extends SingleTableView to provide a structured way to manage and display tabular data,
    including support for filtering and pagination.

    Attributes:
        template_name (str): The template used to render the table view.
        table_class (type): The class of the table to be displayed.
        filterset_class (type): The class used for filtering the queryset.

    Methods:
        get_table(): Retrieves the table and applies pagination based on the request parameters.
        get_queryset(): Retrieves the queryset and applies filtering if a filterset class is
            defined.
        get_context_data(**kwargs): Returns the context data, including the filterset if
            applicable.

    Args:
        self: The instance of the class.
        **kwargs: Additional keyword arguments to pass to the superclass methods.

    Returns:
        dict: A dictionary containing the context data, including the filterset and paginated
            table.
    """

    template_name = "django_tables2/bootstrap4.html"
    table_class = None
    filterset_class = None

    def get_table(self):
        """
        Retrieves the table for the view and applies pagination based on the request parameters.
        This method enhances the default table retrieval by ensuring that the table is paginated,
        allowing for better management of large datasets.

        Args:
            self: The instance of the class.

        Returns:
            Table: The paginated table object ready for rendering.
        """

        table = super().get_table()
        table.paginate(page=self.request.GET.get("page", 1), per_page=10)
        return table

    def get_queryset(self):
        """
        Retrieves the queryset for the view, applying filtering if a filterset class is defined.
        This method allows for dynamic filtering of the queryset based on request parameters,
        enabling more tailored data retrieval for the view.

        Args:
            self: The instance of the class.

        Returns:
            QuerySet: The filtered queryset if a filterset class is provided; otherwise, the
                default queryset.
        """

        queryset = super().get_queryset()
        if self.filterset_class:
            self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
            return self.filterset.qs
        return queryset

    def get_context_data(self, **kwargs):
        """
        Retrieves and returns the context data for the template, including any filterset if it
        exists. This method enhances the context by adding the filterset to the context dictionary,
        allowing for better integration of filtering functionality in the view.

        Args:
            self: The instance of the class.
            **kwargs: Additional keyword arguments to pass to the superclass method.

        Returns:
            dict: A dictionary containing the context data, including the filterset if applicable.
        """

        context = super().get_context_data(**kwargs)
        if hasattr(self, "filterset"):
            context["filterset"] = self.filterset
        return context


class BaseCreateView(FormMessagesMixin, CreateView):
    """
    Base class for creating views that provides success and error messages. This class extends the
    CreateView and includes functionality for displaying messages upon successful or failed
    creation of an item.

    Attributes:
        success_message (str): The message displayed upon successful creation of an item.
        error_message (str): The message displayed when there is an error during the creation
            process.
    """

    success_message = _("Successfully created.")
    error_message = _("There was an error creating the item.")


class BaseUpdateView(FormMessagesMixin, UpdateView):
    """
    Base class for updating views that provides success and error messages. This class extends the
    UpdateView and includes functionality for displaying messages upon successful or failed updates
    of an item.

    Attributes:
        success_message (str): The message displayed upon successful update of an item.
        error_message (str): The message displayed when there is an error during the update
            process.
    """

    success_message = _("Successfully updated.")
    error_message = _("There was an error updating the item.")


class BaseDeleteView(DeleteView):
    """
    Base class for delete views that provides success and error messages upon deletion. This
    class extends the DeleteView and includes functionality to display messages based on the
    outcome of the delete operation.

    Attributes:
        success_message (str): The message displayed upon successful deletion of an item.
        error_message (str): The message displayed when there is an error during the deletion
            process.

    Methods:
        delete(request, *args, **kwargs): Attempts to delete the object and display the appropriate
            success or error message.
    """

    success_message = _("Successfully deleted.")
    error_message = _("There was an error deleting the item.")

    def delete(self, request, *args, **kwargs):
        """
        Handles the deletion of an object and displays appropriate success or error messages. This
        method attempts to delete the object and, based on the outcome, shows a success message if
        the deletion is successful or an error message if an exception occurs.

        Args:
            self: The instance of the class.
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The response from the delete operation, typically a redirect to the
                success URL.

        Raises:
            Exception: Catches any exception that occurs during the deletion process and displays
                an error message.
        """

        try:
            response = super().delete(request, *args, **kwargs)
            if self.success_message:
                messages.success(self.request, self.success_message)
            return response
        except Exception:
            if self.error_message:
                messages.error(self.request, self.error_message)
            return redirect(self.get_success_url())


class BaseManageView(BaseTemplateView):
    """
    Base class for management views that extends the functionality of template views. This class
    provides a mechanism to include related objects in the context data, allowing for easier
    management of related models.

    Attributes:
        related_model (type): The model class related to the view.
        related_queryset (QuerySet): The queryset of related objects to be included in the context.

    Methods:
        get_context_data(**kwargs): Returns the context data, including related objects if
            specified.

    Args:
        self: The instance of the class.
        **kwargs: Additional keyword arguments to pass to the superclass method.

    Returns:
        dict: A dictionary containing the context data, including related objects if applicable.
    """

    related_model = None
    related_queryset = None

    def get_context_data(self, **kwargs):
        """
        Retrieves and returns the context data for the template, including related objects if
        specified. This method enhances the context by adding a queryset of related objects,
        allowing for better management and display of related data in the view.

        Args:
            self: The instance of the class.
            **kwargs: Additional keyword arguments to pass to the superclass method.

        Returns:
            dict: A dictionary containing the context data, including related objects if
                applicable.
        """

        context = super().get_context_data(**kwargs)
        if self.related_model and self.related_queryset:
            context["related_objects"] = self.related_queryset
        return context
