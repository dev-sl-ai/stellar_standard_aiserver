# 龍泉寺様　AI サーバー 🤖

## 開発者向け
### セットアップ ⚙️

Operation System: Windows 11

1. リポジトリをクローンする
```
>> git clone　git@github.com:dev-sl-ai/stellar_standard_aiserver.git
```
2. 環境設定

Virtualenv 
```
>> pip install virtualenv
>> python -m venv chatbotenv
>> .\chatbotenv\Scripts\Activate.ps1

>> cd stellar_standard_aiserver
>> pip install -r requirements.txt
```

3. API keys 設定

set your own api keys in `.env`

API Keys file (.env)は関係者から貰ってください。

----
### 1. サーバー起動

以下コメンドを実行する:
```
>> python runner.py
```
以下の表示が出ったらサーバー起動完了
```
[07/07/25 15:58:24] INFO     サーバー起動 モード: 在宅モード
INFO:     Started server process [14504]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```
























