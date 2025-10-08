# module_utils/radware_cc.py

import requests
import time
import random
import os
import tempfile
import pickle
import hashlib
from ansible.module_utils.logger import Logger


class RadwareCC:
    def __init__(self, cc_ip, username, password, verify_ssl=False, logger=None, log_level="disabled", session_lifetime=600, timeout=30):
        self.cc_ip = cc_ip
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self._username = username  # Store for re-login
        self._password = password  # Store for re-login
        self.session_lifetime = session_lifetime
        if not self.verify_ssl:
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            except Exception:
                pass
        if logger is None:
            self.log = Logger(verbosity=log_level)
        else:
            self.log = logger
        self._load_or_login()

    def _get_session_file(self):
        key = f"{self.cc_ip}_{self._username}"
        key_hash = hashlib.md5(key.encode()).hexdigest()
        # Try to use ./tmp/radware_cc_sessions under the current working directory
        try:
            cwd = os.getcwd()
            session_dir = os.path.join(cwd, "tmp", "radware_cc_sessions")
            os.makedirs(session_dir, exist_ok=True)
        except Exception:
            # Fallback to system temp dir if creation fails
            session_dir = os.path.join(tempfile.gettempdir(), "radware_cc_sessions")
            os.makedirs(session_dir, exist_ok=True)
        session_file = os.path.join(session_dir, f"session_{key_hash}.pkl")
        session_time_file = os.path.join(session_dir, f"session_{key_hash}.time")
        return session_file, session_time_file

    def _load_or_login(self):
        session_file, session_time_file = self._get_session_file()
        # Add separator at the start of a new run
        self.log.info("======================================================")
        self.log.info("Checking for existing session")
        if os.path.exists(session_file) and os.path.exists(session_time_file):
            try:
                with open(session_time_file, "r") as tf:
                    created_time = float(tf.read().strip())
                age = time.time() - created_time
                self.log.debug(f"Session file age: {age:.2f} seconds (lifetime: {self.session_lifetime}s)")
                if age < self.session_lifetime:
                    with open(session_file, "rb") as f:
                        cookies = pickle.load(f)
                    self.session.cookies.update(cookies)
                    self.log.info(f"Reusing session for {self.cc_ip} as {self._username} (age: {age:.2f}s < {self.session_lifetime}s)")
                    return
                else:
                    self.log.info(f"Session expired for {self.cc_ip} as {self._username} (age: {age:.2f}s >= {self.session_lifetime}s), re-logging in")
            except Exception as e:
                self.log.error(f"Failed to load session: {e}")
        self.log.info(f"Logging in to Radware CC at {self.cc_ip} as {self._username}")
        self.login(self._username, self._password)
        # Save session after login
        with open(session_file, "wb") as f:
            pickle.dump(self.session.cookies, f)
        with open(session_time_file, "w") as tf:
            tf.write(str(time.time()))
        # Log where the session is stored after first login
        self.log.info(f"Session stored at: {session_file}")

    def login(self, username, password):
        url = f"https://{self.cc_ip}/mgmt/system/user/login"
        r = self.session.post(url, json={"username": username, "password": password},
                              verify=self.verify_ssl, timeout=self.timeout)
        r.raise_for_status()
        if self.log:
            self.log.info(f"Logged in to Radware CC at {self.cc_ip} as {username}")
        data = r.json()
        if data.get("status") != "ok":
            if self.log:
                self.log.error(f"Login failed: {data}")
            raise Exception("Login failed")


    def _request(self, method, url, retries=3, delay=1, data=None, json=None):
        relogin_attempted = False
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.request(method=method, url=url,
                                            data=data, json=json,
                                            verify=self.verify_ssl, timeout=self.timeout)
                resp.raise_for_status()
                return resp
            except requests.exceptions.HTTPError as err:
                # On 403, re-login once and retry
                if err.response is not None and err.response.status_code == 403 and not relogin_attempted:
                    if self.log:
                        self.log.info(f"[{method.upper()}] 403 Forbidden. Reauthenticating and retrying once…")
                    try:
                        self._load_or_login()
                        relogin_attempted = True
                        continue
                    except Exception as login_err:
                        err_msg = f"403 Forbidden. Re-login failed: {login_err}"
                        raise requests.exceptions.HTTPError(err_msg, response=err.response)
                # Enhance error message with response body if available
                err_msg = str(err)
                if err.response is not None:
                    try:
                        content_type = err.response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            err_body = err.response.json()
                        else:
                            err_body = err.response.text
                        err_msg += f"\nResponse body: {err_body}"
                    except Exception:
                        pass
                raise requests.exceptions.HTTPError(err_msg, response=err.response)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.SSLError,
                    requests.exceptions.Timeout):
                if attempt < retries:
                    sleep_time = delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    time.sleep(sleep_time)
                else:
                    raise

    def _post(self, url, data=None, json=None):
        return self._request("post", url, data=data, json=json)

    def _get(self, url):
        return self._request("get", url)

    def _put(self, url, data=None, json=None):
        return self._request("put", url, data=data, json=json)

    def _delete(self, url, data=None, json=None):
        return self._request("delete", url, data=data, json=json)


