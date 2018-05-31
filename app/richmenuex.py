from richmenu import RichMenu, RichMenuManager

# Setup RichMenuManager
channel_access_token = 'MRxgDT2kynXriL1fXUHC7yY6FRx0A8sYBhTqsAl6wL0UYoMLt2d+T9QEwPq0ySiwBMnwMFb8Hkf23Z8lmsaqzEfkKH188hrlhIDCp6+hIFDQBTutt5sNhheL2+VVALeTHHHVnabxRQPdo3WPAJyZLwdB04t89/1O/w1cDnyilFU='
rmm = RichMenuManager(channel_access_token)

# Setup RichMenu to register
rm = RichMenu(name="Test menu", chat_bar_text="押してぽん!")
rm.add_area(0, 0, 1250, 843, "message", "新しいリマインダ")
rm.add_area(1250, 0, 1250, 843, "message", "一覧を見る")
rm.add_area(0, 843, 1250, 843, "message", "おはよう")
rm.add_area(1250, 843, 1250, 843, "message", "リマインダヌキ")

# Register
res = rmm.register(rm, "./image/menu2.png")
richmenu_id = res["richMenuId"]
print("Registered as " + richmenu_id)

# Apply to user
user_id = "LINE_MID_TO_APPLY"
rmm.apply(user_id, richmenu_id)

#check
res = rmm.get_applied_menu(user_id)
print(user_id  + ":" + richmenu_id)

