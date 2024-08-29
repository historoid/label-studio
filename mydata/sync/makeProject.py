#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import re
import shutil
import requests
from dotenv import load_dotenv
from label_studio_sdk.client import LabelStudio


# In[2]:


# 設定値
load_dotenv('./config.env')

server_ip = os.getenv('SERVER_IP') 
backend_ip = os.getenv('BACKEND_IP')
api_key = os.getenv('API_KEY')
ui_config_path = os.getenv('UI_CONFIG_PATH')
data_dir = os.getenv('DATA_DIR')


# In[3]:


def create_projects(**kwargs):

    # default
    SERVER_IP = kwargs.get('SERVER_IP', server_ip)
    BACKEND_IP = kwargs.get('BACKEND_IP', backend_ip)
    API_KEY = kwargs.get('API_KEY', api_key)
    UI_CONFIG_PATH = kwargs.get('UI_CONFIG_PATH', ui_config_path)
    DATA_DIR = kwargs.get('DATA_DIR', data_dir)
    SOURCE_DIR = os.path.join(DATA_DIR, '00_UNIMPORTED')
    DIST_DIR = os.path.join(DATA_DIR, '01_IMPORTED')
    image_extensions = ('.jpeg', '.jpg', '.png', '.gif')

    # initialize client
    client = LabelStudio(base_url=SERVER_IP, api_key=API_KEY)

    # 患者フォルダのフォルダ名のパターン
    pattern = re.compile(r'^[fs][0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

    # IMPORTED ディレクトリの有無
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)

    # DATA_DIR にある患者フォルダのみを逐次処理
    for dirname in os.listdir(DATA_DIR):
        dir_path = os.path.join(DATA_DIR, dirname)
        if os.path.isdir(dir_path) and pattern.match(dirname):
            print(f'\n--- 処理中のフォルダ: {dirname} ---')

            # 画像ファイルの選択
            image_files = [os.path.join(dir_path, item) for item in os.listdir(dir_path)]
            image_files = [item for item in image_files if os.path.isfile(item) and item.lower().endswith(image_extensions)]
            total_files = len(image_files)

            # 画像があるときのみ、プロジェクトを新規作成
            if total_files != 0:
                
                # プロジェクト作成
                try:
                    with open(UI_CONFIG_PATH, 'r', encoding='utf-8') as file:
                        label_config = file.read()
                    project = client.projects.create(title=f"{dirname}", label_config=label_config)
                    backend = client.ml.create(
                        url=BACKEND_IP,
                        project=project.id,
                        is_interactive=True,
                        title='SAM',
                        # auth_method='BASIC_AUTH',
                        # basic_auth_user='oudx',
                        # basic_auth_pass='f302'
                    )

                    # 画像ファイルのアップロード
                    for i, image in enumerate(image_files):
                        with open(image, 'rb') as img:
                            response = requests.post(
                                f'{SERVER_IP}/api/projects/{project.id}/import',
                                headers={'Authorization': f'Token {API_KEY}'},
                                files={'file': img}
                            )
                        # プログレスバーの設定
                        progress = (i + 1) / total_files * 100
                        progress_bar = '█' * int(progress / 10) + '▏' * (10 - int(progress / 10))
                        print(f'\rアップロード中: [{progress_bar}] {progress:.2f}%', end='')
                        if response.status_code == 201:
                            print(f'  ファイルがアップロードされました：{os.path.basename(image)}')
                        else:
                            print(f'  ファイルアップロードに失敗しました：{os.path.basename(image)}, {response.status_code}, {response.text}')
                
                    # プロジェクト化が完了したフォルダをIMPORTEDフォルダに移動
                    shutil.move(dir_path, os.path.join(DIST_DIR, dirname))
                    print(f'フォルダを移動しました：{dirname}')
            
                except Exception as e:
                    print(f'プロジェクトの作成またはフォルダの移動に失敗しました：{dirname}, エラー：{str(e)}')
            
            else:
                shutil.move(dir_path, os.path.join(DIST_DIR, dirname))
                print(f'このフォルダには画像が含まれていません。処理済みとして移動します。：{dirname}')


# In[4]:

if __name__ == '__main__':
    create_projects()


# In[ ]:




