import pandas as pd
import numpy as np
import math
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

#Constants
df = pd.read_excel(r"...")
END_NUMBER = len(df.index)
index = 0

#Preprocess variables
def sorg_ecog(value):
    if (value == 0 or
        value == 1 or
        value == 2):
        return 0
    elif (value == 3 or
          value == 4):
        return 1

def sorg_asia(value):
    if value == 4:
        return 0
    else:
        return 1

def sorg_spine_met(value):
    if value == 2:
        return 1
    else: 
        return 0

#Methods
def closest(list, k):
    return list[min(range(len(list)), key = lambda i: abs(list[i]-k))]

def my_round(n, ndigits):
    part = n * 10 ** ndigits
    delta = part - int(part)
    # always round "away from 0"
    if delta >= 0.5 or -0.5 < delta <= 0:
        part = math.ceil(part)
    else:
        part = math.floor(part)
    return part / (10 ** ndigits) if ndigits >= 0 else part * 10 ** abs(ndigits)

def round_to_five(value):
    value = float(value)
    value = my_round(my_round(value*20,0)/20,2)
    return value

def calc_value_lymph(df_value): 
    all_abs_lymp = np.arange(0.06,4.51,0.05).tolist()
    all_abs_lymp = [my_round(num, 2) for num in all_abs_lymp]
    all_abs_lymp.append(4.5)
    
    target_value = closest(all_abs_lymp, df_value)
    return target_value

def calc_value_neu(df_value):
    all_abs_neu = np.arange(0.8,60.3,0.5).tolist()
    all_abs_neu = [my_round(num, 1) for num in all_abs_neu]
    all_abs_neu.append(60)
    
    target_value = closest(all_abs_neu, df_value)
    return target_value

def calc_alb(df_value):
    # We have in g/L, SORG uses g/dL
    target_value = df_value/10
    return target_value

def calc_creat(df_value):
    # We have in umol/L, SORG uses mg/dL, conversion unit from https://www.scymed.com/en/smnxps/psxdf212_c.htm
    target_value = df_value/88.42
    return target_value

def calc_hemo(df_value):
    # We have in mmol/L, SORG uses g/dL, conversion unit from https://www.scymed.com/en/smnxpf/pfxdq210_c.htm
    target_value = df_value/0.6206
    return target_value


prediction_result0, prediction_result0A, prediction_result1, prediction_result1A, prediction_result2, prediction_result2A  = 0, 0, 0, 0, 0, 0

def not_default_choice_first(row, column, option):
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="shiny-tab-Input"]/div[{}]/div[{}]/div/div/div/div[1]/div'.format(str(row),str(column))))).click()
    driver.find_element("xpath",'//*[@id="shiny-tab-Input"]/div[{}]/div[{}]/div/div/div/div[2]/div/div[{}]'.format(str(row),str(column),str(option))).click()
    
def not_default_choice(row, column, option):
    driver.find_element("xpath",'//*[@id="shiny-tab-Input"]/div[{}]/div[{}]/div/div/div/div[1]/div'.format(str(row),str(column))).click()
    driver.find_element("xpath",'//*[@id="shiny-tab-Input"]/div[{}]/div[{}]/div/div/div/div[2]/div/div[{}]'.format(str(row),str(column),str(option))).click()

def target_value_trimming(target_value, maximum, minimum):
    if target_value > maximum:target_value = maximum
    if target_value < minimum:target_value = minimum
    return target_value

def custom_round(value, decimals=4):
    """
    Rounds the value to the specified number of decimals, removing trailing zeros from the last decimal place.
    """
    rounded_value = round(value, decimals)  # Round to the specified number of decimals
    formatted_value = f"{rounded_value:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted_value

def set_slider_value_with_drag(target_value, row, column, min_value, max_value):
    # Constants for slider range
    max_percentage = 88.2353

    # Calculate the percentage for the target value
    percentage = ((target_value - min_value) / (max_value - min_value)) * max_percentage
    percentage = float(custom_round(percentage))  # Apply custom rounding

    # Locate the slider handle
    slider_handle = driver.find_element("xpath", '/html/body/div[1]/div/section/div/div[3]/div[{}]/div[{}]/div/span/span[5]'.format(row, column))

    # Current percentage (extract current position)
    style = slider_handle.get_attribute("style")
    current_percentage = float(style.split("left:")[1].replace("%;", "").strip())

    # Calculate offset needed for the target percentage
    slider_width = slider_handle.size['width']  # Width of the slider bar
    container = driver.find_element("xpath", '/html/body/div[1]/div/section/div/div[3]/div[{}]/div[{}]/div/span'.format(row, column))
    container_width = container.size['width']  # Width of the slider container
    offset = (percentage - current_percentage) / 100 * container_width

    # Simulate drag-and-drop operation
    action = ActionChains(driver)
    action.click_and_hold(slider_handle).move_by_offset(offset, 0).release().perform()

    # Trigger a change event to ensure the slider updates
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", slider_handle)

