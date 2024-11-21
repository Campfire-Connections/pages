# pages/models/menu.py

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.db import models

class MenuItem(models.Model):
    """
    Represents a menu item.
    
    Args:
        title: The title of the menu item.
        url_name: The name of the URL associated with the menu item.
        url_params: Parameters for the URL.
        image: An optional image for the menu item.
        image_path: The relative path to a static image.
        css_class: The CSS class for styling the menu item.
        parent: The parent menu item.
        permissions: Permissions required to access the menu item.
        visible_to: Specifies who can see the menu item.
    """
    title = models.CharField(max_length=100, null=True)  # Temporarily allow null
    url_name = models.CharField(max_length=100, null=True)  # Temporarily allow null
    url_params = models.JSONField(default=dict, null=True, blank=True)
    image = models.ImageField(
        upload_to="menu_images/",
        blank=True,
        null=True
    )  # Optional image field
    image_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Relative path to a static image",
    )
    css_class = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="CSS class for the menu item"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )
    permissions = models.ManyToManyField(Permission, blank=True)
    visible_to = models.CharField(
        max_length=20,
        choices=(
            ("all", "All"),
            ("authenticated", "Authenticated"),
            ("guest", "Guest"),
        ),
        default="all",
    )

    def get_url(self):
        """
        Get the URL for the menu item.
        
        Returns:
            str: The URL for the menu item.
        """
        try:
            if self.url_params:
                return reverse(self.url_name, kwargs=self.url_params)
            else:
                return reverse(self.url_name)
        except Exception as e:
            # Handle exceptions or return a fallback URL
            return "#"

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["menus", "parent__id", "id"]


class Menu(models.Model):
    """
    Represents a menu.
    
    Args:
        name: The name of the menu.
        permissions: Permissions required to access the menu.
        items: Menu items associated with the menu.
    """
    name = models.CharField(max_length=100)
    permissions = models.ManyToManyField(Permission, blank=True)
    items = models.ManyToManyField(MenuItem, related_name='menus')

    def __str__(self):
        return self.name
