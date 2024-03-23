import re
from typing import Dict, List

import requests


def extract_user_data(response: Dict) -> List[Dict]:
    customer_info = []
    for customer in response.get("data", []):
        id = customer["object_id"]
        first_name = re.sub(r"<[^>]+>", "", customer.get("first_name", ""))
        last_name = re.sub(r"<[^>]+>", "", customer.get("last_name", ""))
        phone = customer.get("phone", "")
        email = customer.get("email", "")
        customer_info.append(
            {
                "id": id,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "email": email,
            }
        )
    return customer_info


def fetch_punchpass_user_data(email: str, cookies: Dict[str, str]) -> Dict:
    url = f"https://app.punchpass.com/a/customers.json?columns[3][data]=email&columns[3][searchable]=true&columns[3][orderable]=true&columns[3][search][value]={email}&start=0&length=1"

    session = requests.Session()
    session.cookies.update(cookies)

    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

    return data
