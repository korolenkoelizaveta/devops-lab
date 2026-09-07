from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import timedelta, datetime

from gym.models import User, MembershipType, Membership, WorkoutSession


class Command(BaseCommand):
    help = "Генерирует тестовые данные для User, MembershipType, Membership, WorkoutSession"

    def handle(self, *args, **options):
        fake = Faker("ru_RU")

        self.stdout.write(self.style.WARNING("Генерация данных началась..."))

        clients = []
        trainers = []

        for _ in range(600):
            clients.append(User.objects.create(
                name=fake.name(),
                role="client",
                phone=fake.phone_number(),
            ))

        for _ in range(100):
            trainers.append(User.objects.create(
                name=fake.name(),
                role="trainer",
                phone=fake.phone_number(),
                specialization=random.choice(["Фитнес", "Кроссфит", "Йога", "Пилатес"]),
            ))

        self.stdout.write(self.style.SUCCESS(f"Создано клиентов: {len(clients)}"))
        self.stdout.write(self.style.SUCCESS(f"Создано тренеров: {len(trainers)}"))

        membership_types = []
        type_names = ["Месячный", "3 месяца", "Годовой", "Разовое посещение", "Безлимит"]

        for name in type_names:
            membership_types.append(MembershipType.objects.create(
                type=name,
                description=fake.sentence(),
            ))

        self.stdout.write(self.style.SUCCESS("Типы абонементов созданы."))

        memberships = []

        for c in clients:
            for _ in range(random.randint(1, 3)):
                memberships.append(Membership.objects.create(
                    client=c,
                    membership_type=random.choice(membership_types),
                    is_active=random.choice([True, False]),
                    owner=None, 
                ))

        self.stdout.write(self.style.SUCCESS(f"Создано абонементов: {len(memberships)}"))

        workout_sessions = []

        for _ in range(1000):
            client = random.choice(clients)
            trainer = random.choice(trainers)
            dt = datetime.now() - timedelta(days=random.randint(0, 365))

            workout_sessions.append(
                WorkoutSession.objects.create(
                    client=client,
                    trainer=trainer,
                    session_date=dt, 
                )
            )

        self.stdout.write(self.style.SUCCESS(
            f"Создано тренировок: {len(workout_sessions)}"
        ))

        self.stdout.write(self.style.SUCCESS("Генерация завершена успешно!"))
