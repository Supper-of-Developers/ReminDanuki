# リマインだぬき

## 概要

事前に何時何分にこの予定をリマインドして欲しいと入力しておくと、その時間になったら通知してくれる予定管理用のLINEボットです。

## 登録方法

LINEアプリで下記のQRコードを読み取って友達登録する。  
![QRコード](./qr.png)

## 使い方

1. 手入力、またはリッチメニューから「新しいリマインダ」と入力。
1. 通知して欲しい予定を聞かれるので入力。またはキャンセル。
1. 通知して欲しい時間を設定する。
1. 設定した時間になったら通知される。

## フロー

![登録フロー](./flow1.png)
![リマインドフロー](./flow2.png)

## OS ミドルウェア

|アーキテクチャ|バージョン等|備考|
|:--|:--|:--:|
|language|python 3.6||
|SDK|line-bot-sdk-python|[Githubリポジトリ](https://github.com/line/line-bot-sdk-python)|
|Docker|17.03.2-ce||
|Docker Image|python:alpine3.7||
|Docker Host|Amazon Linux|AWS|
|DB|Amazon RDS||
|Redis|Amazon ElastiCacheRedis||

## 構成図

![構成図](./diagram.png)
