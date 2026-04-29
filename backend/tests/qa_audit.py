"""End-to-end QA audit of the running GYM backend.

Run inside the backend container: `python -m tests.qa_audit`.
Hits the live FastAPI app via httpx ASGI transport (no network needed).
"""
from __future__ import annotations

import asyncio
import json
import secrets
import sys
import traceback
from datetime import date
from typing import Any

import httpx

from app.main import app

API = "/api"


class Step:
    def __init__(self, name: str) -> None:
        self.name = name
        self.passed = False
        self.message = ""

    def ok(self, msg: str = "") -> None:
        self.passed = True
        self.message = msg

    def fail(self, msg: str) -> None:
        self.passed = False
        self.message = msg


class Audit:
    def __init__(self) -> None:
        self.steps: list[Step] = []

    def step(self, name: str) -> Step:
        s = Step(name)
        self.steps.append(s)
        return s

    def report(self) -> int:
        passed = sum(1 for s in self.steps if s.passed)
        failed = [s for s in self.steps if not s.passed]
        print()
        print("=" * 70)
        print(f"QA AUDIT: {passed}/{len(self.steps)} passed")
        print("=" * 70)
        for s in self.steps:
            mark = "PASS" if s.passed else "FAIL"
            print(f"[{mark}] {s.name}")
            if s.message and not s.passed:
                print(f"        FAIL >> {s.message}")
            elif s.message and s.passed:
                print(f"        info: {s.message}")
        return 1 if failed else 0


def _ensure(audit: Audit, label: str, condition: bool, fail_msg: str = "", ok_msg: str = "") -> Step:
    s = audit.step(label)
    if condition:
        s.ok(ok_msg)
    else:
        s.fail(fail_msg)
    return s


