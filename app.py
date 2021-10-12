import os
import boto3
import datetime
import pandas as pd
import json
from datetime import timedelta, timezone
import pathlib
import MeCab
 
neologd_tagger = MeCab.Tagger(
    '-O wakati '
    '-r /dev/null '
    '-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
 
 
def lambda_handler(event, context):

    # 現在の年/日付を取得(日本時間)
    JST = timezone(timedelta(hours=+9), 'JST')
    dt_now = datetime.datetime.now(JST)
    date_str = dt_now.strftime('%Y-%m-%d')

    # 読み込み用/書き込み用s3バケットを指定
    s3 = boto3.resource('s3')
    bucket_read = s3.Bucket('googlenews-store')
    bucket_write = s3.Bucket('news-keitaiso')

    # 読み込むオブジェクト一覧
    print('Reading...')
    list_objects = bucket_read.meta.client.list_objects_v2(Bucket=bucket_read.name, Prefix='dx/').get('Contents')

    # オブジェクトを一時的に保存
    for o in list_objects:
        filename_read = o.get('Key').split('/')[-1]
        bucket_read.download_file(Key=o.get('Key'), Filename='/tmp/{}'.format(filename_read))

    # 保存したファイルの一覧
    list_files = [str(p) for p in pathlib.Path('/tmp').iterdir() if p.is_file()]
    
    # 各ファイルをdataframe形式で読み込みリストに格納
    list_texts = list()
    for p in list_files:
        list_texts.append(pd.read_csv(p))
        os.remove(p)
    
    # 読み込んだdataframeを重複を削除してまとめる
    df_text = pd.concat(list_texts, axis=0).drop_duplicates(['title']).reset_index(drop=True)
    
    # 各タイトルを結合
    all_text = "\n".join(df_text['title'])
    
    # 形態素解析
    print('Mecab...')
    node = neologd_tagger.parseToNode(all_text)

    result =[]
    while node:
        word_type = node.feature.split(',')[0]
        if word_type == '名詞': # 名詞のみ取得
            result.append(node.surface)
        node = node.next
    
    # csvにして一時的に保存
    print('Writing...')
    filename_write = '{0}_{1}.csv'.format(date_str, 'mecab')
    dir_write = '/tmp/' + filename_write
    #with open(dir_write, 'w') as fout:
    #    fout.write(",".join(result))

    df_result = pd.Series(result).value_counts().to_frame('counts').reset_index().rename(columns={'index':'word'})
    df_result.to_csv(dir_write, index=False, encoding='utf-8')
    
    # 書き込み用s3に保存
    bucket_write.upload_file(dir_write, 'dx/' + filename_write) # S3に格納
        
    os.remove(dir_write)
    
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'body': df_result.to_json(force_ascii=False, orient='index')
    }
