from django.apps import AppConfig

class InfrastructureConfig(AppConfig):
    name = 'core.infrastructure'
    
    def ready(self):
        import core.infrastructure.signals

