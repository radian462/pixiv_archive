import json
import os
from urllib.error import URLError
from urllib.parse import urlparse, urlencode
from urllib.request import Request, urlopen

class PixivClient:
    def __init__(self, refresh_token: str | None = None):
        self.CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
        self.CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
        self.USER_AGENT = "PixivIOSApp/7.13.3 (iOS 14.6; iPhone13,2)"

        self.AUTH_ENDPOINT = "https://oauth.secure.pixiv.net/auth/token"
        self.DETAIL_ENDPOINT = "https://app-api.pixiv.net/v1/illust/detail"
        self.NO_AUTH_DETAIL_ENDPOINT = "https://www.pixiv.net/ajax/illust/%s"

        self.REFRESH_TOKEN = refresh_token
        self.ACCESS_TOKEN = None

        if self.REFRESH_TOKEN is not None:
            self._refresh_access_token()

    def _refresh_access_token(self):
        data = urlencode({
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": self.REFRESH_TOKEN,
        }).encode()

        headers = {
            "User-Agent": self.USER_AGENT,
            "App-OS-Version": "14.6",
            "App-OS": "ios",
        }

        r = Request(self.AUTH_ENDPOINT, data=data, headers=headers, method="POST")

        try:
            with urlopen(r) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    self.ACCESS_TOKEN = data["access_token"]
        except URLError as e:
            print(f"Error refreshing access token: {e}")

    def get_illusts(self, illust_id: int | str):
        if self.ACCESS_TOKEN is None:
            headers = {
                "Referer": "https://www.pixiv.net/",
                "User-Agent": self.USER_AGENT,
            }

            illust_id = str(illust_id)
            r = Request(self.NO_AUTH_DETAIL_ENDPOINT % illust_id, headers=headers)

            try:
                with urlopen(r) as response:
                    IllustData = json.loads(response.read().decode())["body"]["userIllusts"][illust_id]

                ParsedFirstImage = urlparse(IllustData["url"])
                TagImgIndex = ParsedFirstImage.path.find('/img/') + len('/img/')
                ImagePath = ParsedFirstImage.path[TagImgIndex:].replace("_custom1200", "").replace("jpg","png")
                FirstImageUrl = "https://i.pximg.net/img-original/img/" + ImagePath
                IllustPage = IllustData["pageCount"]

                ImageList = [FirstImageUrl.replace("p0", f"p{i}") for i in range(IllustPage)]
            except URLError as e:
                print(f"Error fetching illust data: {e}")
                return []

        else:
            params = urlencode({"illust_id": illust_id})
            url = f"{self.DETAIL_ENDPOINT}?{params}"

            headers = {
                "App-OS": "ios",
                "App-OS-Version": "14.6",
                "User-Agent": self.USER_AGENT,
                "Authorization": f"Bearer {self.ACCESS_TOKEN}",
            }

            r = Request(url, headers=headers)

            try:
                with urlopen(r) as response:
                    data = json.loads(response.read().decode())
                    ImageList = [i["image_urls"]["original"] for i in data["illust"]["meta_pages"]]
            except URLError as e:
                print(f"Error fetching illust data: {e}")
                return []

        return ImageList

    def save_illusts(self, urls: list):
        illust_paths = []

        for url in urls:
            parsed_url = urlparse(url)
            file_name = os.path.basename(parsed_url.path)

            if not os.path.splitext(file_name)[1]:
                file_name += '.png'

            current_directory = os.getcwd()
            save_path = os.path.join(current_directory, file_name)

            headers = {
                "Referer": "https://www.pixiv.net/",
                "User-Agent": self.USER_AGENT,
            }

            r = Request(url, headers=headers)

            try:
                with urlopen(r) as response, open(file_name, 'wb') as out_file:
                    out_file.write(response.read())
                illust_paths.append(save_path)
            except URLError as e:
                print(f"Error downloading image: {e}")

        return illust_paths

if __name__ == "__main__":
    pclient = PixivClient()
    illusts = pclient.get_illusts(123516741)
    print(pclient.save_illusts(illusts))
