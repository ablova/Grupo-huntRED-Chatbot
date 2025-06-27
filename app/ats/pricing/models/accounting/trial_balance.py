"""
📊 MODELOS DE BALANCE DE COMPROBACIÓN

Gestión de balances de comprobación y reportes contables.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit, Person
from .accounts import Account

class TrialBalance(models.Model):
    """Balance de comprobación."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='trial_balances'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre del balance")
    date = models.DateField(help_text="Fecha del balance")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Estados
    is_adjusted = models.BooleanField(default=False, help_text="¿Balance ajustado?")
    is_closed = models.BooleanField(default=False, help_text="¿Período cerrado?")
    
    # Totales
    total_debits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de débitos"
    )
    total_credits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de créditos"
    )
    total_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de activos"
    )
    total_liabilities = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de pasivos"
    )
    total_equity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de capital"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_trial_balances'
    )
    
    class Meta:
        verbose_name = "Balance de Comprobación"
        verbose_name_plural = "Balances de Comprobación"
        ordering = ['-date']
        unique_together = ['business_unit', 'date']
    
    def __str__(self):
        return f"{self.business_unit.name} - {self.name} ({self.date})"
    
    def generate_entries(self):
        """Genera las entradas del balance de comprobación."""
        # Eliminar entradas existentes
        self.entries.all().delete()
        
        # Obtener todas las cuentas activas
        accounts = Account.objects.filter(
            chart_of_accounts__business_unit=self.business_unit,
            is_active=True
        ).order_by('account_number')
        
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')
        total_assets = Decimal('0.00')
        total_liabilities = Decimal('0.00')
        total_equity = Decimal('0.00')
        
        for account in accounts:
            # Calcular saldos del período
            opening_balance = account.get_balance(self.period_start)
            ending_balance = account.get_balance(self.period_end)
            period_debits = account.get_period_debits(self.period_start, self.period_end)
            period_credits = account.get_period_credits(self.period_start, self.period_end)
            
            # Crear entrada del balance
            entry = TrialBalanceEntry.objects.create(
                trial_balance=self,
                account=account,
                opening_debit=opening_balance if opening_balance > 0 else Decimal('0.00'),
                opening_credit=abs(opening_balance) if opening_balance < 0 else Decimal('0.00'),
                period_debits=period_debits,
                period_credits=period_credits,
                ending_debit=ending_balance if ending_balance > 0 else Decimal('0.00'),
                ending_credit=abs(ending_balance) if ending_balance < 0 else Decimal('0.00')
            )
            
            # Acumular totales
            total_debits += entry.ending_debit
            total_credits += entry.ending_credit
            
            # Acumular por tipo de cuenta
            if account.account_type == 'asset':
                total_assets += ending_balance
            elif account.account_type == 'liability':
                total_liabilities += ending_balance
            elif account.account_type == 'equity':
                total_equity += ending_balance
        
        # Actualizar totales
        self.total_debits = total_debits
        self.total_credits = total_credits
        self.total_assets = total_assets
        self.total_liabilities = total_liabilities
        self.total_equity = total_equity
        self.save(update_fields=[
            'total_debits', 'total_credits', 'total_assets',
            'total_liabilities', 'total_equity'
        ])
    
    def is_balanced(self):
        """Verifica si el balance está balanceado."""
        return self.total_debits == self.total_credits
    
    def get_balance_sheet_data(self):
        """Obtiene datos para el balance general."""
        return {
            'assets': self.entries.filter(account__account_type='asset'),
            'liabilities': self.entries.filter(account__account_type='liability'),
            'equity': self.entries.filter(account__account_type='equity'),
            'total_assets': self.total_assets,
            'total_liabilities': self.total_liabilities,
            'total_equity': self.total_equity
        }
    
    def get_income_statement_data(self):
        """Obtiene datos para el estado de resultados."""
        return {
            'revenues': self.entries.filter(account__account_type='revenue'),
            'expenses': self.entries.filter(account__account_type='expense'),
            'total_revenues': self.entries.filter(
                account__account_type='revenue'
            ).aggregate(total=models.Sum('ending_credit'))['total'] or Decimal('0.00'),
            'total_expenses': self.entries.filter(
                account__account_type='expense'
            ).aggregate(total=models.Sum('ending_debit'))['total'] or Decimal('0.00')
        }
    
    def close_period(self, closed_by):
        """Cierra el período contable."""
        if not self.is_balanced():
            raise ValueError("No se puede cerrar un período desbalanceado")
        
        self.is_closed = True
        self.save(update_fields=['is_closed'])
        
        # Crear asientos de cierre
        from .journal_entries import JournalEntry, JournalEntryLine
        
        # Cerrar cuentas de ingresos
        revenue_accounts = self.entries.filter(account__account_type='revenue')
        if revenue_accounts.exists():
            revenue_total = revenue_accounts.aggregate(
                total=models.Sum('ending_credit')
            )['total'] or Decimal('0.00')
            
            if revenue_total > 0:
                closing_entry = JournalEntry.objects.create(
                    business_unit=self.business_unit,
                    date=self.period_end,
                    reference=f"CIERRE-{self.date}",
                    description=f"Cierre de ingresos - {self.name}",
                    entry_type='closing',
                    created_by=closed_by
                )
                
                # Débito a cuentas de ingresos
                for entry in revenue_accounts:
                    if entry.ending_credit > 0:
                        JournalEntryLine.objects.create(
                            journal_entry=closing_entry,
                            account=entry.account,
                            description=f"Cierre de {entry.account.name}",
                            debit_amount=entry.ending_credit,
                            credit_amount=Decimal('0.00')
                        )
                
                # Crédito a utilidades retenidas
                retained_earnings = Account.objects.filter(
                    chart_of_accounts__business_unit=self.business_unit,
                    category='retained_earnings'
                ).first()
                
                if retained_earnings:
                    JournalEntryLine.objects.create(
                        journal_entry=closing_entry,
                        account=retained_earnings,
                        description="Cierre de ingresos",
                        debit_amount=Decimal('0.00'),
                        credit_amount=revenue_total
                    )
                
                closing_entry.post(closed_by)
        
        # Cerrar cuentas de gastos
        expense_accounts = self.entries.filter(account__account_type='expense')
        if expense_accounts.exists():
            expense_total = expense_accounts.aggregate(
                total=models.Sum('ending_debit')
            )['total'] or Decimal('0.00')
            
            if expense_total > 0:
                closing_entry = JournalEntry.objects.create(
                    business_unit=self.business_unit,
                    date=self.period_end,
                    reference=f"CIERRE-{self.date}",
                    description=f"Cierre de gastos - {self.name}",
                    entry_type='closing',
                    created_by=closed_by
                )
                
                # Crédito a cuentas de gastos
                for entry in expense_accounts:
                    if entry.ending_debit > 0:
                        JournalEntryLine.objects.create(
                            journal_entry=closing_entry,
                            account=entry.account,
                            description=f"Cierre de {entry.account.name}",
                            debit_amount=Decimal('0.00'),
                            credit_amount=entry.ending_debit
                        )
                
                # Débito a utilidades retenidas
                retained_earnings = Account.objects.filter(
                    chart_of_accounts__business_unit=self.business_unit,
                    category='retained_earnings'
                ).first()
                
                if retained_earnings:
                    JournalEntryLine.objects.create(
                        journal_entry=closing_entry,
                        account=retained_earnings,
                        description="Cierre de gastos",
                        debit_amount=expense_total,
                        credit_amount=Decimal('0.00')
                    )
                
                closing_entry.post(closed_by)

