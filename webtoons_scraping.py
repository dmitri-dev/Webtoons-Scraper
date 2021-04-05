from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import selenium.webdriver.support.expected_conditions as EC
import pandas as pd


options = Options()
# options.add_argument("--headless")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
wait = WebDriverWait(driver, 10)
url = "https://www.webtoons.com/en/challenge/tested/list?title_no=231173"

driver.get(url)

driver.implicitly_wait(10)


data = {
    "episode_name": [], "date": [], "loves": [], "episode_number": [], "comments_count": [],
    "comment_username": [], "comment_description": [], "comment_likes": [], "comment_dislikes": [],
    "reply_username": [], "reply_description": [], "reply_likes": [], "reply_dislikes": []
}


# add data to array by key
def append_data(arr: dict):
    try:
        for key, val in arr.items():
            data[key].append(val)
    except Exception as e:
        print("Append Data failed: ", e)


# list(episodes) must refreshed due to stale elements
def get_episodes():
    return driver.find_element_by_id("_listUl").find_elements_by_tag_name("li")


# exit conditions for loops are "index out of range - pages(episodes/comments) or element not found - next_page_button"
# use Exception as e print(e) to view exceptions
try:
    while True:
        # scrape episode
        wait.until(EC.visibility_of_element_located((By.ID, "_listUl")))
        list_items = get_episodes()
        for i in range(len(list_items)):
            episodes = get_episodes()
            episode_name = episodes[i].find_element_by_class_name("subj").text
            date = episodes[i].find_element_by_class_name("date").text
            loves = episodes[i].find_element_by_class_name("like_area").text[4:]
            episode_number = episodes[i].find_element_by_class_name("tx").text

            episode_data = {
                "episode_name": episode_name,
                "date": date,
                "loves": loves,
                "episode_number": episode_number
            }
            print(episode_data)
            append_data(episode_data)

            episodes[i].click()
            wait.until(EC.staleness_of(list_items[0]))

            # scrape comments
            try:
                while True:
                    comments = driver.find_element_by_id("cbox_module").find_elements_by_class_name("u_cbox_comment")
                    for comment in comments:
                        comment_username = comment.find_element_by_class_name("u_cbox_nick").text
                        comment_description = comment.find_element_by_class_name("u_cbox_contents").text
                        comment_likes = comment.find_element_by_class_name("u_cbox_cnt_recomm").text
                        comment_dislikes = comment.find_element_by_class_name("u_cbox_cnt_unrecomm").text
                        reply_count = comment.find_element_by_class_name("u_cbox_reply_cnt").text
                        comment_data = {
                            "comment_username": comment_username,
                            "comment_description": comment_description,
                            "comment_likes": comment_likes,
                            "comment_dislikes": comment_dislikes
                        }
                        print(comment_data)
                        append_data(comment_data)

                        # scrape replies
                        if reply_count and int(reply_count) > 0:
                            replies_button = comment.find_element_by_css_selector("a.u_cbox_btn_reply")
                            # SE click() not working due to JS rendering so execute_script()
                            driver.execute_script("arguments[0].click();", replies_button)
                            # comment box requires dynamic selector due to JS rendering comments
                            comment_class = comment.get_attribute('class').split(" ")[1]
                            replies_selector = f".{comment_class} > .u_cbox_reply_area > .u_cbox_list > .u_cbox_comment"
                            replies = driver.find_elements_by_css_selector(replies_selector)

                            for reply in replies:
                                reply_username = reply.find_element_by_class_name("u_cbox_nick").text
                                reply_description = reply.find_element_by_class_name("u_cbox_contents").text
                                reply_likes = reply.find_element_by_class_name("u_cbox_cnt_recomm").text
                                reply_dislikes = reply.find_element_by_class_name("u_cbox_cnt_unrecomm").text

                                reply_data = {
                                    "reply_username": reply_username,
                                    "reply_description": reply_description,
                                    "reply_likes": reply_likes,
                                    "reply_dislikes": reply_dislikes
                                }
                                print(reply_data)
                                append_data(reply_data)

                        pages = driver.find_element_by_class_name("u_cbox_paginate").find_elements_by_css_selector("span.u_cbox_num_page")
                        # find selected page - parent="strong"
                        for j in range(len(pages)):
                            if pages[j].find_element_by_xpath("..").tag_name == "strong":
                                # if page divisible by 10 click next_page_button else click next page
                                if int(pages[j].text) % 10 == 0:
                                    next_pages_button = driver.find_element_by_class_name("u_cbox_next")
                                    next_pages_button.click()
                                else:
                                    pages[j + 1].click()
                                break

            # if no more pages go back
            except:
                driver.back()

        # find selected episode page - class="on"
        pages = driver.find_element_by_class_name("paginate").find_elements_by_tag_name("span")
        for i in range(len(pages)):
            if pages[i].get_attribute("class") == "on":
                # if page divisible by 10 click next_page_button else click next page
                if int(pages[i].text) % 10 == 0:
                    next_pages_button = driver.find_element_by_class_name("pg_next")
                    next_pages_button.click()
                else:
                    pages[i + 1].click()
                break

except:
    print("EXECUTION COMPLETE")


df = pd.DataFrame.from_dict(data, orient="index").T


df.to_csv("webtoons_data.csv", index=False)
df.to_excel("webtoons_data.xlsx", index=False)
