# アバター通常版サーバー 🤖

Unity アバター受付ロボット用の AI サーバーです（`stellar_standard_aiserver`）。特定のクライアント向けではなく、複数案件で使い回す標準版のベースサーバーです。

## 開発者向け
### セットアップ ⚙️

Operation System: Windows 11

1. リポジトリをクローンする
```
>> git clone git@github.com:dev-sl-ai/stellar_standard_aiserver.git
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
INFO:     Started server process [14504]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

----

## Unity Avatar でテスト
Unity のアバター　exe を実行してください。

## Command Line　でテスト

AI サーバーと新しいcommand line から直接話できます。
Unity からのUI 入力が必要な機能たちはテストできないです。

You can speak with AI server from command line terminal. \
Open a new terminal with environment activated. \
Some of the UI inputs which required Unity can't be used.

以下コメンドを実行する（`room_id` が異なる2つの独立したテストクライアントです）:
```
>> python unit_test/test_client1.py
>> python unit_test/test_client2.py
```

## Customization📝
- To modify AI prompt, rag information, tool usage, update
[src\configs\AI_conf.yaml](src\configs\AI_conf.yaml).

- サーバー設定 (ホスト/ポート, タイムアウト, 公開URLなど) は　
[src\configs\server_conf.yaml](src\configs\server_conf.yaml)　に更新してください。

----
## Docker 🐳

本番相当の実行環境として Docker にも対応しています。

```
>> docker build -t aiserver -f dockerfile .
>> docker run -p 8080:8080 --env-file .env -v /opt/aiserver/logs:/app/logs aiserver
```

- `WEB_CONCURRENCY`（既定値: 3）で uvicorn のワーカープロセス数を指定できます。VPS の CPU コア数に合わせて `-e WEB_CONCURRENCY=4` のように上書きしてください。
- `LOG_DIR`（既定値: `/app/logs`）をホスト側にバインドマウントすると、コンテナを削除してもログが残ります。

