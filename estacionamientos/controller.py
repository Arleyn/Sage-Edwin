# Archivo con funciones de control para SAGE
from estacionamientos.models import Estacionamiento
from datetime import datetime, timedelta, time
from django.db.models.lookups import Minute
from decimal import Decimal
from collections import OrderedDict

# chequeo de horarios de extended
def HorarioEstacionamiento(HoraInicio, HoraFin):
	return HoraFin > HoraInicio

def validarHorarioReserva(inicioReserva, finReserva, apertura, cierre):
	if inicioReserva >= finReserva:
		return (False, 'El horario de inicio de reservacion debe ser menor al horario de fin de la reserva.')
	if finReserva - inicioReserva < timedelta(hours=1):
		return (False, 'El tiempo de reserva debe ser al menos de 1 hora.')
	if inicioReserva.replace(second=0, microsecond=0) < datetime.now().replace(second=0, microsecond=0):
		return (False, 'La reserva no puede tener lugar en el pasado.')
	if finReserva > datetime.now()+timedelta(days=7):
		return (False, 'La reserva debe estar dentro de los próximos 7 días.')
	if apertura.hour==0 and apertura.minute==0 \
		and cierre.hour==23 and cierre.minute==59:
		seven_days=timedelta(days=7)
		if finReserva-inicioReserva<=seven_days :
			return (True,'')
		else:
			return(False,'Se puede reservar un puesto por un maximo de 7 dias.')
	else:
		delta =       timedelta(hours=cierre.hour,  minutes=cierre.minute)
		delta = delta-timedelta(hours=apertura.hour,minutes=apertura.minute)

		if finReserva-inicioReserva>delta:
			return (False, 'El horario de inicio de reserva debe estar en un horario válido.')
		else:
			hora_inicio = time(hour = inicioReserva.hour, minute = inicioReserva.minute)
			hora_final  = time(hour = finReserva.hour   , minute = finReserva.minute)
			if hora_inicio<apertura:
				return (False, 'El horario de inicio de reserva debe estar en un horario válido.')
			if hora_final > cierre:
				return (False, 'El horario de fin de la reserva debe estar en un horario válido.')
		return (True,'')

def marzullo(idEstacionamiento, hIn, hOut):
	e = Estacionamiento.objects.get(id = idEstacionamiento)
	ocupacion = []
	capacidad = e.nroPuesto

	for reserva in e.reserva_set.all():
		ocupacion += [(reserva.inicioReserva, 1), (reserva.finalReserva, -1)]
	ocupacion += [(hIn, 1), (hOut, -1)]

	count = 0
	for r in sorted(ocupacion):
		count += r[1]
		if count > capacidad:
			return False
	return True

def tasa_reservaciones(id_estacionamiento):
	e = Estacionamiento.objects.get(id = id_estacionamiento)
	ahora = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
	reservas_filtradas = e.reserva_set.filter(finalReserva__gt=ahora)
	lista_fechas=[(ahora+timedelta(i)).date() for i in range(8)]
	lista_valores=[0 for i in range(8)]
	ocupacion_por_dia = OrderedDict(zip(lista_fechas,lista_valores))
	UN_DIA = timedelta(days = 1)
	
	for reserva in reservas_filtradas:
		# Caso del inicio de la reserva
		if (reserva.inicioReserva < ahora):
			reserva_inicio = ahora
		else:
			reserva_inicio = reserva.inicioReserva
		reserva_final = reserva.finalReserva
		final_aux=reserva_inicio.replace(hour=0,minute=0,second=0,microsecond=0)
		while (reserva_final-reserva_inicio>UN_DIA): 
			final_aux+=UN_DIA
			longitud_reserva = final_aux-reserva_inicio
			ocupacion_por_dia[reserva_inicio.date()] += longitud_reserva.seconds/60+longitud_reserva.days*24*60
			reserva_inicio = final_aux
		if reserva_final.date()>reserva_inicio.date():
			longitud_reserva = reserva_final.replace(hour=0,minute=0,second=0,microsecond=0) - reserva_inicio
			ocupacion_por_dia[reserva_inicio.date()] += longitud_reserva.seconds/60 + longitud_reserva.days*24*60
			reserva_inicio+=UN_DIA
			reserva_inicio=reserva_inicio.replace(hour=0,minute=0,second=0,microsecond=0)
		longitud_reserva=reserva_final-reserva_inicio
		ocupacion_por_dia[reserva_inicio.date()] += longitud_reserva.seconds/60 + longitud_reserva.days*24*60
	return ocupacion_por_dia

def calcular_porcentaje_de_tasa(hora_apertura,hora_cierre, capacidad, ocupacion):
	factor_divisor=timedelta(hours=hora_cierre.hour,minutes=hora_cierre.minute)
	factor_divisor-=timedelta(hours=hora_apertura.hour,minutes=hora_apertura.minute)
	factor_divisor=Decimal(factor_divisor.seconds)/Decimal(60)
	if (hora_apertura==time(0,0) and hora_cierre==time(23,59)):
		factor_divisor+=1 # Se le suma un minuto
	for i in ocupacion.keys():
		ocupacion[i]=(Decimal(ocupacion[i])*100/(factor_divisor*capacidad)).quantize(Decimal('1.0'))