def mouse_left_or_right(target_value, interval, xoffset, row, column):
    interval, xoffset, row, column, i = float(interval), float(xoffset), str(row), str(column), 0
    current = driver.find_element("xpath",'/html/body/div[1]/div/section/div/div[3]/div[{}]/div[{}]/div/span/span[1]/span[6]'.format(row, column))
    current_value = current.text
    if ',' in current_value: current_value = current_value.replace(',','')
    current_value = round(float(current_value), 2)
    diff = round(target_value - current_value, 2)
    if diff != 0: circle_direct = diff/abs(diff)
    else: circle_direct = 0
    while diff*circle_direct > interval:
        current_old_vlue, i = current_value, i+1
        if i>20: break
        action = ActionChains(driver)
        circle = driver.find_element("xpath",'/html/body/div[1]/div/section/div/div[3]/div[{}]/div[{}]/div/span/span[5]'.format(row, column))
        circle.click()
        action.drag_and_drop_by_offset(circle, xoffset*circle_direct, 0).perform()
        sleep(1)
        while (current_old_vlue == current_value):
            sleep(0.1)
            current_value = current.text
            if ',' in current_value: current_value = current_value.replace(',','')
            current_value = round(float(current_value),2)
        diff = round(target_value - current_value, 2)

def key_board_left_or_right(target_value, row, column):
    row, column = str(row), str(column)
    current = driver.find_element("xpath",'/html/body/div[1]/div/section/div/div[3]/div[{}]/div[{}]/div/span/span[1]/span[6]'.format(row, column))
    current_value = current.text
    if ',' in current_value: current_value = current_value.replace(',','')
    current_value = round(float(current_value), 2)
    diff = round(target_value - current_value, 2)

    while (diff!=0):
        current_old_vlue = current_value
        action = ActionChains(driver)
        circle = driver.find_element("xpath",'/html/body/div[1]/div/section/div/div[3]/div[{}]/div[{}]/div/span/span[5]'.format(row, column))
        circle.click()
        if diff > 0: action.key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()
        else: action.key_down(Keys.ARROW_LEFT).key_up(Keys.ARROW_LEFT).perform()
        while (current_value == current_old_vlue):
            sleep(0.5)
            current_value = current.text
            if ',' in current_value: current_value = current_value.replace(',','')
            current_value = round(float(current_value),2)
        diff = round(target_value - current_value, 2)

def isElementExist_xpath(xpath):
    flag=True
    try:
        driver.find_element("xpath",str(xpath))
        return flag
    except:
        flag = False
        return flag

def isElementClickable_xpath(xpath):
    flag=True
    try:
        driver.find_element("xpath",str(xpath)).click()
        driver.find_element("xpath",str(xpath)).click()
        return flag
    except:
        flag = False
        return flag

def extract_result(text):
    end, start = text.find('percent'), text.find('is')
    text = text[start+3:end-1]
    return text

def dateframe_reset_index(data_frame):
    data_frame = data_frame.reset_index()
    if 'index' in data_frame.columns:
        data_frame = data_frame.drop('index', axis = 1)
    return data_frame

def initialize_webdriver():
    # open it, go to a website, and get results
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    driver.get("https://sorg-apps.shinyapps.io/spinemetssurvival/")
    
    return driver

