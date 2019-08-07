# coding: utf-8
from json import loads
from time import sleep, time
from pickle import dump, load
from os.path import exists
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Concert(object):
    def __init__(self, session, price, real_name, damai_url, target_url):
        self.session = session # 场次序号优先级
        self.price = price # 票价序号优先级
        self.real_name = real_name # 实名者序号
        self.status = 0 # 状态标记
        self.time_start = 0 # 开始时间
        self.time_end = 0 # 结束时间
        self.num = 0 # 尝试次数
        self.damai_url = damai_url # 大麦网官网网址 
        self.target_url = target_url # 目标购票网址
    

    def isClassPresent(self, item, name, ret=False):
        try:
            result = item.find_element_by_class_name(name)
            if ret:
                return result
            else:
                return True
        except:
            return False
            

    def get_cookie(self):
        self.driver.get(self.damai_url)
        print("###请点击登录###")
        while self.driver.title.find('大麦网-全球演出赛事官方购票平台')!=-1: # 等待网页加载完成
            sleep(1)
        print("###请扫码登录###")
        while self.driver.title == '大麦登录': # 等待扫码完成
            sleep(1)
        dump(self.driver.get_cookies(), open("cookies.pkl", "wb")) 
        print("###Cookie保存成功###")
    

    def set_cookie(self):
        try:
            cookies = load(open("cookies.pkl", "rb")) # 载入cookie
            for cookie in cookies:
                cookie_dict = {
                    'domain':'.damai.cn', # 必须有，不然就是假登录
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False}
                self.driver.add_cookie(cookie_dict)
            print('###载入Cookie###')
        except Exception as e:
            print(e)
            

    def login(self):
        print('###开始登录###')
        if not exists('cookies.pkl'):# 如果不存在cookie.pkl,就获取一下
            self.get_cookie()
        self.driver.get(self.target_url)
        self.set_cookie()
     

    def enter_concert(self):
        print('###打开浏览器，进入大麦网###')
        self.driver = webdriver.Firefox() # 默认火狐浏览器
        self.driver.maximize_window()
        self.login()
        self.driver.refresh()
    

    def choose_ticket(self):
        self.time_start = time() 
        print("###开始进行日期及票价选择###")
        
        while self.driver.title.find('确认订单') == -1:  # 如果跳转到了确认界面就算这步成功了，否则继续执行此步
            '''###自动添加购票数###
            try:
                self.driver.find_elements_by_xpath('/html/body/div[2]/div/div[1]/div[1]/div/div[2]/div[3]/div[7]/div[2]/div/div/a[2]')[0].click()   #购票数+1(若需要)
            except:
                print("购票数添加失败")
            '''
            self.num += 1
            selects = self.driver.find_elements_by_class_name('perform__order__select')
            print('可选区域数量为：{}'.format(len(selects)))
            for item in selects:
                if item.find_element_by_class_name('select_left').text == '场次':
                    session = item
                    print('\t场次定位成功')
                elif item.find_element_by_class_name('select_left').text == '票档':
                    price = item
                    print('\t票档定位成功')

            session_list = session.find_elements_by_class_name('select_right_list_item')
            print('可选场次数量为：{}'.format(len(session_list)))
            for i in self.session: # 根据优先级选择一个可行场次
                j = session_list[i-1]
                k = self.isClassPresent(j, 'presell', True)
                if k: # 如果找到了带presell的类
                    if k.text == '无票':
                        continue
                    elif k.text == '预售':
                        j.click()
                        break
                else:
                    j.click()
                    break

            price_list = price.find_elements_by_class_name('select_right_list_item')
            print('可选票档数量为：{}'.format(len(price_list)))
            for i in self.price:
                j = price_list[i-1]
                k = self.isClassPresent(j, 'notticket')
                if k: # 存在notticket代表存在缺货登记，跳过
                    continue
                else:
                    j.click()
                    break
            
            buybutton = self.driver.find_element_by_class_name('buybtn')
            buybutton_text = buybutton.text
            
            if buybutton_text == "即将开抢":
                self.status = 2
                self.driver.get(self.target_url)
                print('###抢票未开始，刷新等待开始###')
                continue

            elif buybutton_text == "立即预订":
                buybutton.click()
                self.status = 3
                    
            elif buybutton_text == "立即购买":
                buybutton.click()
                self.status = 4                    
        
            elif buybutton_text == "选座购买": # 选座购买暂时无法完成自动化
                buybutton.click()
                self.status = 5
                print("###请自行选择位置和票价###") # 此处或可改成input，等待用户选完后反馈，继续抢票流程
                break
                    
            elif buybutton_text == "提交缺货登记":
                print('###抢票失败，请手动提交缺货登记###')  
                break  
                
            # break           
    

    def check_order(self):
        if self.status in [3,4,5]:
            print('###开始确认订单###')
            print('###选择购票人信息###')   
            try:
                tb = WebDriverWait(self.driver, 3, 0.3).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[2]/div/div[2]/div[2]/div[1]')))
            except Exception as e:
                print("###实名信息选择框没有显示###")
                print(e)
            lb=tb.find_elements_by_tag_name('label')[self.real_name-1] # 选择第self.real_name个实名者
            lb.find_element_by_tag_name('input').click()
            print('###不选择订单优惠###')
            print('###请在付款完成后下载大麦APP进入订单详情页申请开具###')
            self.driver.find_element_by_xpath('/html/body/div[2]/div[2]/div/div[9]/button').click() # 同意以上协议并提交订单
            try:
                element = WebDriverWait(self.driver, 5).until(EC.title_contains('支付'))
                self.status = 6
                print('###成功提交订单,请手动支付###')
                self.time_end = time()
            except:
                print('###提交订单失败,请查看问题###')
               

    def finish(self):
        if self.status == 6: # 说明抢票成功
            print("###经过%d轮奋斗，共耗时%f秒，抢票成功！请及时付款###"%(self.num-1,round(self.time_end-self.time_start,3)))
        else:
            self.driver.quit()


if __name__ == '__main__':
    try:
        with open('./config.json', 'r', encoding='utf-8') as f:
            config = loads(f.read())
            # params: 场次优先级，票价优先级，实名者序号, 官网网址， 目标网址
        con = Concert(config['sess'], config['price'], config['real_name'], config['damai_url'], config['target_url'])
        con.enter_concert()
        con.choose_ticket()
        con.check_order()
        con.finish()
    except Exception as e:
        print(e)