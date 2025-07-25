# decorators.py para la app common
# Aquí se implementarán decoradores personalizados reutilizables.

from functools import wraps
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response


def validate_prerequisites(view_func):
    """
    Decorador para validar prerrequisitos de inscripción.
    
    Este decorador verifica que el estudiante haya aprobado todas las materias
    prerrequisito antes de permitir la inscripción.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Solo aplicar validación en métodos POST (inscripciones)
        if request.method != 'POST':
            return view_func(request, *args, **kwargs)
        
        try:
            from apps.users.models import User
            from apps.materias.models import Materia, Prerrequisito
            from apps.inscripciones.models import Inscripcion, Calificacion
            
            # Obtener datos de la solicitud
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = request.POST
            
            estudiante_id = data.get('estudiante_id') or data.get('estudiante')
            materia_id = data.get('materia_id') or data.get('materia')
            
            # Si no se proporcionan los datos necesarios, continuar sin validar
            if not estudiante_id or not materia_id:
                return view_func(request, *args, **kwargs)
            
            # Verificar que el estudiante y la materia existen
            try:
                estudiante = User.objects.get(id=estudiante_id, role='estudiante')
                materia = Materia.objects.get(id=materia_id)
            except (User.DoesNotExist, Materia.DoesNotExist):
                # Si no existen, dejar que la vista maneje el error
                return view_func(request, *args, **kwargs)
            
            # Obtener prerrequisitos de la materia
            prerrequisitos = Prerrequisito.objects.filter(
                materia=materia
            ).select_related('materia_prerrequisito')
            
            # Validar cada prerrequisito
            for prerrequisito in prerrequisitos:
                materia_prerrequisito = prerrequisito.materia_prerrequisito
                
                # Verificar si el estudiante ha aprobado este prerrequisito
                inscripcion_prerrequisito = Inscripcion.objects.filter(
                    estudiante=estudiante,
                    materia=materia_prerrequisito
                ).first()
                
                if not inscripcion_prerrequisito:
                    error_msg = f"Debe inscribirse primero a la materia prerrequisito: {materia_prerrequisito.nombre}"
                    if hasattr(request, 'data'):
                        # Es una API REST
                        return Response({
                            'error': error_msg,
                            'codigo_error': 'PREREQUISITO_NO_INSCRITO',
                            'materia_prerrequisito': {
                                'id': materia_prerrequisito.id,
                                'nombre': materia_prerrequisito.nombre,
                                'codigo': materia_prerrequisito.codigo
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # Es una vista tradicional
                        return JsonResponse({
                            'error': error_msg
                        }, status=400)
                
                # Verificar si ha aprobado el prerrequisito
                calificacion = Calificacion.objects.filter(
                    inscripcion=inscripcion_prerrequisito
                ).first()
                
                if not calificacion or calificacion.nota is None or calificacion.nota < 3.0:
                    error_msg = f"Debe aprobar la materia prerrequisito: {materia_prerrequisito.nombre} (nota >= 3.0)"
                    if hasattr(request, 'data'):
                        # Es una API REST
                        return Response({
                            'error': error_msg,
                            'codigo_error': 'PREREQUISITO_NO_APROBADO',
                            'materia_prerrequisito': {
                                'id': materia_prerrequisito.id,
                                'nombre': materia_prerrequisito.nombre,
                                'codigo': materia_prerrequisito.codigo,
                                'nota_actual': calificacion.nota if calificacion else None
                            }
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # Es una vista tradicional
                        return JsonResponse({
                            'error': error_msg
                        }, status=400)
            
            # Si todas las validaciones pasan, continuar con la vista
            return view_func(request, *args, **kwargs)
            
        except Exception as e:
            # Si hay algún error en la validación, registrarlo pero continuar
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en validación de prerrequisitos: {str(e)}")
            
            # Continuar con la vista original para que no se rompa el flujo
            return view_func(request, *args, **kwargs)
    
    return wrapper


def validate_credit_limits(view_func):
    """
    Decorador para validar límites de créditos por semestre.
    
    Este decorador verifica que el estudiante no exceda su límite
    de créditos permitidos por semestre.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Solo aplicar validación en métodos POST (inscripciones)
        if request.method != 'POST':
            return view_func(request, *args, **kwargs)
        
        try:
            from apps.users.models import User
            from apps.materias.models import Materia, Periodo
            from apps.inscripciones.models import Inscripcion
            
            # Obtener datos de la solicitud
            if hasattr(request, 'data'):
                data = request.data
            else:
                data = request.POST
            
            estudiante_id = data.get('estudiante_id') or data.get('estudiante')
            materia_id = data.get('materia_id') or data.get('materia')
            periodo_id = data.get('periodo_id') or data.get('periodo')
            
            # Si no se proporcionan los datos necesarios, continuar sin validar
            if not estudiante_id or not materia_id:
                return view_func(request, *args, **kwargs)
            
            # Verificar que existen
            try:
                estudiante = User.objects.get(id=estudiante_id, role='estudiante')
                materia = Materia.objects.get(id=materia_id)
                
                # Si no se especifica período, usar el activo
                if periodo_id:
                    periodo = Periodo.objects.get(id=periodo_id)
                else:
                    periodo = Periodo.objects.filter(activo=True).first()
                    
                if not periodo:
                    return view_func(request, *args, **kwargs)
                    
            except (User.DoesNotExist, Materia.DoesNotExist, Periodo.DoesNotExist):
                return view_func(request, *args, **kwargs)
            
            # Calcular créditos actuales del estudiante en el período
            from django.db import models
            creditos_actuales = Inscripcion.objects.filter(
                estudiante=estudiante,
                periodo=periodo
            ).aggregate(
                total=models.Sum('materia__creditos')
            )['total'] or 0
            
            # Obtener límite de créditos del estudiante (por defecto 20)
            limite_creditos = getattr(estudiante.profile, 'creditos_maximos_semestre', 20) if hasattr(estudiante, 'profile') else 20
            
            # Verificar si agregar esta materia excede el límite
            if creditos_actuales + materia.creditos > limite_creditos:
                error_msg = f"Excede el límite de créditos por semestre. Actual: {creditos_actuales}, Límite: {limite_creditos}, Materia: {materia.creditos}"
                if hasattr(request, 'data'):
                    return Response({
                        'error': error_msg,
                        'codigo_error': 'LIMITE_CREDITOS_EXCEDIDO',
                        'creditos_actuales': creditos_actuales,
                        'creditos_materia': materia.creditos,
                        'limite_creditos': limite_creditos
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return JsonResponse({
                        'error': error_msg
                    }, status=400)
            
            # Si pasa la validación, continuar
            return view_func(request, *args, **kwargs)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en validación de límites de créditos: {str(e)}")
            return view_func(request, *args, **kwargs)
    
    return wrapper 