class TrialBalanceEntry(models.Model):
    """Entrada del balance de comprobación."""
    
    trial_balance = models.ForeignKey(
        TrialBalance,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='trial_balance_entries'
    )
    
    # Saldos de apertura
    opening_debit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo de débito de apertura"
    )
    opening_credit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo de crédito de apertura"
    )
    
    # Movimientos del período
    period_debits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Débitos del período"
    )
    period_credits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Créditos del período"
    )
    
    # Saldos de cierre
    ending_debit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo de débito de cierre"
    )
    ending_credit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo de crédito de cierre"
    )
    
    class Meta:
        verbose_name = "Entrada de Balance de Comprobación"
        verbose_name_plural = "Entradas de Balance de Comprobación"
        ordering = ['account__account_number']
        unique_together = ['trial_balance', 'account']
    
    def __str__(self):
        return f"{self.account.account_number} - {self.account.name}"
    
    def get_opening_balance(self):
        """Obtiene el saldo de apertura."""
        if self.opening_debit > 0:
            return self.opening_debit
        elif self.opening_credit > 0:
            return -self.opening_credit
        return Decimal('0.00')
    
    def get_ending_balance(self):
        """Obtiene el saldo de cierre."""
        if self.ending_debit > 0:
            return self.ending_debit
        elif self.ending_credit > 0:
            return -self.ending_credit
        return Decimal('0.00')
    
    def get_net_movement(self):
        """Obtiene el movimiento neto del período."""
        return self.period_debits - self.period_credits 