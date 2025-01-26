import requests
import json
import sys

def get_instance_metadata(key=None):
    """
    Retrieves metadata for the instance from the AWS metadata service.
    If a specific key is provided, retrieves only that key's data.

    Args:
        key (str): The specific metadata key to retrieve (optional).

    """
    base_url = "http://169.254.169.254/latest/meta-data/"
    token_url = "http://169.254.169.254/latest/api/token"

    def fetch_token():
        response = requests.put(token_url, headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, timeout=2)
        response.raise_for_status()
        return response.text

    def fetch_metadata(url, token):
        response = requests.get(url, headers={"X-aws-ec2-metadata-token": token}, timeout=2)
        response.raise_for_status()
        return response.text

    def fetch_recursive(url, token):
        result = {}
        items = fetch_metadata(url, token).splitlines()
        for item in items:
            item_url = url + item
            if item.endswith("/"):
                result[item[:-1]] = fetch_recursive(item_url, token)
            else:
                try:
                    result[item] = fetch_metadata(item_url, token)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        result[item] = None  
                    else:
                        raise e
        return result

    try:
        token = fetch_token()
        if key:
            key_url = base_url + key
            return {key: fetch_metadata(key_url, token)}
        else:
            return fetch_recursive(base_url, token)
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch metadata: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        key = sys.argv[1]
    else:
        key = None

    metadata = get_instance_metadata(key)
    print(json.dumps(metadata, indent=4))

