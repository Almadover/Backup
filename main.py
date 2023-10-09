import requests
import json
from tqdm import tqdm

amount_photo = 5

class VKUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, user_ids, amount_photo, version):
        self.params = {
            'access_token': token,
            'user_ids': user_ids,
            'v': version
        }
        self.amount_photo = amount_photo

    def get_data_user_vk(self):
        data_url = self.url+'photos.get'
        data_params = {
            'owner_id': self.params['user_ids'],
            'album_id': 'profile',
            'extended': '1',
            'v': '5.131'
        }

        res = requests.get(data_url, params={**self.params, **data_params}).json()
        return res['response']['items']

    def selection_quality_photos(self, size_photos):
        quality_photos = 0
        for size in size_photos:
            if size['height'] * size['width'] >= quality_photos:
                quality_photos = size['height'] * size['width']
                type_photo = size['type']
                url_photo = size['url']
        return type_photo, url_photo

    def data_filtering(self):
        data_user = self.get_data_user_vk()
        data_user = data_user[:amount_photo]

        list_photo = []
        for item in data_user:
            likes_photo = item['likes']['count']
            type_photo, url_photo = self.selection_quality_photos(item['sizes'])
            list_photo.append({'likes': likes_photo, 'type': type_photo, 'url': url_photo})
        return list_photo

def get_list_files(list_photo):
    output_list_files = []
    list_files = []
    files = []

    for photo in list_photo:
        index = 0
        file_name = str(photo['likes']) + '.jpg'
        while file_name in files:
            index += 1
            file_name = str(photo['likes']) + '_' + str(index)+'.txt'
        files.append(file_name)
        output_list_files.append({'file_name': file_name, 'size': photo['type']})
        list_files.append({'file_name': file_name, 'url': photo['url']})
    return output_list_files, list_files

class YaUploader:
    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def _get_upload_link(self, disk_file_path):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {'path': disk_file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def create_folder_ya(self, folder_name):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'overwrite': 'false'}
        response = requests.put(f'{upload_url}?path={folder_name}', headers=headers, params=params)
        if response.status_code == 201:
            print(f'Папка {folder_name} успешно создана на Яндекс диске')

    def upload(self, list_files, folder_ya):
        self.create_folder_ya(folder_name=folder_ya)
        print(f'Cохраняем файлы {len(list_files)} шт. в папку {folder_ya} на Яндекс диск')
        for file in tqdm(list_files, colour='green'):
            file_name = file['file_name']
            disk_file_path = folder_ya + '/' + file_name
            response_href = self._get_upload_link(disk_file_path=disk_file_path)
            href = response_href.get('href', '')
            data = requests.get(file['url'])
            response = requests.put(href, data=data.content)
        print('Файлы успешно сохранены на Яндекс диск')

if __name__ == '__main__':
    with open('user_id_token.txt', 'r') as file_object:
        token_vk = file_object.readline().strip()
        token_ya = file_object.readline().strip()
        user_ids = file_object.readline().strip()

    amount_photo = int(input('Введите количество сохраняемых фотографий на Яндекс диск: '))
    folder_name_ya = 'my_photo_vk'
    version = '5.131'

    vk_client = VKUser(token=token_vk, user_ids=user_ids, amount_photo=amount_photo, version=version)
    list_photo = vk_client.data_filtering()
    output_list_files, list_files = get_list_files(list_photo)

    with open('data_json', 'w', encoding='utf-8') as file_obj:
        json.dump(output_list_files, file_obj, indent=4, ensure_ascii=False)
        print('Список файлов с указанием размера сохранен в формате json в файл data.json')

    uploader = YaUploader(token_ya)

    uploader.upload(list_files, folder_name_ya)