async def _signup_and_login(client: httpx.AsyncClient, audit: Audit) -> tuple[str, str, dict]:
    rid = secrets.token_hex(4)
    email = f"qa-{rid}@example.com"
    password = "QaPassw0rd!"
    full_name = f"QA User {rid}"
    r = await client.post(f"{API}/auth/register", json={
        "email": email, "password": password, "full_name": full_name,
    })
    _ensure(audit, "auth: register new user", r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")
    r = await client.post(f"{API}/auth/login", json={"email": email, "password": password})
    _ensure(audit, "auth: login returns tokens", r.status_code == 200 and "access_token" in r.json(),
            fail_msg=f"{r.status_code} {r.text}")
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = await client.get(f"{API}/auth/me", headers=headers)
    _ensure(audit, "auth: /me with token", r.status_code == 200 and r.json()["email"] == email,
            fail_msg=f"{r.status_code} {r.text}")
    return tokens["access_token"], tokens["refresh_token"], {"email": email, "password": password, "id": r.json()["id"]}


async def _negative_auth(client: httpx.AsyncClient, audit: Audit) -> None:
    r = await client.post(f"{API}/auth/login", json={"email": "noone-real@example.com", "password": "Wrong0Pass!!"})
    _ensure(audit, "auth: invalid credentials returns 401", r.status_code == 401)
    r = await client.post(f"{API}/auth/register", json={"email": "bad", "password": "x"})
    _ensure(audit, "auth: bad email rejected (422)", r.status_code == 422)
    r = await client.post(f"{API}/auth/register", json={"email": "ok@x.com", "password": "short"})
    _ensure(audit, "auth: short password rejected (422)", r.status_code == 422)
    r = await client.get(f"{API}/auth/me")
    _ensure(audit, "auth: /me without token returns 401", r.status_code == 401)
    r = await client.get(f"{API}/auth/me", headers={"Authorization": "Bearer not-a-token"})
    _ensure(audit, "auth: /me with bad token returns 401", r.status_code == 401)


async def _generate(client: httpx.AsyncClient, headers: dict, body: dict) -> httpx.Response:
    return await client.post(f"{API}/workouts/generate", headers=headers, json=body)


def _all_exercise_ids(plan: dict) -> list[int]:
    ids: list[int] = []
    for d in plan.get("days", []):
        for e in d.get("exercises", []):
            ids.append(e["exercise"]["id"])
    return ids


def _all_exercise_equipment(plan: dict) -> list[str]:
    out: list[str] = []
    for d in plan.get("days", []):
        for e in d.get("exercises", []):
            out.append(e["exercise"]["equipment"])
    return out


def _all_contraindications(plan: dict) -> list[list[str]]:
    out: list[list[str]] = []
    for d in plan.get("days", []):
        for e in d.get("exercises", []):
            out.append(e["exercise"].get("contraindications") or [])
    return out


async def _bodyweight_only(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    body = {
        "weight_kg": 75, "height_cm": 180, "age": 28,
        "experience": "intermediate", "goal": "muscle_gain",
        "equipment": ["bodyweight"], "injuries": [],
        "days_per_week": 3,
    }
    r = await _generate(client, headers, body)
    s = _ensure(audit, "generator: bodyweight-only HTTP 201", r.status_code == 201,
                fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    plan = r.json()
    eqs = _all_exercise_equipment(plan)
    bad = [e for e in eqs if e != "bodyweight"]
    _ensure(audit, "generator: bodyweight-only -> ZERO non-bodyweight exercises",
            not bad, fail_msg=f"non-bodyweight equipment leaked: {bad[:5]}",
            ok_msg=f"{len(eqs)} exercises, all bodyweight")
    locations = {tuple(plan["params"].get("equipment") or [])}
    _ensure(audit, "generator: params.equipment reflects request",
            ("bodyweight",) in locations,
            fail_msg=f"params.equipment={plan['params'].get('equipment')}")


async def _gym_full(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    body = {
        "weight_kg": 80, "height_cm": 178, "age": 30,
        "experience": "advanced", "goal": "muscle_gain",
        "equipment": ["barbell", "dumbbell", "machine"], "injuries": [],
        "days_per_week": 5,
    }
    r = await _generate(client, headers, body)
    s = _ensure(audit, "generator: gym full HTTP 201", r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    plan = r.json()
    eqs = _all_exercise_equipment(plan)
    _ensure(audit, "generator: gym full -> uses gym equipment, no bodyweight slop",
            all(eq in {"barbell", "dumbbell", "machine"} for eq in eqs) and len(eqs) >= 5,
            fail_msg=f"unexpected equipment in plan: {set(eqs)}",
            ok_msg=f"{len(eqs)} exercises, equipment set: {sorted(set(eqs))}")
    cats: list[str] = []
    for d in plan["days"]:
        for e in d["exercises"]:
            cats.append(e["exercise"]["category"])
    _ensure(audit, "generator: gym full -> mix of compound + isolation",
            "compound" in cats and "isolation" in cats,
            fail_msg=f"only categories: {set(cats)}")


async def _injury_knees(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    body = {
        "weight_kg": 75, "height_cm": 178, "age": 35,
        "experience": "intermediate", "goal": "muscle_gain",
        "equipment": ["barbell", "dumbbell", "machine", "bodyweight"],
        "injuries": ["knees"], "days_per_week": 4,
    }
    r = await _generate(client, headers, body)
    s = _ensure(audit, "generator: knee injury HTTP 201", r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    plan = r.json()
    contras = _all_contraindications(plan)
    flat = {token for arr in contras for token in arr}
    bad = flat & {"knee", "deep_squat", "high_impact"}
    _ensure(audit, "generator: knees → NO exercises with knee/deep_squat/high_impact contras",
            not bad, fail_msg=f"unsafe contraindications still present: {bad}",
            ok_msg=f"{sum(len(d['exercises']) for d in plan['days'])} exercises, no knee-load")
    eqs = _all_exercise_equipment(plan)
    _ensure(audit, "generator: knees → still produced replacement exercises",
            len(eqs) >= 6, fail_msg=f"only {len(eqs)} exercises generated")


async def _beginner(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    body = {
        "weight_kg": 70, "height_cm": 170, "age": 22,
        "experience": "beginner", "goal": "general",
        "equipment": ["barbell", "dumbbell", "machine"],
        "injuries": [], "days_per_week": 3,
    }
    r = await _generate(client, headers, body)
    s = _ensure(audit, "generator: beginner HTTP 201", r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    plan = r.json()
    diffs: list[int] = []
    for d in plan["days"]:
        for e in d["exercises"]:
            diffs.append(e["exercise"]["difficulty"])
    _ensure(audit, "generator: beginner -> difficulty <= 3 (no advanced lifts)",
            all(d <= 3 for d in diffs), fail_msg=f"too-advanced lifts: {[d for d in diffs if d > 3]}",
            ok_msg=f"max difficulty in plan: {max(diffs) if diffs else 'n/a'}")
    _ensure(audit, "generator: beginner -> split is full_body",
            plan["split_type"] == "full_body",
            fail_msg=f"split_type={plan['split_type']}")


async def _advanced_strength(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    body = {
        "weight_kg": 90, "height_cm": 180, "age": 32,
        "experience": "advanced", "goal": "strength",
        "equipment": ["barbell", "dumbbell", "machine"],
        "injuries": [], "days_per_week": 4,
    }
    r = await _generate(client, headers, body)
    s = _ensure(audit, "generator: advanced strength HTTP 201", r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    plan = r.json()
    work_reps_min: list[int] = []
    work_reps_max: list[int] = []
    for d in plan["days"]:
        for e in d["exercises"]:
            if e.get("is_test_set"):
                continue
            work_reps_min.append(e["reps_min"])
            work_reps_max.append(e["reps_max"])
    if work_reps_min:
        _ensure(audit, "generator: advanced strength → working sets in 3-10 rep window",
                all(rmin >= 3 for rmin in work_reps_min) and max(work_reps_max) <= 10,
                fail_msg=f"reps_min: {work_reps_min[:8]}, reps_max: {work_reps_max[:8]}",
                ok_msg=f"min={min(work_reps_min)} max={max(work_reps_max)}")


async def _edge_cases(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    body = {"weight_kg": 1, "height_cm": 1, "age": 5,
            "experience": "beginner", "goal": "general",
            "equipment": [], "injuries": [], "days_per_week": 4}
    r = await _generate(client, headers, body)
    _ensure(audit, "generator: extreme small numbers rejected (422)", r.status_code == 422)

    body = {"weight_kg": 75, "height_cm": 180, "age": 25,
            "experience": "muscle_god", "goal": "muscle_gain",
            "equipment": ["barbell"], "injuries": [], "days_per_week": 4}
    r = await _generate(client, headers, body)
    _ensure(audit, "generator: invalid experience enum rejected (422)", r.status_code == 422)

    body = {"weight_kg": 75, "height_cm": 180, "age": 25,
            "experience": "beginner", "goal": "general",
            "equipment": ["barbell"], "injuries": [], "days_per_week": 99}
    r = await _generate(client, headers, body)
    _ensure(audit, "generator: days_per_week=99 rejected (422)", r.status_code == 422)

    body = {"weight_kg": 75, "height_cm": 180, "age": 25,
            "experience": "beginner", "goal": "general",
            "equipment": ["nuclear_press"], "injuries": ["bigfoot"], "days_per_week": 3}
    r = await _generate(client, headers, body)
    _ensure(audit, "generator: unknown equipment string falls back gracefully (201)",
            r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")


async def _profile(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    payload = {
        "full_name": "QA Tester",
        "sex": "male",
        "birth_date": "1995-01-01",
        "height_cm": 180,
        "weight_kg": 78,
        "experience": "intermediate",
        "goal": "muscle_gain",
        "global_restrictions": ["KNEES", "knees", "shoulders", "  "],
        "priority_exercise_ids": [1, 2, 2, -3, 0, 4],
    }
    r = await client.put(f"{API}/users/me", headers=headers, json=payload)
    s = _ensure(audit, "profile: PUT /me with new profile fields", r.status_code == 200,
                fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    me = r.json()
    _ensure(audit, "profile: restrictions normalized + deduped",
            me["global_restrictions"] == ["knees", "shoulders"],
            fail_msg=f"got: {me['global_restrictions']}")
    _ensure(audit, "profile: priority_exercise_ids deduped + positive only",
            me["priority_exercise_ids"] == [1, 2, 4],
            fail_msg=f"got: {me['priority_exercise_ids']}")

    bad = {**payload, "weight_kg": -5}
    r = await client.put(f"{API}/users/me", headers=headers, json=bad)
    _ensure(audit, "profile: negative weight rejected (422)", r.status_code == 422)

    bad = {**payload, "height_cm": 9999}
    r = await client.put(f"{API}/users/me", headers=headers, json=bad)
    _ensure(audit, "profile: height=9999 rejected (422)", r.status_code == 422)


async def _full_questionnaire_flow(client: httpx.AsyncClient, headers: dict, audit: Audit) -> int | None:
    payload = {
        "sex": "male", "age": 27, "height_cm": 178, "weight_kg": 76,
        "experience": "intermediate", "goal": "muscle_gain",
        "location": "gym",
        "equipment": ["barbell", "dumbbell", "machine"],
        "injuries": ["shoulders"],
        "days_per_week": 4,
        "available_days": ["mon", "tue", "thu", "fri"],
        "notes": "тестовая анкета",
        "priority_exercise_ids": [1, 2, 3],
        "session_duration_min": 90,
        "training_structure": "upper_lower",
        "periodization": "dup",
        "cycle_length_weeks": 6,
    }
    r = await client.post(f"{API}/workouts/questionnaires", headers=headers, json=payload)
    ok = r.status_code in (200, 201)
    s = _ensure(audit, "questionnaire: create with full config", ok, fail_msg=f"{r.status_code} {r.text}")
    if not ok:
        return None
    qid = r.json()["id"]
    r = await client.post(f"{API}/workouts/questionnaires/{qid}/generate", headers=headers)
    s = _ensure(audit, "questionnaire: generate plan from saved questionnaire", r.status_code == 201,
                fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return qid
    plan = r.json()
    pp = plan["params"]
    _ensure(audit, "questionnaire: params.session_duration_min=90", pp.get("session_duration_min") == 90)
    _ensure(audit, "questionnaire: params.training_structure='upper_lower'",
            pp.get("training_structure") == "upper_lower")
    _ensure(audit, "questionnaire: params.periodization='dup'", pp.get("periodization") == "dup")
    _ensure(audit, "questionnaire: params.cycle_length_weeks=6", pp.get("cycle_length_weeks") == 6)
    stored_priority = set(pp.get("priority_exercise_ids") or [])
    _ensure(audit, "questionnaire: priority_exercise_ids include questionnaire input (merged with profile)",
            {1, 2, 3}.issubset(stored_priority),
            fail_msg=f"got: {stored_priority}",
            ok_msg=f"merged: {sorted(stored_priority)}")
    weeks = {d["week_index"] for d in plan["days"]}
    _ensure(audit, "questionnaire: cycle_length_weeks=6 produces 6 unique week_index",
            weeks == {1, 2, 3, 4, 5, 6}, fail_msg=f"weeks: {sorted(weeks)}")
    return qid


async def _editing(client: httpx.AsyncClient, headers: dict, audit: Audit) -> dict | None:
    body = {
        "weight_kg": 75, "height_cm": 178, "age": 28,
        "experience": "intermediate", "goal": "muscle_gain",
        "equipment": ["barbell", "dumbbell", "machine"], "injuries": [],
        "days_per_week": 3,
    }
    r = await _generate(client, headers, body)
    if r.status_code != 201:
        audit.step("editing: prep generate plan").fail(f"{r.status_code} {r.text}")
        return None
    plan = r.json()
    plan_id = plan["id"]
    target_day = next(d for d in plan["days"] if not d["is_rest"])
    day_id = target_day["id"]

    r = await client.get(f"{API}/exercises", headers=headers)
    pool = r.json()
    chosen = [ex for ex in pool if ex["equipment"] in {"barbell", "dumbbell"} and ex["is_active"]][:3]
    if len(chosen) < 3:
        audit.step("editing: prep load exercises").fail("not enough exercises in catalog")
        return None
    payload = {
        "exercises": [
            {"exercise_id": chosen[0]["id"], "sets": 3, "reps_min": 8, "reps_max": 10, "rest_sec": 90},
            {"exercise_id": chosen[1]["id"], "sets": 4, "reps_min": 6, "reps_max": 8, "rest_sec": 120, "weight_kg": 50.5},
        ],
    }
    r = await client.put(f"{API}/workouts/{plan_id}/days/{day_id}", headers=headers, json=payload)
    s = _ensure(audit, "editing: update day with new exercises (200)", r.status_code == 200,
                fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return None
    updated = r.json()
    new_day = next(d for d in updated["days"] if d["id"] == day_id)
    _ensure(audit, "editing: day has exactly 2 exercises after edit", len(new_day["exercises"]) == 2)
    _ensure(audit, "editing: weight_kg=50.5 persisted",
            any(e["weight_kg"] == 50.5 for e in new_day["exercises"]))
    user_edits = updated["params"]["user_edits"]
    _ensure(audit, "editing: prefer/avoid lists tracked",
            "prefer_exercise_ids" in user_edits and "avoid_exercise_ids" in user_edits)

    bad = {"exercises": [{"exercise_id": 999999, "sets": 3, "reps_min": 8, "reps_max": 10}]}
    r = await client.put(f"{API}/workouts/{plan_id}/days/{day_id}", headers=headers, json=bad)
    _ensure(audit, "editing: invalid exercise_id rejected (404)", r.status_code == 404)

    bad = {"exercises": [
        {"exercise_id": chosen[0]["id"], "sets": 0, "reps_min": 8, "reps_max": 10},
    ]}
    r = await client.put(f"{API}/workouts/{plan_id}/days/{day_id}", headers=headers, json=bad)
    _ensure(audit, "editing: sets=0 rejected (422)", r.status_code == 422)

    bad = {"exercises": [
        {"exercise_id": chosen[0]["id"], "sets": 3, "reps_min": 8, "reps_max": 10, "weight_kg": -5},
    ]}
    r = await client.put(f"{API}/workouts/{plan_id}/days/{day_id}", headers=headers, json=bad)
    _ensure(audit, "editing: weight=-5 rejected (422)", r.status_code == 422)

    bad = {"exercises": [
        {"exercise_id": chosen[0]["id"], "sets": 3, "reps_min": 12, "reps_max": 6},
    ]}
    r = await client.put(f"{API}/workouts/{plan_id}/days/{day_id}", headers=headers, json=bad)
    _ensure(audit, "editing: reps_min > reps_max rejected (422)", r.status_code == 422,
            fail_msg=f"{r.status_code} {r.text}")

    bad = {"exercises": [
        {"exercise_id": chosen[0]["id"], "sets": 3, "reps_min": 8, "reps_max": 10, "weight_kg": 9999},
    ]}
    r = await client.put(f"{API}/workouts/{plan_id}/days/{day_id}", headers=headers, json=bad)
    _ensure(audit, "editing: weight=9999 rejected (422)", r.status_code == 422)

    return {"plan_id": plan_id, "day_id": day_id, "exercises": chosen}


async def _isolation_between_users(client: httpx.AsyncClient, audit: Audit) -> None:
    a_token, _, _ = await _signup_and_login(client, audit)
    b_token, _, _ = await _signup_and_login(client, audit)
    h_a = {"Authorization": f"Bearer {a_token}"}
    h_b = {"Authorization": f"Bearer {b_token}"}
    body = {"weight_kg": 75, "height_cm": 178, "age": 28,
            "experience": "intermediate", "goal": "muscle_gain",
            "equipment": ["barbell"], "injuries": [], "days_per_week": 3}
    r = await _generate(client, h_a, body)
    if r.status_code != 201:
        audit.step("isolation: failed to seed plan A").fail(r.text)
        return
    plan_a = r.json()
    r = await client.get(f"{API}/workouts/{plan_a['id']}", headers=h_b)
    _ensure(audit, "isolation: user B cannot read user A's plan (404)", r.status_code == 404)
    day_a = next(d for d in plan_a["days"] if not d["is_rest"])
    r = await client.put(f"{API}/workouts/{plan_a['id']}/days/{day_a['id']}",
                         headers=h_b, json={"exercises": []})
    _ensure(audit, "isolation: user B cannot edit user A's day (404)", r.status_code == 404)


async def _nutrition(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    payload = {"sex": "male", "age": 28, "weight_kg": 80, "height_cm": 180,
               "activity": "moderate", "goal": "maintain"}
    r = await client.post(f"{API}/nutrition/targets", headers=headers, json=payload)
    s = _ensure(audit, "nutrition: targets calculator returns 200", r.status_code == 200,
                fail_msg=f"{r.status_code} {r.text}")
    if s.passed:
        data = r.json()
        bmr_expected = round(10 * 80 + 6.25 * 180 - 5 * 28 + 5)
        _ensure(audit, "nutrition: BMR matches Mifflin-St Jeor formula",
                data["bmr"] == bmr_expected, fail_msg=f"bmr={data['bmr']} expected {bmr_expected}")
        _ensure(audit, "nutrition: TDEE = BMR * 1.55 (moderate)",
                abs(data["tdee"] - data["bmr"] * 1.55) < 1.0)
        _ensure(audit, "nutrition: target_calories ~ TDEE (maintain mult=1.0)",
                abs(data["target_calories"] - data["tdee"]) < 1.0)
        _ensure(audit, "nutrition: protein grams = 80 * 1.8 = 144",
                abs(data["protein"]["grams"] - 144) < 0.5)

    bad = {**payload, "weight_kg": -10}
    r = await client.post(f"{API}/nutrition/targets", headers=headers, json=bad)
    _ensure(audit, "nutrition: targets weight=-10 rejected (422)", r.status_code == 422)

    bad = {**payload, "weight_kg": 0}
    r = await client.post(f"{API}/nutrition/targets", headers=headers, json=bad)
    _ensure(audit, "nutrition: targets weight=0 rejected (422)", r.status_code == 422)

    bad = {**payload, "age": 5}
    r = await client.post(f"{API}/nutrition/targets", headers=headers, json=bad)
    _ensure(audit, "nutrition: targets age=5 rejected (422)", r.status_code == 422)

    today = date.today().isoformat()
    r = await client.post(f"{API}/meals", headers=headers, json={"date": today, "name": "Завтрак"})
    s = _ensure(audit, "meal: create breakfast", r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    meal_id = r.json()["id"]

    r = await client.post(f"{API}/meals", headers=headers, json={"date": today, "name": "   "})
    _ensure(audit, "meal: empty whitespace name rejected (422)", r.status_code == 422,
            fail_msg=f"{r.status_code} {r.text}")
    r = await client.post(f"{API}/meals", headers=headers, json={"date": today, "name": ""})
    _ensure(audit, "meal: empty string name rejected (422)", r.status_code == 422)

    r = await client.post(f"{API}/food-entries", headers=headers, json={
        "meal_id": meal_id, "name": "Куриная грудка",
        "protein_per_100g": 23, "fat_per_100g": 1.5, "carbs_per_100g": 0,
        "grams": 200,
    })
    s = _ensure(audit, "food entry: add chicken 200g", r.status_code == 201, fail_msg=f"{r.status_code} {r.text}")
    if s.passed:
        e = r.json()
        _ensure(audit, "food entry: protein 23/100 * 200 = 46",
                abs(e["calculated_protein"] - 46) < 0.5,
                fail_msg=f"got {e['calculated_protein']}")
        _ensure(audit, "food entry: kcal = 4P + 9F + 4C ≈ 197.5",
                abs(e["calories"] - (46 * 4 + 3 * 9 + 0)) < 1,
                fail_msg=f"got {e['calories']}")

    r = await client.post(f"{API}/food-entries", headers=headers, json={
        "meal_id": meal_id, "name": "Bad", "protein_per_100g": -1, "fat_per_100g": 0, "carbs_per_100g": 0, "grams": 100,
    })
    _ensure(audit, "food entry: negative protein rejected (422)", r.status_code == 422)

    r = await client.post(f"{API}/food-entries", headers=headers, json={
        "meal_id": meal_id, "name": "Bad", "protein_per_100g": 0, "fat_per_100g": 0, "carbs_per_100g": 0, "grams": 0,
    })
    _ensure(audit, "food entry: grams=0 rejected (422)", r.status_code == 422)

    r = await client.post(f"{API}/food-entries", headers=headers, json={
        "meal_id": meal_id, "name": "Bad", "protein_per_100g": 0, "fat_per_100g": 0, "carbs_per_100g": 0, "grams": -50,
    })
    _ensure(audit, "food entry: grams=-50 rejected (422)", r.status_code == 422)

    r = await client.post(f"{API}/food-entries", headers=headers, json={
        "meal_id": meal_id, "name": "X", "protein_per_100g": 9999, "fat_per_100g": 0, "carbs_per_100g": 0, "grams": 100,
    })
    _ensure(audit, "food entry: protein/100g=9999 rejected (422)", r.status_code == 422)

    r = await client.post(f"{API}/food-entries", headers=headers, json={
        "meal_id": 999999, "name": "X", "protein_per_100g": 1, "fat_per_100g": 0, "carbs_per_100g": 0, "grams": 100,
    })
    _ensure(audit, "food entry: meal not found returns 404", r.status_code == 404)

    r = await client.post(f"{API}/food-entries", headers=headers, json={
        "meal_id": meal_id, "name": "   ", "protein_per_100g": 1, "fat_per_100g": 0, "carbs_per_100g": 0, "grams": 100,
    })
    _ensure(audit, "food entry: whitespace-only name rejected (422)", r.status_code == 422)

    r = await client.get(f"{API}/nutrition/daily-summary", headers=headers, params={"date": today})
    _ensure(audit, "nutrition: daily-summary 200", r.status_code == 200)


async def _template_generate(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    """The new simplified flow: 4 questions -> 4-week plan, no auto-weights."""
    r = await client.post(f"{API}/workouts/template/generate", headers=headers, json={
        "goal": "muscle_gain",
        "days_per_week": 4,
        "training_structure": "upper_lower",
        "weeks": 4,
    })
    s = _ensure(audit, "template: upper_lower 4d generates 201", r.status_code == 201,
                fail_msg=f"{r.status_code} {r.text}")
    if not s.passed:
        return
    plan = r.json()
    weeks = sorted({d["week_index"] for d in plan["days"]})
    _ensure(audit, "template: plan has 4 distinct weeks", weeks == [1, 2, 3, 4],
            fail_msg=f"got weeks={weeks}")
    _ensure(audit, "template: 16 days for 4w x 4d/week", len(plan["days"]) == 16,
            fail_msg=f"got {len(plan['days'])} days")
    weights = [ex["weight_kg"] for d in plan["days"] for ex in d["exercises"]]
    _ensure(audit, "template: every exercise starts with weight_kg=null",
            all(w is None for w in weights), fail_msg="some weights are non-null")
    _ensure(audit, "template: plan picks upper-lower template",
            plan["params"].get("template_slug") == "upper-lower-4",
            fail_msg=f"slug={plan['params'].get('template_slug')}")

    target = plan["days"][0]["exercises"][0]
    r = await client.patch(
        f"{API}/workouts/exercises/{target['id']}/weight",
        headers=headers, json={"weight_kg": 82.5},
    )
    s = _ensure(audit, "template: PATCH weight 200", r.status_code == 200)
    if s.passed:
        _ensure(audit, "template: PATCH stores 82.5kg", r.json()["weight_kg"] == 82.5)

    r = await client.patch(
        f"{API}/workouts/exercises/{target['id']}/weight",
        headers=headers, json={"weight_kg": None},
    )
    _ensure(audit, "template: PATCH null clears weight",
            r.status_code == 200 and r.json()["weight_kg"] is None)

    r = await client.patch(
        f"{API}/workouts/exercises/{target['id']}/weight",
        headers=headers, json={"weight_kg": 9999},
    )
    _ensure(audit, "template: PATCH weight=9999 rejected (422)", r.status_code == 422)

    r = await client.patch(
        f"{API}/workouts/exercises/9999999/weight",
        headers=headers, json={"weight_kg": 50},
    )
    _ensure(audit, "template: PATCH unknown exercise -> 404", r.status_code == 404)

    for goal, days, struct, expected in [
        ("strength",    3, None,           "strength-3-4"),
        ("muscle_gain", 6, "split",        "push-pull-legs-6"),
        ("general",     3, "full_body",    "full-body-3"),
        ("muscle_gain", 5, "hypertrophy",  "hypertrophy-5"),
    ]:
        body: dict[str, object] = {"goal": goal, "days_per_week": days, "weeks": 4}
        if struct:
            body["training_structure"] = struct
        r = await client.post(f"{API}/workouts/template/generate", headers=headers, json=body)
        s = _ensure(audit, f"template: pick {goal}/{days}d/{struct} -> {expected}",
                    r.status_code == 201)
        if s.passed:
            slug = r.json()["params"].get("template_slug")
            _ensure(audit, f"template: {goal}/{days}d/{struct} slug match",
                    slug == expected, fail_msg=f"got {slug}")


async def _exercises_endpoint(client: httpx.AsyncClient, headers: dict, audit: Audit) -> None:
    r = await client.get(f"{API}/exercises", params={"equipment": "bodyweight"})
    s = _ensure(audit, "exercises: filter by equipment=bodyweight 200", r.status_code == 200)
    if s.passed:
        eqs = {ex["equipment"] for ex in r.json()}
        _ensure(audit, "exercises: filter equipment=bodyweight returns ONLY bodyweight",
                eqs == {"bodyweight"} or eqs == set(),
                fail_msg=f"contaminated set: {eqs}")
    r = await client.get(f"{API}/exercises", params={"muscle": "chest"})
    _ensure(audit, "exercises: filter by muscle=chest 200", r.status_code == 200)

    r = await client.get(f"{API}/exercises", params={"muscle": "tail"})
    _ensure(audit, "exercises: invalid muscle enum rejected (422)", r.status_code == 422)

    r = await client.get(f"{API}/exercises/9999999")
    _ensure(audit, "exercises: GET /9999999 returns 404", r.status_code == 404)


async def _security(client: httpx.AsyncClient, audit: Audit) -> None:
    payloads = [
        ("' OR 1=1 --", "sql"),
        ("'; DROP TABLE users; --", "sql"),
        ("<script>alert(1)</script>@example.com", "xss"),
    ]
    for value, kind in payloads:
        r = await client.post(f"{API}/auth/login", json={"email": value, "password": "anything"})
        _ensure(audit, f"security: {kind} payload in email -> 401/422 (no crash)",
                r.status_code in (401, 422), fail_msg=f"{r.status_code} {r.text}")

    r = await client.post(f"{API}/auth/refresh", json={"refresh_token": "abc.def.ghi"})
    _ensure(audit, "security: bogus refresh token returns 401", r.status_code == 401)

    r = await client.post(f"{API}/auth/refresh", json={"refresh_token": ""})
    _ensure(audit, "security: empty refresh token returns 401/422",
            r.status_code in (401, 422))

    r = await client.get(f"{API}/admin/stats", headers={"Authorization": "Bearer notvalid"})
    _ensure(audit, "security: admin endpoint with bad token returns 401",
            r.status_code in (401, 403, 404))


async def main() -> int:
    audit = Audit()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        try:
            r = await client.get(f"{API}/health")
            _ensure(audit, "health: /api/health returns 200", r.status_code == 200,
                    fail_msg=f"{r.status_code} {r.text}")

            await _negative_auth(client, audit)
            access, refresh, _user = await _signup_and_login(client, audit)
            r = await client.post(f"{API}/auth/refresh", json={"refresh_token": refresh})
            _ensure(audit, "auth: refresh produces new access token",
                    r.status_code == 200 and "access_token" in r.json())

            headers = {"Authorization": f"Bearer {access}"}
            await _profile(client, headers, audit)
            await _bodyweight_only(client, headers, audit)
            await _gym_full(client, headers, audit)
            await _injury_knees(client, headers, audit)
            await _beginner(client, headers, audit)
            await _advanced_strength(client, headers, audit)
            await _full_questionnaire_flow(client, headers, audit)
            await _editing(client, headers, audit)
            await _template_generate(client, headers, audit)
            await _isolation_between_users(client, audit)
            await _nutrition(client, headers, audit)
            await _exercises_endpoint(client, headers, audit)
            await _edge_cases(client, headers, audit)
            await _security(client, audit)
        except Exception as exc:
            print("UNEXPECTED EXCEPTION:")
            traceback.print_exc()
            audit.step("ABORT: unhandled exception").fail(str(exc))
    return audit.report()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
