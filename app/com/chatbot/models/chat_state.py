from django.db import models

class ChatState(models.Model):
    user_id = models.CharField(max_length=255)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    state = models.CharField(max_length=255, default="initial")
    menu_page = models.IntegerField(default=0)  # Página actual del menú
    last_menu = models.CharField(max_length=255, null=True, blank=True)  # Último menú visitado
    last_submenu = models.CharField(max_length=255, null=True, blank=True)  # Último submenú visitado
    search_term = models.CharField(max_length=255, null=True, blank=True)  # Término de búsqueda actual
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user_id", "business_unit")
        indexes = [
            models.Index(fields=["user_id", "business_unit"]),
            models.Index(fields=["state"]),
            models.Index(fields=["menu_page"]),
            models.Index(fields=["last_menu"]),
            models.Index(fields=["last_submenu"]),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.business_unit.name} - {self.state}"

    async def reset_menu_state(self):
        """Resetea el estado de navegación del menú."""
        self.menu_page = 0
        self.last_menu = None
        self.last_submenu = None
        self.search_term = None
        await self.asave()

    async def update_menu_state(self, menu: str = None, submenu: str = None, page: int = None):
        """Actualiza el estado de navegación del menú."""
        if menu is not None:
            self.last_menu = menu
        if submenu is not None:
            self.last_submenu = submenu
        if page is not None:
            self.menu_page = page
        await self.asave()

    async def update_search_term(self, term: str):
        """Actualiza el término de búsqueda actual."""
        self.search_term = term
        await self.asave() 