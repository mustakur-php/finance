from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Send visit and event reminders via Telegram and Email'

    def handle(self, *args, **kwargs):
        from visits.tasks import send_visit_reminders, send_event_reminders
        r1 = send_visit_reminders()
        r2 = send_event_reminders()
        self.stdout.write(f"{r1} | {r2}")
