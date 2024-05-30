# Import packages
import pandas as pd
import math
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# Load data, set constants
df = pd.read_excel(r"Data")
df_pathfx = df.copy()
index = 0
END_NUMBER = len(df.index)

# Preprocess variables
# Invert binary variables since dropdown index is inverted
df_pathfx["Gender"] = 1 - df["Gender"]
df_pathfx["Path_Fract"] = 1 - df["Path_Fract"]
df_pathfx["Lymph"] = 2 - df["Lymph"] # 2 because first dropdown option is "-"

ecog_map = {0: "fullyActive",
            1: "restricted", 
            2: "ambulatory",
            3: "limited-selfcare",
            4: "disabled"}
            
df_pathfx["Organ"] = 1 - (df['Visceral'] | 
                          df['Brain'] | 
                          df['Disseminated']).astype(int)

# Defining methods
def initialize_webdriver():
    options = Options()
    # Options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager()
                                              .install()), options=options)
    
    driver.maximize_window()
    driver.get("https://www.pathfx.org/login")
        
    return driver

def target_value_trimming(target_value, maximum, minimum):
    if target_value > maximum:target_value = maximum
    if target_value < minimum:target_value = minimum
    return target_value

def my_round(n, ndigits):
    part = n * 10 ** ndigits
    delta = part - int(part)
    # always round "away from 0"
    if delta >= 0.5 or -0.5 < delta <= 0:
        part = math.ceil(part)
    else:
        part = math.floor(part)
    return part / (10 ** ndigits) if ndigits >= 0 else part * 10 ** abs(ndigits)

def hemo_conv(hemo):
    # Needed for PathFx: hemo g/Dl, we have mmol/L
    conv_hemo = hemo * 1.61134386078
    return conv_hemo

def fill_number(ID, option):
    number = driver.find_element(By.ID, ID)
    number.clear()
    number.send_keys(str(option).replace(".", ","))
    print("Filled out:", option)
    
def fill_default(ID, option):
    default = Select(WebDriverWait(driver, 10)
                     .until(EC.element_to_be_clickable((By.ID, ID))))
    default.select_by_index(option)
    print("Filled out:", option)

def fill_visible_dropdown(ID, option):
    default = Select(WebDriverWait(driver, 10)
                     .until(EC.element_to_be_clickable((By.ID, ID))))
    default.select_by_visible_text(option)
    print("Filled out:", option)
    

def login_cookie():
    # Try to allow cookies
    try:
        allow_cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, 
                                        "/html/body/div/div/div/button[1]")))
        allow_cookies_button.click()
        
    except TimeoutException:
        # Allow cookies button not found, continue with login
        print("Timeout occurred. Element with ID 'coockies' did not appear within the specified time.")
        pass
    
    # Try to login and wait until fields appear
    try:
        # Check if fields are available and fill username
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username")))
        username.clear()
        username.send_keys("login name")
    
        # Fill password
        password = driver.find_element(By.ID, "password")
        password.clear()
        password.send_keys("nfj!bxg_RGE7gve2qry")
        
        # Press login button
        driver.find_element(By.XPATH, 
                        "//*[@id='caseform']/div/fieldset/button").click()
        
    except TimeoutException:
        # Handle the timeout exception
        print("Timeout occurred. Element with ID 'username' did not appear within the specified time.")
        
def login():
    # Try to login and wait until fields appear
    try:
        # Check if fields are available and fill username
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username")))
        username.clear()
        username.send_keys("login name")
    
        # Fill password
        password = driver.find_element(By.ID, "password")
        password.clear()
        password.send_keys("your password")
        
        # Press login button
        driver.find_element(By.XPATH, 
                        "//*[@id='caseform']/div/fieldset/button").click()
        
    except TimeoutException:
        # Handle the timeout exception
        print("Timeout occurred. Element with ID 'username' did not appear within the specified time.")

def scroll_until_button_click(xpath):
    # Define the number of times to scroll
    scroll_count = 1
    scroll_distance = 1000

    # Perform scrolling action
    for _ in range(scroll_count):
        # Scroll down the page using JavaScript
        driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
        # Wait for a short duration to allow the page to load content after scrolling
        time.sleep(1)
        
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, 
                                       xpath))).click()
    
def scroll_until_ecog_visible():
    # Define the target element ID
    target_element_id = "disabled"

    # Set the maximum number of scroll attempts
    max_scroll_attempts = 10
    scroll_distance = 500

    # Scroll until the target element is found or the maximum scroll attempts are reached
    scroll_attempts = 0

    while scroll_attempts < max_scroll_attempts:
        # Scroll down the page using JavaScript
        driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
    
        # Wait for a short duration to allow the page to load after scrolling
        driver.implicitly_wait(2)
    
        # Check if the target element is present
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, target_element_id)))
            break  # Exit the loop if the target element is found
        except:
            # Increment the scroll attempts counter
            scroll_attempts += 1

