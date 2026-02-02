"""
    爬虫基类模块
    主要通过单篇文章获取信息
"""
import requests
requests.packages.urllib3.disable_warnings()  # 去除网络请求警告

from fake_useragent import UserAgent    # 生成随机浏览器代理
User_Agent = UserAgent().chrome           # 获取chrome浏览器标识

from bs4 import BeautifulSoup
import lxml
import os
import re
import time
import random


from src.tools import *


class BaseSpider:
    """
        功能描述：
            爬虫基类，所有爬虫类均需继承该类
    """
    def __init__(self):
        self.session = requests.Session()    # 配置共享请求会话
        self.timeout = 10    # 设置超时
        self.headers = {'User-Agent': User_Agent}
        self.data = {}
        self.cookies = {}
        self.nickname = ''      # 公众号名称
        self.public_main_link = ''  # 公众号主页链接
    
    def delay_time(self):
        """
            功能描述：
                延时函数, 用于避免频繁请求导致的IP被封禁
            输入：
                无
            输出：
                无
        """
        second_max_num = 7
        second_min_num = 3
        second_num = random.uniform(second_min_num, second_max_num)
        second_num = round(second_num, 3)   # 保留3位小数
        print('为预防被封禁,开始延时操作，延时时间：' + str(second_num) + '秒')

        time.sleep(second_num)
    
    def delay_short_time(self):
        """
            功能描述：
                延时函数, 用于避免频繁请求导致的IP被封禁
            输入：
                无
            输出：
                无
        """
        second_max_num = 1.5
        second_min_num = 0.1
        second_num = random.uniform(second_min_num, second_max_num)
        second_num = round(second_num, 3)   # 保留3位小数
        print('为预防被封禁, 短延时：' + str(second_num) + '秒')

        time.sleep(second_num)

    def get_an_article(self, content_url):
        """
            功能描述：
                单独获取一篇文章, 只负责是否获取成功, 成功则返回文章内容, 失败则返回空字符串
            输入：
                微信文章链接（永久链接或短链接）
            输出：
                1.状态码
                2.文章内容
        """
        res = self.session.get(
            url=content_url, 
            headers=self.headers, 
            cookies=self.cookies, 
            verify=False)
        self.delay_short_time()
        # 验证请求
        if 'var createTime = ' in res.text:  # 正常获取到文章内容
            print('正常获取到文章内容')
            # save_cache(res.text)  # 保存文章内容到缓存文件，方便后续检查内容
            return {'content_flag': 1, 'content': res.text}
        elif '>当前环境异常, 完成验证后即可继续访问 <' in res.text:
            print('当前环境异常, 请检查链接后访问!!!')  # 代码访问遇到人机验证，需进行验证操作
            return {'content_flag': 0, 'current_url': content_url}
        elif '操作频繁, 请稍后再试' in res.text:
            print('操作频繁了, 等会再弄或换ip弄!!!')  # 遇到次数较少，如有遇到请前往GitHub留言
            return {'content_flag': 0, 'current_url': content_url}
        else:
            print('出现其他问题, 请查找原因后再试！！！！\n'
                  '************************************\n'
                  '一般情况下, 这篇文章可能是一整页的图片, 没有文本内容, 具体原因待讨论.该文章链接为：\n'
                  + content_url + '\n'
                  '************************************\n')  # 出现错误信息，如有遇到请前往GitHub留言
            return {'content_flag': 0, 'current_url': content_url}
        
    def format_content(self, content):
        """
            功能描述：
                格式化文章内容，提取出文章中的文本内容
            输入：
                文章内容
            输出：
                格式化后的文章内容
        """
        # 整理文章关键信息
        # nickname = re.search(r'var nickname.*"(.*?)".*', article_content).group(1)  # 公众号名称
        # article_link = re.search(r'var msg_link = .*"(.*?)".*', article_content).group(1)  # 文章链接
        # createTime = re.search(r"var createTime = '(.*?)'.*", article_content).group(1)  # 文章创建时间
        # # year, month, day = createTime.split(" ")[0].split("-")      # 年，月，日
        # # hour, minute = createTime.split(" ")[1].split(":")          # 小时，分钟
        # author = re.search(r'var author = "(.*?)".*', article_content).group(1)  # 文章作者
        # print(article_content)

        # 整理文章关键信息
        soup = BeautifulSoup(content, 'lxml')
        self.nickname = soup.find("a", id="js_name").get_text().strip()  # 公众号名称  
        author = soup.find("meta", {"name": "author"}).get("content").strip()  # 文章作者
        article_link = soup.find("meta", property="og:url").get("content")  # 文章链接
        article_title = soup.find("h1", id="activity-name").get_text().strip()  # 文章标题
        print('当前文章为>>>> ' + article_title)

        # 将文字内容转换为列表形式存储
        original_texts = soup.getText().split('\n')  # 将页面所有的文本内容提取，并转为列表形式
        format_texts = list(filter(lambda x: bool(x.strip()), original_texts))  # filter() 函数可以根据指定的函数对可迭代对象进行过滤
        
        # 正则方式
        createTime = re.search(r"var createTime = '(.*?)'.*", content).group(1)  # 文章创建时间
        year, month, day = createTime.split(" ")[0].split("-")      # 年，月，日
        hour, minute = createTime.split(" ")[1].split(":") 
        
        # 提取公众号biz值, 拼凑主页链接
        appuin = re.search(r"var appuin = (.*?);", content).group(1)  # 公众号biz值
        quoted_values = re.findall(r'["\']([^"\']*)["\']', appuin)
        for value in quoted_values:
            if value:
                self.biz = value
        # 公众号主页链接
        self.public_main_link = ('https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=' 
                                 + self.biz + '&scene=124#wechat_redirect')
        
        return {
            'nickname': self.nickname, 
            'author': author, 
            'article_link': article_link, 
            'article_title': article_title,
            'createTime': createTime,
            'content': content,
            'format_texts': format_texts,   # 格式化后的文章内容
        }
        
    def save_article_img(self, data_path, content_info):
        """
            功能描述：
                保存单篇文章的图片内容到本地目录
            输入：
                文章信息
            输出：
                None
        """
        # 文章图片保存目录
        nickname_path = os.path.join(data_path, '公众号----' + self.nickname)
        os.makedirs(nickname_path, exist_ok=True)  # 创建数据存储目录

        # 适配Windows系统路径
        article_title = content_info['article_title']  # 文章标题
        article_title_win = re.sub(r'[\\/*?:"<>|].', '_', article_title)  # Windows下标题
        article_title_win = article_title_win.replace('.', '')  # Windows下标题，去除小数点，防止自动省略报错
        title_time = content_info['createTime'].replace(':', '_')  # 文章发布时间，Windows下文件名不能包含冒号 

        # 创建图片保存目录
        img_save_path = os.path.join(nickname_path, title_time + ' ---- ' + article_title_win)
        os.makedirs(img_save_path, exist_ok=True)
        print('设置文章图片存储路径>>>> ' + img_save_path)

        # 保存该文章图片内容
        images = content_info['content'].split('https://mmbiz.qpic.cn/')
        # print(images)
    
        for i in range(0, len(images) - 1):
            image_url = 'https://mmbiz.qpic.cn/' + images[i + 1].split('"')[0]
            # print('正在获取图片：' + image_url)
            image_name = ''

            try:
                # 添加随机延迟，避免请求过快
                time.sleep(0.5 + random.random())

                # 使用session发送请求，设置超时
                response = self.session.get(image_url, verify=False, timeout=self.timeout)
                
                # 检查响应状态码
                if response.status_code == 200:
                    # 图片命名
                    img_hz = ['gif', 'jpg', 'jpeg', 'png', 'webp']
                    for imghz in img_hz:
                        if imghz in image_url:
                            image_name = str(i + 1) + '.' + imghz
                    if image_name == '':  # 如果链接中没有标明图片属性
                        image_name = str(i + 1) + '.jpg'
                    file_path = os.path.join(img_save_path, image_name)
                    # 保存图片
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"已成功下载图片： {file_path}")
                else:
                    print(f"无法下载图片，状态码: {response.status_code}")
            except Exception as e:
                print(f"下载图片时出错：{str(e)}")
                time.sleep(1)  # 重试前等待
        print('已保存文章图片>>>> ' + article_title)

