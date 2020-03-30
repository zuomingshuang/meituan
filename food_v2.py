'''
需求：
全国的店铺名称中含有：粥|沙拉|轻食|烧烤|烤肉，任意关键词的
Excel 存放所有的文本信息（序号、店铺名称、店铺城市、店铺月销量、店铺评论数、店铺电话、店铺地址）
然后需要店铺评论图片20张，一个存放图片的文件夹，文件夹里面一个子文件夹放一个店铺（子文件的命名大概是 序号@城市@店铺名称）这样的4000
'''
from gevent import monkey
monkey.patch_all()
import gevent
from gevent import pool

import requests
import re
import os
import json
import pandas as pd


class MeiTuan_Food():
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    row_id = 1

    #获取所有城市名和城市链接
    def get_city(self):
        url='https://www.meituan.com/changecity/'
        res=requests.get(url=url,headers=self.headers).text
        city_list=re.findall(r'class="link city ">(.*?)<',res)
        city_href=re.findall(r'href="(.*?)" class="link city "',res)
        city_href[0]='//as.meituan.com'
        return city_list,city_href

    #获取符合条件的商店信息并保存到data_dict
    def get_shop_msg(self,city,city_href,p):
        try:
            url = 'https:{city_href}/meishi/pn{p}/'.format(city_href=city_href,p=p)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
            res = requests.get(url=url, headers=headers).text
            poiInfos=re.findall('window._appState = (.*?)</script>',res)[0].strip(';')
            poiInfos_dict=json.loads(poiInfos)
            poiLists=poiInfos_dict['poiLists']['poiInfos']
            # print(poiLists)
            for one in poiLists:
                try:
                    if '粥' in one['title'] or '沙拉' in one['title'] or '轻食' \
                            in one['title'] or '烧烤' in one['title'] or '烤肉' in one['title']:
                        data_dict['序号'].append(self.row_id)
                        data_dict['城市'].append(city)
                        data_dict['店铺名称'].append(one['title'])
                        data_dict['评分'].append(one['avgScore'])
                        data_dict['评论数'].append(one['allCommentNum'])
                        data_dict['人均'].append(one['avgPrice'])
                        data_dict['地址'].append(one['address'])
                        # 下载并保存店铺的评论图片
                        # self.get_comment_img(one['poiId'],city,one['title'])
                        self.row_id += 1
                        print('成功爬取：'+city+'-'+one['title'])
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

        #下载并保存店铺的评论图片
        def get_comment_img(self,shop_id,city,shop_name):
            url = 'https://www.meituan.com/meishi/api/poi/getMerchantComment?uuid=17973cbd6f284620be01.1568858704.1.0.0&platform=1&partner=126&originUrl=https%3A%2F%2Fwww.meituan.com%2Fmeishi%2F{0}%2F&riskLevel=1&optimusCode=10&id={1}&userId=&offset=0&pageSize=30&mode=1&sortType=1' \
                .format(shop_id,shop_id)
            res = requests.get(url=url, headers=self.headers).text
            img_urls=re.findall(r'"url":"(.*?\.jpg)"',res)
            i=1
            shop_file_name=str(self.row_id)+'-'+city+'-'+shop_name
            os.makedirs(os.path.dirname(os.path.abspath(__file__)) + '/评论图片/' + shop_file_name)
            shop_img_path=os.path.join('评论图片',shop_file_name)
            for img_url in img_urls[:20]:
                img=requests.get(url=img_url,headers=self.headers).content
                with open(shop_img_path+'/'+str(i)+'.jpg','wb') as f:
                    f.write(img)
                i+=1



if __name__=='__main__':
    mt_food=MeiTuan_Food()
    #获取所有城市名和城市链接
    city_list,city_href=mt_food.get_city()
    # 下载并保存店铺的评论图片
    # mt_food.get_comment_img('4486515')
    data_dict={
        '序号':[],
        '城市':[],
        '店铺名称': [],
        '评分': [],
        '评论数': [],
        '人均':[],
        '地址': [],
    }
    tasks=[]
    pool=pool.Pool(30)
    for j in range(len(city_list)):
        for p in range(1,68):
            try:
                task=pool.spawn(mt_food.get_shop_msg,city_list[j],city_href[j],p)
                tasks.append(task)
                # mt_food.get_shop_msg(city=city_list[j], city_href=city_href[j],p=p)
                # 把data_dict的数据保存到Excel
            except Exception as e:
                print(e)
    gevent.joinall(tasks)
    pd.DataFrame(data_dict).to_excel('美团店铺信息.xlsx', index=False)