def fill_out_form():
    # Wait untill logged in and click "Other Primary Tumors"
    primary_button_locator = (By.XPATH, 
                              "//*[@id='root']/div/main/div/div/div[2]/nav/ul/li[1]/button")
    primary_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(primary_button_locator))
    primary_button.click()
    
    fill_number(ID = "age", 
                option = df_pathfx["Age"][index])
    
    fill_default(ID = "gender", 
                 option = df_pathfx["Gender"][index])
    
    fill_visible_dropdown(ID = "oncologic-diagnosis", 
                          option = df_pathfx["PathFx_Primary"][index])
    
    fill_default(ID = "pathologic-fracture", 
                 option = df_pathfx["Path_Fract"][index])
    
    scroll_until_ecog_visible()
    css_selector = ecog_map.get(df_pathfx["ECOG"][index])
    ecog_element = driver.find_element(By.CSS_SELECTOR, 
                                 f"label[for='{css_selector}']")
    driver.execute_script("arguments[0].click();", ecog_element)

    fill_number(ID = "hemoglobin", 
                option = target_value_trimming(my_round(hemo_conv(df_pathfx["Hemo"][index]), 1), 18, 3))
    
    fill_number(ID = "lymphocyte", 
                option = target_value_trimming(my_round(df_pathfx["Abs_L"][index], 1), 8, 0))  
    
    fill_default(ID = "skeletal-metastases",
                 option = df_pathfx["Nr_Skel_Met"][index])
    
    fill_default(ID = "organ-metastases",
                 option = df_pathfx["Organ"][index])
    
    fill_default(ID = "lymph-node-metastases",
                 option = df_pathfx["Lymph"][index])
    
    print("Status: Filled out complete form")
    
    # Click "Calculate Survival Trajectory"
    scroll_until_button_click("//*[@id='root']/div/main/div/div/div[2]/div/form/fieldset/button")
        
def attribute_contains(element, attribute, value):
    return element.get_attribute(attribute) and value in element.get_attribute(attribute)

def get_results():
    print("Status: Starting to retrieve results")
    # Get results

    # Find the chart element
    chart = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 
                                       "Chart_root__3Ke9P")))
    
    circle_elements = driver.find_elements(By.TAG_NAME, "circle")
    print("Total Circles:", len(circle_elements))

    # Find all the nested <circle> elements
    results = []
    for circle in circle_elements:
        # Hover over the circle
        ActionChains(driver).move_to_element(circle).perform()
        time.sleep(2)
        
        # Retrieve id
        g_element = circle.find_element(By.XPATH, "..")
        id_value = g_element.get_attribute("id")
        print(f"Circle ID: {id_value}")

        # Construct the XPath for the tooltip element
        ActionChains(driver).move_to_element(circle).perform()
        tooltips = []
        elements = chart.find_elements(By.XPATH, "//*")
        for element in elements:
            if element.tag_name == 'g' and element.get_attribute('role') == 'tooltip':
                tooltips.append(element)
               
        print("Tooltips total:", len(tooltips))
        text = tooltips[3].text.rstrip('%')
        results.append(text)
        print(text)
    
    print("Status: Finished retrieving results")
    
    # Check the number of percentages retrieved
    if len(results) == 6:
        return results
    else:
        # Run again
        return get_results()

##############################################################################
##############################################################################
################################THE CRAWLER###################################
##############################################################################
##############################################################################

print('Which patient do you want to start with?')
start_index = int(input()) - 1

# Initialize webdriver
driver = initialize_webdriver()
login_cookie()

# Filling out the form and retrieve results
while(index < END_NUMBER):
    try:
        if index < start_index: 
            index += 1
            continue
        else:
            start_time = time.time()
            print("---------------- Patient ", index + 1, " ----------------" )
        
            fill_out_form()
            results = get_results()
            
            df.at[index, "PathFx_1_months"] = results[0]
            df.at[index, "PathFx_3_months"] = results[1]
            df.at[index, "PathFx_6_months"] = results[2]
            df.at[index, "PathFx_12_months"] = results[3]
            df.at[index, "PathFx_18_months"] = results[4]
            df.at[index, "PathFx_24_months"] = results[5]
            
            driver.get("https://www.pathfx.org/login")
            login()
                                                
            save_path = r"Data"
            df.to_excel(save_path, index = False)
            
        index += 1
        if start_index < index: 
            start_index += 1
                
    except:
        driver.get("https://www.pathfx.org/login")
        login()
        print('Error in crawling api, trying again')

driver.quit()
