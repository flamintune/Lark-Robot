import requests
import json
import os
from datetime import datetime
import hashlib
import time
import random

def translate_text(text):
    try:
        url = "https://translate.googleapis.com/translate_a/t"
        
        params = {
            'client': 'gtx',
            'dt': 't',
            'sl': 'en',
            'tl': 'zh-CN',
        }
        
        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        }
        
        data = {
            'q': text
        }
        
        response = requests.post(url, params=params, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()
        
        # Google Translate API 返回的是一个嵌套数组，第一个元素是翻译结果
        return result[0]
    except Exception as e:
        print(f"Translation error: {e}")
        return ""

def get_top_stories():
    try:
        response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
        response.raise_for_status()  # 检查 HTTP 错误
        story_ids = response.json()[:10]
    except Exception as e:
        print(f"Error fetching top stories: {e}")
        raise

    stories = []
    for story_id in story_ids:
        try:
            story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
            response = requests.get(story_url)
            response.raise_for_status()
            story = response.json()
            if story and 'title' in story and 'url' in story:
                # 获取翻译
                translated_title = translate_text(story['title'])
                stories.append({
                    'title': story['title'],
                    'translated_title': translated_title,
                    'url': story['url']
                })
                print(f"Successfully fetched and translated story: {story['title']}")
        except Exception as e:
            print(f"Error fetching story {story_id}: {e}")
            continue
    
    return stories

def send_to_lark(stories):
    webhook_url = os.environ['LARK_WEBHOOK']
    
    # 构建消息内容
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # 构建内容数组
    content_elements = []
    for idx, story in enumerate(stories, 1):
        # 添加序号和空格
        content_elements.append({
            "tag": "text",
            "text": f"{idx}. "
        })
        # 添加原文链接
        content_elements.append({
            "tag": "a",
            "text": f"{story['title']}",
            "href": story['url']
        })
        # 添加翻译（如果有）
        if story['translated_title']:
            content_elements.append({
                "tag": "text",
                "text": f" ({story['translated_title']})"
            })
        # 添加换行
        content_elements.append({
            "tag": "text",
            "text": "\n"
        })

    # 构建飞书消息格式
    message = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": f"HackerNews Daily Top 30 ({current_date})",
                    "content": [content_elements]
                }
            }
        }
    }
    
    # 发送到飞书
    # 添加调试信息
    print(f"Sending message with {len(stories)} stories")
    print(f"Message content: {json.dumps(message, indent=2)}")
    
    response = requests.post(webhook_url, json=message)
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")
    
    if response.status_code != 200:
        raise Exception(f"Failed to send message: {response.text}")

def main():
    stories = get_top_stories()
    send_to_lark(stories)

if __name__ == '__main__':
    main()