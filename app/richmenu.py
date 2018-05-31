import json
import requests

class RichMenu:
    def __init__(self, name, chat_bar_text, size_full=True, selected=False):
        self.size = {"width": 2500, "height": 1686}
        if not size_full:
            self.size["height"] = 843
        self.selected = selected
        self.name = name
        self.chat_bar_text = chat_bar_text
        self.areas = []

    def add_area(self, x, y, width, height, action_type, payload):
        bounds = {"x": x, "y": y, "width": width, "height": height}
        action = {"type": action_type}
        if action_type == "postback":
            if isinstance(payload, list):
                action["data"] = payload[0]
                if len(payload) > 1:
                    action["text"] = payload[1]
            else:
                action["data"] = payload
        elif action_type == "uri":
            action["uri"] = payload
        else:
            action["text"] = payload
        self.areas.append({"bounds": bounds, "action": action})

    def to_json(self):
        dic = {"size": self.size, "selected": self.selected, "name": self.name, "chatBarText": self.chat_bar_text, "areas": self.areas}
        return json.dumps(dic)


class RichMenuManager:
    def __init__(self, channel_access_token, verify=True):
        self.headers = {"Authorization": "Bearer {%s}" % channel_access_token}
        self.verify = verify

    def register(self, rich_menu, image_path=None):
        url = "https://api.line.me/v2/bot/richmenu"
        res = requests.post(url, headers=dict(self.headers, **{"content-type": "application/json"}), data=rich_menu.to_json(), verify=self.verify).json()
        if image_path:
            self.upload_image(res["richMenuId"], image_path)
        return res

    def upload_image(self, rich_menu_id, image_path):
        url = "https://api.line.me/v2/bot/richmenu/%s/content" % rich_menu_id
        image_file = open(image_path, "rb")
        return requests.post(url, headers=dict(self.headers, **{"content-type": "image/jpeg"}), data=image_file, verify=self.verify).json()

    def download_image(self, richmenu_id, filename=None):
        url = "https://api.line.me/v2/bot/richmenu/%s/content" % richmenu_id
        res = requests.get(url, headers=self.headers, verify=self.verify)
        if filename:
            with open(filename, "wb") as f:
                f.write(res.content)
        else:
            return res.content

    def get_list(self):
        url = "https://api.line.me/v2/bot/richmenu/list"
        return requests.get(url, headers=self.headers, verify=self.verify).json()

    def remove(self, richmenu_id):
        url = "https://api.line.me/v2/bot/richmenu/%s" % richmenu_id
        return requests.delete(url, headers=self.headers, verify=self.verify).json()


    def remove_all(self):
        menus = self.get_list()
        for m in menus["richmenus"]:
            self.remove(m["richMenuId"])

    def apply(self, user_id, richmenu_id):
        url = "https://api.line.me/v2/bot/user/%s/richmenu/%s" % (user_id, richmenu_id)
        return requests.post(url, headers=self.headers, verify=self.verify).json()

    def detach(self, user_id):
        url = "https://api.line.me/v2/bot/user/%s/richmenu" % user_id
        return requests.delete(url, headers=self.headers, verify=self.verify).json()

    def get_applied_menu(self, user_id):
        url = "https://api.line.me/v2/bot/user/%s/richmenu" % user_id
        return requests.get(url, headers=self.headers, verify=self.verify).json()