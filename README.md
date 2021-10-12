# Lambda Mecab-NEologd
AWS LambdaでMecab+NEologdの実行環境をセットアップする。

参考：[AWS Lambda with Container Image で MeCab (NEologd) を動かしてみた](https://recruit.cct-inc.co.jp/tecblog/aws/lambda-container-image-mecab/)

## 1. Dockerイメージを作成

`public.ecr.aws/lambda/python:3.8`をもとに、Mecabやmecab-ipadic-NEologd、その他必要やPythonパッケージが入った環境を作成する。

```bash
docker build -t pymecab-lambda-container ./
```

## 2. AWS ECRにログイン

```bash
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin {accountID}.dkr.ecr.ap-northeast-1.amazonaws.com
```

## 3. リポジトリが未作成の場合、ECRにリポジトリ作成

```bash
aws ecr create-repository --repository-name {repository} --image-scanning-configuration scanOnPush=true
```

## 4. イメージ名を変更

3で作成したリポジトリと同じ名前にする。

```
docker tag {image}:{tag} {accountID}.dkr.ecr.ap-northeast-1.amazonaws.com/{repository}:{tag}
```

## 5. イメージをリポジトリにpush

```
docker push {accountID}.dkr.ecr.ap-northeast-1.amazonaws.com/{repository}:{tag}
```