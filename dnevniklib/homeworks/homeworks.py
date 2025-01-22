from dnevniklib.student import Student
from requests import get
from dnevniklib.customtypes import Homework as HomeworkType
import json
from datetime import date, timedelta
from dnevniklib.utils import utils


class Homeworks:
    def __init__(self, student: Student):
        self.student = student

    def get_homework_by_date(self):
        res = []
        dt = date.today()
        dt_start = utils.Utils.get_normal_date(dt.year, dt.month, dt.day)
        dt_2 = date.today().__add__(timedelta(days=7))
        dt_end = utils.Utils.get_normal_date(dt_2.year, dt_2.month, dt_2.day)
        try:
            response = get(
                f"https://school.mos.ru/api/family/web/v1/homeworks?from={dt_start}&to={dt_end}&student_id={self.student.id}",
                headers={
                    "Auth-Token": self.student.token,
                    "X-Mes-Subsystem": "familyweb"
                }
            )
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response content: {response.text}")
                return res
            response_json = response.json()
            if "payload" in response_json:
                for homework in response_json["payload"]:
                    res.append(
                        HomeworkType(
                            id=homework["homework_entry_student_id"],
                            description=homework["description"],
                            subject_id=homework["subject_id"],
                            subject_name=homework["subject_name"],
                            created_at=homework["date_prepared_for"][:10],
                            is_done=homework["is_done"]
                        )
                    )
            else:
                    print("Error: 'payload' not found in response JSON")
        except json.JSONDecodeError:
            print("Error: Response is not valid JSON.")
            print(f"Response content: {response.text}")
        except Exception as e:
            print(f"An error occurred: {e}")
        return res