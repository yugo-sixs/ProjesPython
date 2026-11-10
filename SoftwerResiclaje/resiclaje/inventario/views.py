from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from datetime import date
from .models import Transaccion, Material


class CustomLoginView(LoginView):
    template_name = 'inventario/login.html'     

class RegistrarCompraView(LoginRequiredMixin, CreateView):
    model = Transaccion
    fields = ['material', 'peso_bruto', 'tara']
    template_name = 'captura_compra.html'
    success_url = '/inventario/lista/' # A donde redirige tras guardar

    def form_valid(self, form):
        # Asignamos el usuario logueado como el operador
        form.instance.usuario_operador = self.request.user
        # Definimos que el tipo de movimiento es COMPRA
        form.instance.tipo = 'COMPRA'
        return super().form_valid(form)    

class CorteDiarioView(LoginRequiredMixin, ListView):
    model = Transaccion
    template_name = 'corte_dia.html'
    context_object_name = 'transacciones'

    def get_queryset(self):
        # Filtramos solo las del día de hoy
        return Transaccion.objects.filter(fecha__date=date.today())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        
        # Calculamos totales de Compra y Venta
        context['total_compras'] = Transaccion.objects.filter(
            fecha__date=hoy, tipo='COMPRA'
        ).aggregate(Sum('total_dinero'))['total_dinero__sum'] or 0
        
        context['total_ventas'] = Transaccion.objects.filter(
            fecha__date=hoy, tipo='VENTA'
        ).aggregate(Sum('total_dinero'))['total_dinero__sum'] or 0
        
        context['fecha_corte'] = hoy
        return context