def fill_out_form():
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, 
                                                               '//*[@id="sidebarItemExpanded"]/ul/li[3]/a'))).click()

    not_default_choice_first(row = 1, column = 1, option = df['Katagiri_Group'][index])
    not_default_choice(row = 1, column = 2, option = sorg_ecog(df['ECOG'][index])+1)
    not_default_choice(row = 1, column = 3, option = sorg_asia(df['ASIA'][index])+1)
    not_default_choice(row = 1, column = 4, option = df['CCI_YN'][index]+1)
    not_default_choice(row = 2, column = 1, option = df['Visceral'][index]+1)
    not_default_choice(row = 2, column = 2, option = df['Brain'][index]+1)
    not_default_choice(row = 2, column = 3, option = df['Pre_Chem'][index]+1)
    not_default_choice(row = 2, column = 4, option = sorg_spine_met(df['Nr_Spine_Met'][index])+1)

      # Body mass index
    target_value = target_value_trimming(my_round(df['BMI'][index],0), 45, 15)
    set_slider_value_with_drag(target_value = target_value, row = 3, column = 1, min_value=15, max_value=45)
    key_board_left_or_right(target_value = target_value, row = 3, column = 1)
    
      # Hemoglobin
    target_value = target_value_trimming(my_round(calc_hemo(df['Hemo'][index]),0), 17, 7)
    set_slider_value_with_drag(target_value = target_value, row = 3, column = 2, min_value=7, max_value=17)
    key_board_left_or_right(target_value = target_value, row = 3, column = 2)
    
      # Platelet
    target_value = target_value_trimming(my_round(df['Platelet'][index],0), 900, 20)
    set_slider_value_with_drag(target_value = target_value, row = 3, column = 3, min_value=20, max_value=900)
    key_board_left_or_right(target_value = target_value, row = 3, column = 3)
    
      # Absolute Lymphocyte
    target_value = target_value_trimming(calc_value_lymph(df['Abs_L'][index]), 4.5, 0.06)
    set_slider_value_with_drag(target_value = target_value, row = 3, column = 4, min_value=0.06, max_value=4.5)
    key_board_left_or_right(target_value = target_value, row = 3, column = 4)

    #  # Absolute Neutrophil
    target_value = target_value_trimming(calc_value_neu(df['Abs_N'][index]), 60, 0.8)
    set_slider_value_with_drag(target_value = target_value, row = 4, column = 1, min_value=0.8, max_value=60)
    key_board_left_or_right(target_value = target_value, row = 4, column = 1)   
    
      # Creatinine
    target_value = target_value_trimming(round_to_five(calc_creat(df['Creat'][index])), 6, 0.3)
    set_slider_value_with_drag(target_value = target_value, row = 4, column = 2, min_value=0.3, max_value=6)
    key_board_left_or_right(target_value = target_value, row = 4, column = 2)   
    
      # INR
    target_value = target_value_trimming(my_round(df['INR'][index],2), 2.1, 0.9)
    set_slider_value_with_drag(target_value = target_value, row = 4, column = 3, min_value=0.9, max_value=2.1)
    key_board_left_or_right(target_value = target_value, row = 4, column = 3)   
    
      # White Blood Cell
    target_value = target_value_trimming(my_round(df['WBC'][index],0), 50, 2)
    set_slider_value_with_drag(target_value = target_value, row = 4, column = 4, min_value=2, max_value=50)
    key_board_left_or_right(target_value = target_value, row = 4, column = 4)
    
      # Alkaline Phosphatase
    target_value = target_value_trimming(my_round(df['Alk_Fos'][index],0), 1200, 30)
    set_slider_value_with_drag(target_value = target_value, row = 5, column = 1, min_value=30, max_value=1200)
    key_board_left_or_right(target_value = target_value, row = 5, column = 1)
    
      # Albumin
    target_value = target_value_trimming(round_to_five(calc_alb(df['Alb'][index])), 5.2, 2.1)
    set_slider_value_with_drag(target_value = target_value, row = 5, column = 2, min_value=2.1, max_value=5.2)
    key_board_left_or_right(target_value = target_value, row = 5, column = 2)   
    
    update_button = driver.find_element(by=By.XPATH, value='//*[@id="update"]')
    update_button.click()
    sleep(1)       

def extract_predictions():
    # 90-day result
    day_90_button = driver.find_element(By.XPATH, '/html/body/div/div/section/div/div[4]/div[1]/div/ul/li[2]')
    day_90_button.click()
    sleep(1)  # Allow time for content to load
    prediction_result1 = extract_result(driver.find_element(by=By.XPATH, value='//*[@id="result90"]').text)

    # 360-day result
    day_365_button = driver.find_element(By.XPATH, '/html/body/div/div/section/div/div[4]/div[1]/div/ul/li[3]')
    day_365_button.click()
    sleep(1)  # Allow time for content to load
    prediction_result2 = extract_result(driver.find_element(by=By.XPATH, value='//*[@id="result360"]').text)

    return prediction_result1, prediction_result2

#Webcrawler
driver = initialize_webdriver()

print('Which patient do you want to start with?')
start_index = int(input()) - 1

while(index < END_NUMBER):
    try:
        if index < start_index: 
            index += 1
            continue
        else:
            print("-------------------- Patient ", index + 1, " --------------------" )
            
            fill_out_form()

            prediction_result1, prediction_result2 = extract_predictions()
                        
            df.at[index, 'SORG_3_months'], prediction_result1A = prediction_result1, prediction_result1
            df.at[index, 'SORG_12_months'], prediction_result2A = prediction_result2, prediction_result2
            save_path = r"..."
            df.to_excel(save_path, index = False)
                        
            print("Patient: ", index + 1,", 90-day = ", prediction_result1, ", 1-year = ", prediction_result2)
                
        index += 1
        if start_index < index: 
            start_index += 1
    except:
        driver.get("https://sorg-apps.shinyapps.io/spinemetssurvival/")
        print('Error in crawling api, trying again')
        

driver.quit()
