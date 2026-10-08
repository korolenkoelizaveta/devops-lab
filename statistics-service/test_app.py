import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app as service

client = TestClient(service.app)

def set_django(monkeypatch, data_by_path):
    async def fake_get(request, *paths):
        return tuple(data_by_path[p] for p in paths)
    monkeypatch.setattr(service, 'get_django_data', fake_get)

def test_users_admin_and_guest(monkeypatch):
    for authenticated in (True, False):
        set_django(monkeypatch, {
            '/api/userprofile/info/': {'is_authenticated': authenticated, 'is_admin': authenticated, 'role': 'admin' if authenticated else None},
            '/api/users/': [
                {'id': 1, 'name': 'X', 'role': 'client'},
                {'id': 2, 'name': 'Y', 'role': 'trainer'},
                {'id': 5, 'name': 'Z', 'role': 'client'},
            ],
        })
        res=client.get('/api/users/stats/')
        assert res.status_code == 200, res.text
        assert res.json() == {'count':3,'clients':2,'trainers':1,'min_id':1,'max_id':5,'avg_id':8/3}

def test_users_client_trainer_and_no_role(monkeypatch):
    for role, expected in (
        ('client', {'count':2,'clients':0,'trainers':2}),
        ('trainer', {'count':2,'clients':2,'trainers':0}),
        (None, {'count':0,'clients':0,'trainers':0}),
    ):
        set_django(monkeypatch, {
            '/api/userprofile/info/': {'is_authenticated': True, 'is_admin': False, 'role': role},
            '/api/users/': [{'id':1,'role':'client'}, {'id':2,'role':'trainer'}, {'id':3,'role':'client'}, {'id':4,'role':'trainer'}]
        })
        data=client.get('/api/users/stats/').json()
        for key, val in expected.items():
            assert data[key] == val
        assert data['avg_id'] is None

def test_membershiptypes_distinct_users(monkeypatch):
    set_django(monkeypatch, {
        '/api/membershiptype/': [{'id':2,'type':'Monthly'}, {'id':4,'type':'Annual'}, {'id':5,'type':'Empty'}],
        '/api/membership/': [
            {'membership_type':2,'client':8,'is_active':True},
            {'membership_type':2,'client':8,'is_active':False},
            {'membership_type':2,'client':9,'is_active':True},
            {'membership_type':4,'client':8,'is_active':True},
        ]
    })
    assert client.get('/api/membershiptype/stats/').json() == [
        {'id':2,'type':'Monthly','users_count':2},
        {'id':4,'type':'Annual','users_count':1},
        {'id':5,'type':'Empty','users_count':0},
    ]

def test_membership_stats(monkeypatch):
    set_django(monkeypatch, {'/api/membership/': [
        {'is_active':True},{'is_active':True},{'is_active':False}
    ]})
    assert client.get('/api/membership/stats/').json() == {'count':3,'active':2,'inactive':1}

def workout_rows():
    now=datetime.now(timezone.utc)
    iso=lambda d: d.isoformat()
    return [
        {'id':1,'client':1,'trainer':3,'session_date':iso(now-timedelta(days=1))},
        {'id':2,'client':1,'trainer':3,'session_date':iso(now+timedelta(days=3))},
        {'id':3,'client':2,'trainer':4,'session_date':iso(now-timedelta(days=10))},
    ]

def test_workout_admin_client_trainer(monkeypatch):
    users=[{'id':1,'name':'Client A'}, {'id':2,'name':'Client B'}, {'id':3,'name':'Trainer A'}, {'id':4,'name':'Trainer B'}]
    for role, expected in [
        ('admin', {'avg_per_client':1.5,'top_trainer_name':'Trainer A','top_client_name':'Client A'}),
        ('client', {'avg_per_client':0.0,'top_trainer_name':'Trainer A','top_client_name':None}),
        ('trainer', {'avg_per_client':1.5,'top_trainer_name':None,'top_client_name':'Client A'}),
    ]:
        set_django(monkeypatch, {
            '/api/userprofile/info/': {'is_authenticated':True, 'is_admin':role=='admin','role':role},
            '/api/workoutsession/':workout_rows(),
            '/api/users/':users
        })
        res=client.get('/api/workoutsession/stats/')
        assert res.status_code == 200, res.text
        data=res.json()
        assert (data['total'],data['last_7_days'],data['upcoming'])==(3,1,1)
        for k,v in expected.items(): assert data[k] == v

def test_workout_unlinked_user_returns_empty(monkeypatch):
    set_django(monkeypatch, {
        '/api/userprofile/info/': {'is_authenticated':True,'is_admin':False,'role':None},
        '/api/workoutsession/':[], '/api/users/':[]
    })
    assert client.get('/api/workoutsession/stats/').json() == service._empty_workout_stats()

def test_health():
    assert client.get('/health').json() == {'status':'ok'}
