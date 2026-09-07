from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from gym.models import User, MembershipType, Membership, WorkoutSession


class Tests(TestCase):

    def setUp(self):
        AuthUser = get_user_model()
        self.admin = AuthUser.objects.create_superuser(
            username="admin_test",
            password="admin123"
        )

        self.api = APIClient()
        self.api.force_authenticate(user=self.admin)

        self.client_user = User.objects.create(
            name="Иван Иванов",
            role=User.Role.CLIENT,
            phone="+79990000001"
        )
        
        self.trainer = User.objects.create(
            name="Петр Петров",
            role=User.Role.TRAINER,
            specialization="Фитнес"
        )

        self.membership_type = MembershipType.objects.create(
            type="Месячный",
            description="Абонемент на один месяц"
        )

        self.membership = Membership.objects.create(
            client=self.client_user,
            membership_type=self.membership_type,
            is_active=True,
            owner=self.admin
        )

        self.workout = WorkoutSession.objects.create(
            client=self.client_user,
            trainer=self.trainer,
            session_date=timezone.now() + timedelta(days=1)
        )

    def test_01_create_client(self):
        response = self.api.post(
            reverse("users-list"),
            {
                "name": "Новый клиент",
                "role": "client",
                "phone": "+79991111111"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.filter(
                name="Новый клиент",
                role=User.Role.CLIENT
            ).exists()
        )

    def test_02_read_client(self):
        response = self.api.get(
            reverse("users-detail", args=[self.client_user.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Иван Иванов")
        self.assertEqual(response.data["role"], "client")

    def test_03_update_client(self):
        response = self.api.patch(
            reverse("users-detail", args=[self.client_user.id]),
            {
                "name": "Иван Иванов Обновленный",
                "phone": "+79992222222"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.client_user.refresh_from_db()
        self.assertEqual(
            self.client_user.name,
            "Иван Иванов Обновленный"
        )
        self.assertEqual(
            self.client_user.phone,
            "+79992222222"
        )

    def test_04_delete_client(self):
        client_id = self.client_user.id

        response = self.api.delete(
            reverse("users-detail", args=[client_id])
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            User.objects.filter(id=client_id).exists()
        )

    def test_05_create_trainer(self):
        response = self.api.post(
            reverse("users-list"),
            {
                "name": "Новый тренер",
                "role": "trainer",
                "specialization": "Силовые тренировки"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.filter(
                name="Новый тренер",
                role=User.Role.TRAINER
            ).exists()
        )

    def test_06_read_trainer(self):
        response = self.api.get(
            reverse("users-detail", args=[self.trainer.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Петр Петров")
        self.assertEqual(response.data["role"], "trainer")

    def test_07_update_trainer(self):
        response = self.api.patch(
            reverse("users-detail", args=[self.trainer.id]),
            {
                "specialization": "Персональный тренинг"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.trainer.refresh_from_db()
        self.assertEqual(
            self.trainer.specialization,
            "Персональный тренинг"
        )

    def test_08_delete_trainer(self):
        trainer_id = self.trainer.id

        response = self.api.delete(
            reverse("users-detail", args=[trainer_id])
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            User.objects.filter(id=trainer_id).exists()
        )

    def test_09_create_membership_type(self):
        response = self.api.post(
            reverse("membershiptype-list"),
            {
                "type": "Годовой",
                "description": "Абонемент на один год"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            MembershipType.objects.filter(type="Годовой").exists()
        )

    def test_10_read_membership_type(self):
        response = self.api.get(
            reverse(
                "membershiptype-detail",
                args=[self.membership_type.id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "Месячный")

    def test_11_update_membership_type(self):
        response = self.api.patch(
            reverse(
                "membershiptype-detail",
                args=[self.membership_type.id]
            ),
            {
                "type": "Месячный плюс"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.membership_type.refresh_from_db()
        self.assertEqual(
            self.membership_type.type,
            "Месячный плюс"
        )

    def test_12_delete_membership_type(self):
        membership_type_id = self.membership_type.id

        response = self.api.delete(
            reverse(
                "membershiptype-detail",
                args=[membership_type_id]
            )
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            MembershipType.objects.filter(
                id=membership_type_id
            ).exists()
        )

    def test_13_create_membership(self):
        response = self.api.post(
            reverse("membership-list"),
            {
                "client": self.client_user.id,
                "membership_type": self.membership_type.id,
                "is_active": True
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            Membership.objects.filter(
                client=self.client_user
            ).count(),
            2
        )

    def test_14_read_membership(self):
        response = self.api.get(
            reverse(
                "membership-detail",
                args=[self.membership.id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["client"],
            self.client_user.id
        )

    def test_15_update_membership(self):
        response = self.api.patch(
            reverse(
                "membership-detail",
                args=[self.membership.id]
            ),
            {
                "is_active": False
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.membership.refresh_from_db()
        self.assertFalse(self.membership.is_active)

    def test_16_delete_membership(self):
        membership_id = self.membership.id

        response = self.api.delete(
            reverse(
                "membership-detail",
                args=[membership_id]
            )
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Membership.objects.filter(
                id=membership_id
            ).exists()
        )

    def test_17_create_workout(self):
        session_date = timezone.now() + timedelta(days=2)

        response = self.api.post(
            reverse("workoutsession-list"),
            {
                "client": self.client_user.id,
                "trainer": self.trainer.id,
                "session_date": session_date.isoformat()
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            WorkoutSession.objects.count(),
            2
        )

    def test_18_read_workout(self):
        response = self.api.get(
            reverse(
                "workoutsession-detail",
                args=[self.workout.id]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["client"],
            self.client_user.id
        )
        self.assertEqual(
            response.data["trainer"],
            self.trainer.id
        )

    def test_19_update_workout(self):
        new_date = timezone.now() + timedelta(days=5)

        response = self.api.patch(
            reverse(
                "workoutsession-detail",
                args=[self.workout.id]
            ),
            {
                "session_date": new_date.isoformat()
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.workout.refresh_from_db()

        self.assertEqual(
            self.workout.session_date.replace(microsecond=0),
            new_date.replace(microsecond=0)
        )

    def test_20_delete_workout(self):
        workout_id = self.workout.id

        response = self.api.delete(
            reverse(
                "workoutsession-detail",
                args=[workout_id]
            )
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            WorkoutSession.objects.filter(
                id=workout_id
            ).exists()
        )